"""Unit tests for ClickHouseReadRepository and AsyncClickHouseReadRepository."""

from __future__ import annotations

from typing import Any

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.query.specs import CHQuerySpec, PageSpec
from axiom.olap.clickhouse.repository.read.async_ import AsyncClickHouseReadRepository
from axiom.olap.clickhouse.repository.read.sync_ import ClickHouseReadRepository
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


class FakeStreamBlock:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.column_names = list(rows[0].keys()) if rows else []

    def __iter__(self):
        for row in self._rows:
            yield tuple(row.values())


class FakeRowBlockStream:
    def __init__(self, blocks: list[list[dict[str, Any]]]) -> None:
        self._blocks = blocks
        self.source = FakeStreamBlock(blocks[0] if blocks else [])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __iter__(self):
        for block in self._blocks:
            yield [[v for v in row.values()] for row in block]


class FakeSyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.raise_on_query: Exception | None = None

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        if self.raise_on_query:
            raise self.raise_on_query
        return FakeQueryResult(self._rows)

    def query_row_block_stream(self, query: str, parameters: dict | None = None):
        return FakeRowBlockStream([self._rows] if self._rows else [[]])


class FakeAsyncQueryResult:
    def __init__(self, rows: list[dict[str, Any]], query_id: str = "async-qid") -> None:
        self._rows = rows
        self.query_id = query_id

    def named_results(self) -> list[dict[str, Any]]:
        return self._rows


class FakeAsyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.raise_on_query: Exception | None = None

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeAsyncQueryResult:
        if self.raise_on_query:
            raise self.raise_on_query
        return FakeAsyncQueryResult(self._rows)


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------

SAMPLE_ROWS = [
    {"id": 1, "name": "alice", "status": "active"},
    {"id": 2, "name": "bob", "status": "inactive"},
    {"id": 3, "name": "carol", "status": "active"},
]


def _make_sync_repo(
    rows: list[dict] | None = None,
) -> tuple[ClickHouseReadRepository, FakeSyncClient]:
    client = FakeSyncClient(SAMPLE_ROWS if rows is None else rows)
    repo = ClickHouseReadRepository(client=client, table="events")
    return repo, client


class TestSyncFetchAll:
    def test_returns_query_result(self):
        repo, _ = _make_sync_repo()
        result = repo.fetch_all()
        assert isinstance(result, QueryResult)
        assert result.row_count == 3

    def test_with_spec_none(self):
        repo, _ = _make_sync_repo([{"id": 1}])
        result = repo.fetch_all(None)
        assert result.row_count == 1

    def test_wraps_exception(self):
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("boom")
        with pytest.raises(ClickHouseQueryError):
            repo.fetch_all()


class TestSyncFetchOne:
    def test_returns_first_row(self):
        repo, _ = _make_sync_repo([{"id": 1, "name": "alice"}])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        row = repo.fetch_one(fr)
        assert row == {"id": 1, "name": "alice"}

    def test_returns_none_on_empty(self):
        repo, _ = _make_sync_repo([])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=99))
        assert repo.fetch_one(fr) is None

    def test_wraps_exception(self):
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("fail")
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        with pytest.raises(ClickHouseQueryError):
            repo.fetch_one(fr)


class TestSyncCount:
    def test_count_all(self):
        # _fetch_scalar returns first col of first row; fake returns full rows
        # count calls _fetch_scalar which calls query -> named_results()[0] first value
        repo, _ = _make_sync_repo([{"count()": 3}])
        assert repo.count() == 3

    def test_count_zero_on_empty(self):
        repo, _ = _make_sync_repo([])
        assert repo.count() == 0


class TestSyncExists:
    def test_exists_true(self):
        repo, _ = _make_sync_repo([{"count()": 5}])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        assert repo.exists(fr) is True

    def test_exists_false(self):
        repo, _ = _make_sync_repo([])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=99))
        assert repo.exists(fr) is False


class TestSyncFetchPaged:
    def test_returns_paged_result(self):
        repo, _ = _make_sync_repo([{"count()": 10}])
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=2))
        # count returns 10, fetch_all returns the fake rows but with count row
        result = repo.fetch_paged(spec)
        assert isinstance(result, PagedResult)

    def test_paged_has_next(self):
        # Setup: count returns 10, fetch_all returns 2 rows
        client = FakeSyncClient([{"count()": 10}])
        repo = ClickHouseReadRepository(client=client, table="events")
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=2))
        result = repo.fetch_paged(spec)
        # total is "10" extracted from {"count()": 10} -> int(10) = 10
        assert result.total == 10
        assert result.has_next is True


