"""Unit tests for ClickHouseWriteRepository and AsyncClickHouseWriteRepository."""

from __future__ import annotations

from typing import Any

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.olap.clickhouse.exception import ClickHouseBulkInsertError, ClickHouseQueryError
from axiom.olap.clickhouse.repository.write.async_ import AsyncClickHouseWriteRepository
from axiom.olap.clickhouse.repository.write.sync_ import ClickHouseWriteRepository
from axiom.olap.clickhouse.result.models import BulkInsertResult, SingleInsertResult

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeSyncClient:
    """Test double for a synchronous clickhouse_connect client."""

    def __init__(self) -> None:
        self.inserted_tables: list[str] = []
        self.inserted_data: list[list[list[Any]]] = []
        self.inserted_columns: list[list[str]] = []
        self.commands: list[str] = []
        self.raise_on_insert: Exception | None = None
        self.raise_on_nth_insert: dict[int, Exception] = {}
        self._insert_call_count = 0

    def insert(
        self,
        table: str,
        data: list[list[Any]],
        column_names: list[str] | None = None,
        settings: dict | None = None,
    ) -> None:
        self._insert_call_count += 1
        if self.raise_on_insert:
            raise self.raise_on_insert
        exc = self.raise_on_nth_insert.get(self._insert_call_count)
        if exc:
            raise exc
        self.inserted_tables.append(table)
        self.inserted_data.append(data)
        self.inserted_columns.append(column_names or [])

    def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        self.commands.append(query)
        return None

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        class _Result:
            def named_results(self) -> list[dict[str, Any]]:
                return []

        return _Result()


class FakeAsyncClient:
    """Test double for an asynchronous clickhouse_connect client."""

    def __init__(self) -> None:
        self.inserted_tables: list[str] = []
        self.inserted_data: list[list[list[Any]]] = []
        self.inserted_columns: list[list[str]] = []
        self.commands: list[str] = []
        self.raise_on_insert: Exception | None = None
        self.raise_on_nth_insert: dict[int, Exception] = {}
        self._insert_call_count = 0

    async def insert(
        self,
        table: str,
        data: list[list[Any]],
        column_names: list[str] | None = None,
        settings: dict | None = None,
    ) -> None:
        self._insert_call_count += 1
        if self.raise_on_insert:
            raise self.raise_on_insert
        exc = self.raise_on_nth_insert.get(self._insert_call_count)
        if exc:
            raise exc
        self.inserted_tables.append(table)
        self.inserted_data.append(data)
        self.inserted_columns.append(column_names or [])

    async def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        self.commands.append(query)
        return None

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        class _Result:
            def named_results(self) -> list[dict[str, Any]]:
                return []

        return _Result()


def _make_sync_repo(
    client: FakeSyncClient | None = None,
) -> tuple[ClickHouseWriteRepository, FakeSyncClient]:
    c = client or FakeSyncClient()
    repo = ClickHouseWriteRepository(client=c, table="events")
    return repo, c


