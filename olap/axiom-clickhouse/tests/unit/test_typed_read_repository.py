"""Unit tests for TypedClickHouseReadRepository and AsyncTypedClickHouseReadRepository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.olap.clickhouse.exception import ClickHouseRowMappingError
from axiom.olap.clickhouse.query.specs import CHQuerySpec, PageSpec
from axiom.olap.clickhouse.repository.read.async_typed import AsyncTypedClickHouseReadRepository
from axiom.olap.clickhouse.repository.read.typed import TypedClickHouseReadRepository
from axiom.olap.clickhouse.result.models import PagedResult, QueryResult

# ---------------------------------------------------------------------------
# Fake clients (test doubles)
# ---------------------------------------------------------------------------


class FakeQueryResult:
    def __init__(self, rows: list[dict[str, Any]], query_id: str = "test-qid") -> None:
        self._rows = rows
        self.query_id = query_id

    def named_results(self) -> list[dict[str, Any]]:
        return self._rows


class FakeRowBlockStream:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.source = type("S", (), {"column_names": list(rows[0].keys()) if rows else []})()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __iter__(self):
        for row in self._rows:
            yield [[v for v in row.values()]]


class FakeSyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        return FakeQueryResult(self._rows)

    def query_row_block_stream(self, query: str, parameters: dict | None = None):
        return FakeRowBlockStream(self._rows)


class FakeAsyncQueryResult:
    def __init__(self, rows: list[dict[str, Any]], query_id: str = "async-qid") -> None:
        self._rows = rows
        self.query_id = query_id

    def named_results(self) -> list[dict[str, Any]]:
        return self._rows


class FakeAsyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeAsyncQueryResult:
        return FakeAsyncQueryResult(self._rows)


# ---------------------------------------------------------------------------
# Domain objects for row_factory compatibility tests
# ---------------------------------------------------------------------------


@dataclass
class UserRow:
    id: int
    name: str


class UserModel:
    """Pydantic-like model (plain class for test isolation)."""

    def __init__(self, **data: Any) -> None:
        self.id = data["id"]
        self.name = data["name"]


SAMPLE_ROWS = [
    {"id": 1, "name": "alice"},
    {"id": 2, "name": "bob"},
    {"id": 3, "name": "carol"},
]

# ---------------------------------------------------------------------------
# Sync typed repository tests
# ---------------------------------------------------------------------------


def _make_sync_typed(rows: list[dict] | None = None, factory=None):
    client = FakeSyncClient(SAMPLE_ROWS if rows is None else rows)
    if factory is None:

        def factory(d):
            return UserRow(id=d["id"], name=d["name"])

    repo = TypedClickHouseReadRepository(client=client, table="users", row_factory=factory)
    return repo


class TestTypedSyncFetchAll:
    def test_returns_typed_query_result(self):
        repo = _make_sync_typed()
        result = repo.fetch_all()
        assert isinstance(result, QueryResult)
        assert result.row_count == 3
        assert all(isinstance(r, UserRow) for r in result.rows)

    def test_row_factory_called_correct_times(self):
        calls = []

        def counting_factory(d):
            calls.append(d)
            return UserRow(id=d["id"], name=d["name"])

        repo = _make_sync_typed(factory=counting_factory)
        repo.fetch_all()
        assert len(calls) == 3

    def test_row_factory_mapping_error_wrapped(self):
        def bad_factory(d):
            raise ValueError("bad field")

        repo = _make_sync_typed(factory=bad_factory)
        with pytest.raises(ClickHouseRowMappingError) as exc_info:
            repo.fetch_all()
        assert exc_info.value.row_index == 0

    def test_row_index_increments_on_error(self):
        call_count = 0

        def fail_on_second(d):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise KeyError("missing_field")
            return UserRow(id=d["id"], name=d["name"])

        repo = _make_sync_typed()
        repo._client._rows = SAMPLE_ROWS
        # Replace factory at instance level
        repo._row_factory = fail_on_second
        with pytest.raises(ClickHouseRowMappingError) as exc_info:
            repo.fetch_all()
        assert exc_info.value.row_index == 1


class TestTypedSyncFetchOne:
    def test_returns_typed_row(self):
        repo = _make_sync_typed([{"id": 1, "name": "alice"}])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        row = repo.fetch_one(fr)
        assert isinstance(row, UserRow)
        assert row.id == 1

    def test_returns_none_on_empty(self):
        repo = _make_sync_typed([])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=99))
        assert repo.fetch_one(fr) is None

    def test_row_factory_mapping_error_wrapped(self):
        def bad_factory(d):
            raise RuntimeError("boom")

        repo = _make_sync_typed([{"id": 1, "name": "x"}], factory=bad_factory)
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        with pytest.raises(ClickHouseRowMappingError):
            repo.fetch_one(fr)


class TestTypedSyncFetchPaged:
    def test_returns_typed_paged_result(self):
        client = FakeSyncClient([{"count()": 10}])
        repo = TypedClickHouseReadRepository(
            client=client,
            table="users",
            row_factory=lambda d: UserRow(id=d.get("id", 0), name=d.get("name", "")),
        )
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=5))
        result = repo.fetch_paged(spec)
        assert isinstance(result, PagedResult)
        assert result.total == 10

    def test_row_factory_called_for_paged_rows(self):
        calls = []
        rows = [{"id": i, "name": f"u{i}", "count()": 10} for i in range(3)]
        client = FakeSyncClient(rows)

        def counting_factory(d):
            calls.append(d)
            return UserRow(id=d.get("id", 0), name=d.get("name", ""))

        repo = TypedClickHouseReadRepository(
            client=client,
            table="users",
            row_factory=counting_factory,
        )
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=3))
        repo.fetch_paged(spec)
        # factory is called for the SELECT rows (not the COUNT row)
        assert len(calls) > 0


class TestTypedSyncFetchById:
    def test_returns_typed_row(self):
        repo = _make_sync_typed([{"id": 42, "name": "dave"}])
        row = repo.fetch_by_id("id", 42)
        assert isinstance(row, UserRow)
        assert row.id == 42

    def test_returns_none_when_not_found(self):
        repo = _make_sync_typed([])
        assert repo.fetch_by_id("id", 999) is None

    def test_get_by_id_alias(self):
        repo = _make_sync_typed([{"id": 5, "name": "eve"}])
        row = repo.get_by_id("id", 5)
        assert isinstance(row, UserRow)


class TestTypedSyncExecuteSelect:
    def test_returns_typed_query_result(self):
        repo = _make_sync_typed([{"id": 7, "name": "frank"}])
        result = repo.execute_select("SELECT id, name FROM users")
        assert isinstance(result, QueryResult)
        assert isinstance(result.rows[0], UserRow)

    def test_row_factory_called_for_each_row(self):
        calls = []

        def factory(d):
            calls.append(d)
            return UserRow(id=d["id"], name=d["name"])

        repo = _make_sync_typed(factory=factory)
        repo.execute_select("SELECT * FROM users")
        assert len(calls) == 3


class TestTypedSyncCompatibility:
    def test_with_dataclass_factory(self):
        repo = _make_sync_typed(factory=lambda d: UserRow(**d))
        result = repo.fetch_all()
        assert all(isinstance(r, UserRow) for r in result.rows)

    def test_with_plain_class_factory(self):
        repo = _make_sync_typed(factory=lambda d: UserModel(**d))
        result = repo.fetch_all()
        assert all(isinstance(r, UserModel) for r in result.rows)
        assert result.rows[0].name == "alice"

    def test_with_dict_passthrough(self):
        repo = _make_sync_typed(factory=lambda d: d)
        result = repo.fetch_all()
        assert result.rows[0] == {"id": 1, "name": "alice"}


class TestTypedSyncStream:
    def test_yields_typed_blocks(self):
        repo = _make_sync_typed()
        blocks = list(repo.stream("SELECT * FROM users"))
        all_rows = [r for block in blocks for r in block]
        assert all(isinstance(r, UserRow) for r in all_rows)

    def test_row_factory_applied_to_each_block(self):
        calls = []

        def factory(d):
            calls.append(d)
            return UserRow(id=d["id"], name=d["name"])

        repo = _make_sync_typed(factory=factory)
        list(repo.stream("SELECT * FROM users"))
        assert len(calls) == 3


# ---------------------------------------------------------------------------
# Async typed repository tests
# ---------------------------------------------------------------------------


def _make_async_typed(rows: list[dict] | None = None, factory=None):
    client = FakeAsyncClient(SAMPLE_ROWS if rows is None else rows)
    if factory is None:

        def factory(d):
            return UserRow(id=d["id"], name=d["name"])

    return AsyncTypedClickHouseReadRepository(client=client, table="users", row_factory=factory)


class TestTypedAsyncFetchAll:
    async def test_returns_typed_query_result(self):
        repo = _make_async_typed()
        result = await repo.fetch_all()
        assert isinstance(result, QueryResult)
        assert result.row_count == 3
        assert all(isinstance(r, UserRow) for r in result.rows)

    async def test_row_factory_called_correct_times(self):
        calls = []

        def factory(d):
            calls.append(d)
            return UserRow(id=d["id"], name=d["name"])

        repo = _make_async_typed(factory=factory)
        await repo.fetch_all()
        assert len(calls) == 3

    async def test_row_factory_mapping_error_wrapped(self):
        def bad_factory(d):
            raise ValueError("bad")

        repo = _make_async_typed(factory=bad_factory)
        with pytest.raises(ClickHouseRowMappingError) as exc_info:
            await repo.fetch_all()
        assert exc_info.value.row_index == 0


class TestTypedAsyncFetchOne:
    async def test_returns_typed_row(self):
        repo = _make_async_typed([{"id": 1, "name": "alice"}])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        row = await repo.fetch_one(fr)
        assert isinstance(row, UserRow)

    async def test_returns_none_on_empty(self):
        repo = _make_async_typed([])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=99))
        assert await repo.fetch_one(fr) is None

    async def test_mapping_error_on_bad_factory(self):
        repo = _make_async_typed(
            [{"id": 1, "name": "x"}],
            factory=lambda d: (_ for _ in ()).throw(KeyError("id")),
        )
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        with pytest.raises((ClickHouseRowMappingError, Exception)):
            await repo.fetch_one(fr)


class TestTypedAsyncFetchById:
    async def test_returns_typed_row(self):
        repo = _make_async_typed([{"id": 42, "name": "dave"}])
        row = await repo.fetch_by_id("id", 42)
        assert isinstance(row, UserRow)
        assert row.id == 42

    async def test_returns_none_when_not_found(self):
        repo = _make_async_typed([])
        assert await repo.fetch_by_id("id", 999) is None

    async def test_get_by_id_alias(self):
        repo = _make_async_typed([{"id": 5, "name": "eve"}])
        row = await repo.get_by_id("id", 5)
        assert isinstance(row, UserRow)


class TestTypedAsyncExecuteSelect:
    async def test_returns_typed_query_result(self):
        repo = _make_async_typed([{"id": 7, "name": "frank"}])
        result = await repo.execute_select("SELECT id, name FROM users")
        assert isinstance(result, QueryResult)
        assert isinstance(result.rows[0], UserRow)

    async def test_row_factory_called_for_each_row(self):
        calls = []

        def factory(d):
            calls.append(d)
            return UserRow(id=d["id"], name=d["name"])

        repo = _make_async_typed(factory=factory)
        await repo.execute_select("SELECT * FROM users")
        assert len(calls) == 3


class TestTypedAsyncCompatibility:
    async def test_with_dataclass_factory(self):
        repo = _make_async_typed(factory=lambda d: UserRow(**d))
        result = await repo.fetch_all()
        assert all(isinstance(r, UserRow) for r in result.rows)

    async def test_with_plain_class_factory(self):
        repo = _make_async_typed(factory=lambda d: UserModel(**d))
        result = await repo.fetch_all()
        assert all(isinstance(r, UserModel) for r in result.rows)

    async def test_with_dict_passthrough(self):
        repo = _make_async_typed(factory=lambda d: d)
        result = await repo.fetch_all()
        assert result.rows[0] == {"id": 1, "name": "alice"}