class TestSyncFetchById:
    def test_found(self):
        repo, _ = _make_sync_repo([{"id": 1}])
        row = repo.fetch_by_id("id", 1)
        assert row == {"id": 1}

    def test_not_found(self):
        repo, _ = _make_sync_repo([])
        row = repo.fetch_by_id("id", 999)
        assert row is None

    def test_wraps_exception(self):
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("err")
        with pytest.raises(ClickHouseQueryError):
            repo.fetch_by_id("id", 1)


class TestSyncStream:
    def test_yields_blocks(self):
        repo, _ = _make_sync_repo(SAMPLE_ROWS)
        blocks = list(repo.stream("SELECT * FROM events"))
        # At least one block returned
        assert len(blocks) >= 1
        all_rows = [row for block in blocks for row in block]
        assert len(all_rows) == 3

    def test_wraps_exception(self):
        client = FakeSyncClient(SAMPLE_ROWS)

        class BrokenStream:
            def __enter__(self):
                raise RuntimeError("stream broken")

            def __exit__(self, *a):
                pass

        client.query_row_block_stream = lambda *a, **kw: BrokenStream()
        repo = ClickHouseReadRepository(client=client, table="events")
        with pytest.raises(ClickHouseQueryError):
            list(repo.stream("SELECT * FROM events"))


class TestSyncExecuteSelect:
    def test_returns_query_result(self):
        repo, _ = _make_sync_repo([{"x": 1}])
        result = repo.execute_select("SELECT x FROM t")
        assert isinstance(result, QueryResult)
        assert result.rows == [{"x": 1}]

    def test_wraps_exception(self):
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("oops")
        with pytest.raises(ClickHouseQueryError):
            repo.execute_select("SELECT 1")


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


def _make_async_repo(
    rows: list[dict] | None = None,
) -> tuple[AsyncClickHouseReadRepository, FakeAsyncClient]:
    client = FakeAsyncClient(SAMPLE_ROWS if rows is None else rows)
    repo = AsyncClickHouseReadRepository(client=client, table="events")
    return repo, client


class TestAsyncFetchAll:
    async def test_returns_query_result(self):
        repo, _ = _make_async_repo()
        result = await repo.fetch_all()
        assert isinstance(result, QueryResult)
        assert result.row_count == 3

    async def test_wraps_exception(self):
        repo, client = _make_async_repo()
        client.raise_on_query = RuntimeError("async boom")
        with pytest.raises(ClickHouseQueryError):
            await repo.fetch_all()


class TestAsyncFetchOne:
    async def test_returns_first_row(self):
        repo, _ = _make_async_repo([{"id": 5}])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=5))
        row = await repo.fetch_one(fr)
        assert row == {"id": 5}

    async def test_returns_none_on_empty(self):
        repo, _ = _make_async_repo([])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        assert await repo.fetch_one(fr) is None


class TestAsyncCount:
    async def test_count(self):
        repo, _ = _make_async_repo([{"c": 7}])
        assert await repo.count() == 7

    async def test_count_zero(self):
        repo, _ = _make_async_repo([])
        assert await repo.count() == 0


class TestAsyncExists:
    async def test_exists_true(self):
        repo, _ = _make_async_repo([{"c": 1}])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        assert await repo.exists(fr) is True

    async def test_exists_false(self):
        repo, _ = _make_async_repo([])
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        assert await repo.exists(fr) is False


class TestAsyncFetchById:
    async def test_found(self):
        repo, _ = _make_async_repo([{"id": 42}])
        row = await repo.fetch_by_id("id", 42)
        assert row == {"id": 42}

    async def test_not_found(self):
        repo, _ = _make_async_repo([])
        row = await repo.fetch_by_id("id", 999)
        assert row is None


class TestAsyncStream:
    async def test_yields_chunks(self):
        rows = [{"id": i} for i in range(5)]
        repo, _ = _make_async_repo(rows)
        chunks = []
        async for chunk in repo.stream("SELECT * FROM events", chunk_size=2):
            chunks.append(chunk)
        assert sum(len(c) for c in chunks) == 5

    async def test_empty_stream(self):
        repo, _ = _make_async_repo([])
        chunks = []
        async for chunk in repo.stream("SELECT * FROM events"):
            chunks.append(chunk)
        assert chunks == []

    async def test_wraps_exception(self):
        repo, client = _make_async_repo()
        client.raise_on_query = RuntimeError("stream err")
        with pytest.raises(ClickHouseQueryError):
            async for _ in repo.stream("SELECT 1"):
                pass


class TestAsyncExecuteSelect:
    async def test_returns_query_result(self):
        repo, _ = _make_async_repo([{"val": 99}])
        result = await repo.execute_select("SELECT val FROM t")
        assert result.rows == [{"val": 99}]

    async def test_wraps_exception(self):
        repo, client = _make_async_repo()
        client.raise_on_query = RuntimeError("fail")
        with pytest.raises(ClickHouseQueryError):
            await repo.execute_select("SELECT 1")
