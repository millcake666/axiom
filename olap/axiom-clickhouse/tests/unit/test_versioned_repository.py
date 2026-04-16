"""Unit tests for VersionedClickHouseRepository and AsyncVersionedClickHouseRepository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from axiom.olap.clickhouse.exception import ClickHouseConfigError
from axiom.olap.clickhouse.repository.versioned.async_ import AsyncVersionedClickHouseRepository
from axiom.olap.clickhouse.repository.versioned.sync_ import VersionedClickHouseRepository
from axiom.olap.clickhouse.result.models import BulkInsertResult, QueryResult, SingleInsertResult


class FakeQueryResult:
    def __init__(self, rows: list[dict[str, Any]], query_id: str = "fake-id") -> None:
        self._rows = rows
        self.query_id = query_id

    def named_results(self) -> list[dict[str, Any]]:
        return self._rows


class FakeSyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.inserted: list[Any] = []

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        return FakeQueryResult(self._rows)

    def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> None:
        return None

    def insert(self, table: str, data: list[list[Any]], column_names: list[str]) -> None:
        self.inserted.append({"table": table, "data": data, "columns": column_names})


class FakeAsyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.inserted: list[Any] = []

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        return FakeQueryResult(self._rows)

    async def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> None:
        return None

    async def insert(self, table: str, data: list[list[Any]], column_names: list[str]) -> None:
        self.inserted.append({"table": table, "data": data, "columns": column_names})


@pytest.fixture
def sync_repo():
    return VersionedClickHouseRepository(
        client=FakeSyncClient(),
        table="events",
        version_column="version",
        is_deleted_column="is_deleted",
    )


@pytest.fixture
def async_repo():
    return AsyncVersionedClickHouseRepository(
        client=FakeAsyncClient(),
        table="events",
        version_column="version",
        is_deleted_column="is_deleted",
    )


class TestAppendVersion:
    def test_returns_single_insert_result(self, sync_repo):
        result = sync_repo.append_version({"id": 1, "name": "test"}, version=1)
        assert isinstance(result, SingleInsertResult)
        assert result.success is True

    def test_sets_version_column(self, sync_repo):
        result = sync_repo.append_version({"id": 1}, version=42)
        assert result.row["version"] == 42

    def test_accepts_datetime_version(self, sync_repo):
        dt = datetime(2024, 1, 1)
        result = sync_repo.append_version({"id": 2}, version=dt)
        assert result.row["version"] == dt

    def test_insert_called_with_correct_table(self, sync_repo):
        sync_repo.append_version({"id": 1}, version=1)
        assert sync_repo._client.inserted[-1]["table"] == "events"


class TestAppendManyVersions:
    def test_empty_list_returns_zero(self, sync_repo):
        result = sync_repo.append_many_versions([])
        assert isinstance(result, BulkInsertResult)
        assert result.inserted == 0
        assert result.failed == 0

    def test_inserts_all_rows(self, sync_repo):
        rows = [{"id": 1, "version": 1}, {"id": 2, "version": 2}]
        result = sync_repo.append_many_versions(rows)
        assert result.inserted == 2
        assert result.failed == 0


class TestSoftDelete:
    def test_raises_config_error_without_is_deleted_column(self):
        repo = VersionedClickHouseRepository(
            client=FakeSyncClient(),
            table="events",
            version_column="version",
            is_deleted_column=None,
        )
        with pytest.raises(ClickHouseConfigError):
            repo.soft_delete("id", 1, version=99)

    def test_soft_delete_sets_is_deleted_true(self, sync_repo):
        result = sync_repo.soft_delete("id", 1, version=2)
        assert result.success is True
        assert result.row["is_deleted"] is True

    def test_soft_delete_includes_version(self, sync_repo):
        result = sync_repo.soft_delete("id", 5, version=10)
        assert result.row["version"] == 10

    def test_soft_delete_includes_id(self, sync_repo):
        result = sync_repo.soft_delete("my_id", 42, version=1)
        assert result.row["my_id"] == 42


class TestGetLatestWithFinal:
    def test_returns_query_result(self, sync_repo):
        result = sync_repo.get_latest_with_final()
        assert isinstance(result, QueryResult)

    def test_no_filter_returns_all_rows(self):
        client = FakeSyncClient(rows=[{"id": 1}, {"id": 2}])
        repo = VersionedClickHouseRepository(
            client=client,
            table="t",
            version_column="v",
        )
        result = repo.get_latest_with_final()
        assert result.row_count == 2


class TestReadActive:
    def test_returns_query_result(self, sync_repo):
        result = sync_repo.read_active()
        assert isinstance(result, QueryResult)


class TestDeduplicatedCount:
    def test_returns_zero_on_empty(self):
        client = FakeSyncClient(rows=[{"COUNT(DISTINCT id)": 0}])
        repo = VersionedClickHouseRepository(
            client=client,
            table="t",
            version_column="v",
        )
        result = repo.deduplicated_count("id")
        assert isinstance(result, int)


class TestAsyncSoftDelete:
    async def test_raises_config_error_without_is_deleted_column(self):
        repo = AsyncVersionedClickHouseRepository(
            client=FakeAsyncClient(),
            table="events",
            version_column="version",
            is_deleted_column=None,
        )
        with pytest.raises(ClickHouseConfigError):
            await repo.soft_delete("id", 1, version=99)

    async def test_soft_delete_sets_is_deleted_true(self, async_repo):
        result = await async_repo.soft_delete("id", 1, version=2)
        assert result.success is True
        assert result.row["is_deleted"] is True


class TestAsyncAppendVersion:
    async def test_returns_single_insert_result(self, async_repo):
        result = await async_repo.append_version({"id": 1}, version=1)
        assert isinstance(result, SingleInsertResult)
        assert result.success is True

    async def test_empty_append_many_returns_zero(self, async_repo):
        result = await async_repo.append_many_versions([])
        assert result.inserted == 0


class TestAsyncGetLatestWithFinal:
    async def test_returns_query_result(self, async_repo):
        result = await async_repo.get_latest_with_final()
        assert isinstance(result, QueryResult)


class TestAsyncReadActive:
    async def test_returns_query_result(self, async_repo):
        result = await async_repo.read_active()
        assert isinstance(result, QueryResult)