def _make_async_repo(
    client: FakeAsyncClient | None = None,
) -> tuple[AsyncClickHouseWriteRepository, FakeAsyncClient]:
    c = client or FakeAsyncClient()
    repo = AsyncClickHouseWriteRepository(client=c, table="events")
    return repo, c


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestClickHouseWriteRepository:
    def test_insert_single_row_success(self):
        repo, client = _make_sync_repo()
        result = repo.insert({"id": 1, "name": "alice"})
        assert isinstance(result, SingleInsertResult)
        assert result.success is True
        assert result.row == {"id": 1, "name": "alice"}
        assert client.inserted_tables == ["events"]

    def test_insert_single_row_raises_on_error(self):
        repo, client = _make_sync_repo()
        client.raise_on_insert = RuntimeError("insert failed")
        with pytest.raises(ClickHouseQueryError, match="insert failed"):
            repo.insert({"id": 1})

    def test_insert_many_empty_list(self):
        repo, client = _make_sync_repo()
        result = repo.insert_many([])
        assert result == BulkInsertResult(inserted=0, failed=0, errors=[])
        assert client.inserted_tables == []

    def test_insert_many_success(self):
        repo, client = _make_sync_repo()
        rows = [{"id": i, "val": i * 10} for i in range(5)]
        result = repo.insert_many(rows)
        assert result.inserted == 5
        assert result.failed == 0
        assert result.success is True
        assert len(client.inserted_tables) == 1

    def test_insert_many_uses_explicit_column_names(self):
        repo, client = _make_sync_repo()
        rows = [{"a": 1, "b": 2}]
        repo.insert_many(rows, column_names=["b", "a"])
        assert client.inserted_columns[0] == ["b", "a"]
        # data should be [[2, 1]]
        assert client.inserted_data[0] == [[2, 1]]

    def test_insert_many_returns_bulk_result_on_failure(self):
        repo, client = _make_sync_repo()
        client.raise_on_insert = RuntimeError("network error")
        result = repo.insert_many([{"id": 1}])
        assert result.inserted == 0
        assert result.failed == 1
        assert result.success is False
        assert "network error" in result.errors[0]

    def test_insert_chunked_empty(self):
        repo, client = _make_sync_repo()
        result = repo.insert_chunked([])
        assert result == BulkInsertResult(inserted=0, failed=0, errors=[])

    def test_insert_chunked_all_succeed(self):
        repo, client = _make_sync_repo()
        rows = [{"id": i} for i in range(10)]
        result = repo.insert_chunked(rows, chunk_size=3)
        assert result.inserted == 10
        assert result.failed == 0
        # 10 rows / 3 per chunk = 4 inserts
        assert len(client.inserted_tables) == 4

    def test_insert_chunked_one_chunk_fails(self):
        """Failed chunks raise ClickHouseBulkInsertError; successful chunks stay inserted."""
        client = FakeSyncClient()
        # Second chunk (insert call #2) raises
        client.raise_on_nth_insert[2] = RuntimeError("chunk 2 failed")
        repo, _ = _make_sync_repo(client)
        rows = [{"id": i} for i in range(6)]
        with pytest.raises(ClickHouseBulkInsertError):
            repo.insert_chunked(rows, chunk_size=3)
        # First chunk was inserted successfully
        assert len(client.inserted_tables) == 1

    def test_execute_command_returns_zero_on_none(self):
        repo, _ = _make_sync_repo()
        result = repo.execute_command("TRUNCATE TABLE events")
        assert result == 0

    def test_insert_dataframe_unsupported_raises(self):
        repo, _ = _make_sync_repo()
        with pytest.raises(ClickHouseQueryError):
            repo.insert_dataframe("not-a-dataframe")

    def test_insert_uses_column_order_from_first_row(self):
        repo, client = _make_sync_repo()
        rows = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        repo.insert_many(rows)
        assert client.inserted_columns[0] == ["x", "y"]


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAsyncClickHouseWriteRepository:
    async def test_insert_single_row_success(self):
        repo, client = _make_async_repo()
        result = await repo.insert({"id": 1, "name": "alice"})
        assert isinstance(result, SingleInsertResult)
        assert result.success is True
        assert result.row == {"id": 1, "name": "alice"}

    async def test_insert_single_row_raises_on_error(self):
        repo, client = _make_async_repo()
        client.raise_on_insert = RuntimeError("async insert failed")
        with pytest.raises(ClickHouseQueryError, match="async insert failed"):
            await repo.insert({"id": 1})

    async def test_insert_many_empty(self):
        repo, client = _make_async_repo()
        result = await repo.insert_many([])
        assert result == BulkInsertResult(inserted=0, failed=0, errors=[])

    async def test_insert_many_success(self):
        repo, client = _make_async_repo()
        rows = [{"id": i} for i in range(3)]
        result = await repo.insert_many(rows)
        assert result.inserted == 3
        assert result.failed == 0

    async def test_insert_many_failure(self):
        repo, client = _make_async_repo()
        client.raise_on_insert = RuntimeError("async error")
        result = await repo.insert_many([{"id": 1}])
        assert result.failed == 1
        assert result.success is False

    async def test_insert_chunked_empty(self):
        repo, client = _make_async_repo()
        result = await repo.insert_chunked([])
        assert result == BulkInsertResult(inserted=0, failed=0, errors=[])

    async def test_insert_chunked_all_succeed(self):
        repo, client = _make_async_repo()
        rows = [{"id": i} for i in range(9)]
        result = await repo.insert_chunked(rows, chunk_size=3)
        assert result.inserted == 9
        assert len(client.inserted_tables) == 3

    async def test_insert_chunked_one_chunk_fails(self):
        client = FakeAsyncClient()
        client.raise_on_nth_insert[2] = RuntimeError("chunk 2 failed")
        repo, _ = _make_async_repo(client)
        rows = [{"id": i} for i in range(6)]
        with pytest.raises(ClickHouseBulkInsertError):
            await repo.insert_chunked(rows, chunk_size=3)
        assert len(client.inserted_tables) == 1

    async def test_execute_command_returns_zero(self):
        repo, _ = _make_async_repo()
        result = await repo.execute_command("TRUNCATE TABLE events")
        assert result == 0

    async def test_insert_many_uses_explicit_column_names(self):
        repo, client = _make_async_repo()
        rows = [{"a": 1, "b": 2}]
        await repo.insert_many(rows, column_names=["b", "a"])
        assert client.inserted_columns[0] == ["b", "a"]
        assert client.inserted_data[0] == [[2, 1]]


# ---------------------------------------------------------------------------
# CRUD-like operations (US-010)
# ---------------------------------------------------------------------------


def _make_filter(field: str = "status", value: str = "active") -> FilterRequest:
    return FilterRequest(chain=FilterParam(field=field, operator=QueryOperator.EQUALS, value=value))


class TestCrudLikeSync:
    def test_update_by_filter_issues_alter_command(self):
        repo, client = _make_sync_repo()
        result = repo.update_by_filter(_make_filter(), {"status": "inactive"})
        assert result == 0
        assert len(client.commands) == 1
        assert "ALTER TABLE" in client.commands[0]
        assert "UPDATE" in client.commands[0]

    def test_update_by_filter_includes_set_and_where(self):
        repo, client = _make_sync_repo()
        repo.update_by_filter(_make_filter("id", "42"), {"name": "bob"})
        cmd = client.commands[0]
        assert "UPDATE" in cmd
        assert "WHERE" in cmd

    def test_delete_by_filter_issues_alter_command(self):
        repo, client = _make_sync_repo()
        result = repo.delete_by_filter(_make_filter())
        assert result == 0
        assert len(client.commands) == 1
        assert "ALTER TABLE" in client.commands[0]
        assert "DELETE" in client.commands[0]

    def test_delete_by_filter_includes_where(self):
        repo, client = _make_sync_repo()
        repo.delete_by_filter(_make_filter("id", "7"))
        cmd = client.commands[0]
        assert "DELETE" in cmd
        assert "WHERE" in cmd

    def test_upsert_delegates_to_insert_many(self):
        repo, client = _make_sync_repo()
        rows = [{"id": 1, "val": "x"}, {"id": 2, "val": "y"}]
        result = repo.upsert(rows)
        assert result.inserted == 2
        assert result.failed == 0
        assert result.success is True
        assert len(client.inserted_tables) == 1

    def test_upsert_empty_list(self):
        repo, client = _make_sync_repo()
        result = repo.upsert([])
        assert result == BulkInsertResult(inserted=0, failed=0, errors=[])


class TestCrudLikeAsync:
    async def test_update_by_filter_issues_alter_command(self):
        repo, client = _make_async_repo()
        result = await repo.update_by_filter(_make_filter(), {"status": "done"})
        assert result == 0
        assert len(client.commands) == 1
        assert "ALTER TABLE" in client.commands[0]
        assert "UPDATE" in client.commands[0]

    async def test_delete_by_filter_issues_alter_command(self):
        repo, client = _make_async_repo()
        result = await repo.delete_by_filter(_make_filter())
        assert result == 0
        assert len(client.commands) == 1
        assert "ALTER TABLE" in client.commands[0]
        assert "DELETE" in client.commands[0]

    async def test_upsert_delegates_to_insert_many(self):
        repo, client = _make_async_repo()
        rows = [{"id": 1, "v": "a"}]
        result = await repo.upsert(rows)
        assert result.inserted == 1
        assert result.success is True

    async def test_upsert_empty_list(self):
        repo, client = _make_async_repo()
        result = await repo.upsert([])
        assert result == BulkInsertResult(inserted=0, failed=0, errors=[])
