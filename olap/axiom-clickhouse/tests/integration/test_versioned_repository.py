# ruff: noqa: S608
"""Integration tests for VersionedClickHouseRepository and AsyncVersionedClickHouseRepository."""

from __future__ import annotations

import pytest

from axiom.olap.clickhouse.exception import ClickHouseConfigError
from axiom.olap.clickhouse.repository.versioned.async_ import AsyncVersionedClickHouseRepository
from axiom.olap.clickhouse.repository.versioned.sync_ import VersionedClickHouseRepository

TEST_TABLE = "test_versioned_events"

CREATE_DDL = f"""
CREATE TABLE IF NOT EXISTS {TEST_TABLE} (
    id UInt64,
    name String,
    version UInt64,
    is_deleted UInt8 DEFAULT 0
) ENGINE = ReplacingMergeTree(version)
ORDER BY id
"""


@pytest.fixture(scope="module")
def versioned_repo(ch_client):
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")
    ch_client.command(CREATE_DDL)
    yield VersionedClickHouseRepository(
        client=ch_client,
        table=TEST_TABLE,
        version_column="version",
        is_deleted_column="is_deleted",
    )
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")


@pytest.fixture(scope="module")
async def async_versioned_repo(async_ch_client):
    await async_ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}_async")
    await async_ch_client.command(
        f"""
        CREATE TABLE IF NOT EXISTS {TEST_TABLE}_async (
            id UInt64,
            name String,
            version UInt64,
            is_deleted UInt8 DEFAULT 0
        ) ENGINE = ReplacingMergeTree(version)
        ORDER BY id
        """,
    )
    yield AsyncVersionedClickHouseRepository(
        client=async_ch_client,
        table=f"{TEST_TABLE}_async",
        version_column="version",
        is_deleted_column="is_deleted",
    )
    await async_ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}_async")


@pytest.fixture(autouse=True)
def truncate_table(ch_client):
    yield
    ch_client.command(f"TRUNCATE TABLE IF EXISTS {TEST_TABLE}")
    ch_client.command(f"TRUNCATE TABLE IF EXISTS {TEST_TABLE}_async")


class TestAppendVersion:
    def test_append_version_returns_success(self, versioned_repo):
        result = versioned_repo.append_version({"id": 1, "name": "alice"}, version=1)
        assert result.success is True

    def test_append_version_sets_version_column(self, versioned_repo):
        result = versioned_repo.append_version({"id": 2, "name": "bob"}, version=42)
        assert result.row["version"] == 42

    def test_append_many_versions_empty(self, versioned_repo):
        result = versioned_repo.append_many_versions([])
        assert result.inserted == 0
        assert result.failed == 0

    def test_append_many_versions(self, versioned_repo):
        rows = [
            {"id": 10, "name": "x", "version": 1},
            {"id": 11, "name": "y", "version": 1},
        ]
        result = versioned_repo.append_many_versions(rows)
        assert result.inserted == 2
        assert result.failed == 0


class TestGetLatest:
    def test_get_latest_returns_latest_version(self, versioned_repo, ch_client):
        versioned_repo.append_version({"id": 100, "name": "v1"}, version=1)
        versioned_repo.append_version({"id": 100, "name": "v2"}, version=2)

        from axiom.core.filter import FilterParam, FilterRequest, QueryOperator

        filters = FilterRequest(
            chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=100),
        )
        row = versioned_repo.get_latest(filters, id_column="id")
        assert row is not None
        assert row["version"] == 2
        assert row["name"] == "v2"

    def test_get_latest_returns_none_for_missing(self, versioned_repo):
        from axiom.core.filter import FilterParam, FilterRequest, QueryOperator

        filters = FilterRequest(
            chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=9999),
        )
        row = versioned_repo.get_latest(filters, id_column="id")
        assert row is None


class TestGetLatestWithFinal:
    def test_get_latest_with_final_after_optimize(self, versioned_repo, ch_client):
        versioned_repo.append_version({"id": 200, "name": "v1"}, version=1)
        versioned_repo.append_version({"id": 200, "name": "v2"}, version=2)
        ch_client.command(f"OPTIMIZE TABLE {TEST_TABLE} FINAL")

        result = versioned_repo.get_latest_with_final()
        ids = [r["id"] for r in result.rows]
        # After OPTIMIZE FINAL, only one row per id should remain
        assert ids.count(200) == 1

    def test_get_latest_with_final_returns_query_result(self, versioned_repo):
        from axiom.olap.clickhouse.result.models import QueryResult

        result = versioned_repo.get_latest_with_final()
        assert isinstance(result, QueryResult)


class TestSoftDelete:
    def test_soft_delete_raises_config_error_without_is_deleted_column(self, ch_client):
        repo_no_delete = VersionedClickHouseRepository(
            client=ch_client,
            table=TEST_TABLE,
            version_column="version",
            is_deleted_column=None,
        )
        with pytest.raises(ClickHouseConfigError):
            repo_no_delete.soft_delete("id", 1, version=99)

    def test_soft_delete_inserts_deletion_row(self, versioned_repo, ch_client):
        versioned_repo.append_version({"id": 300, "name": "to_delete"}, version=1)
        result = versioned_repo.soft_delete("id", 300, version=2)
        assert result.success is True
        assert result.row["is_deleted"] is True


class TestReadActive:
    def test_read_active_excludes_soft_deleted(self, versioned_repo, ch_client):
        versioned_repo.append_version({"id": 400, "name": "active"}, version=1)
        versioned_repo.append_version({"id": 401, "name": "deleted"}, version=1)
        versioned_repo.soft_delete("id", 401, version=2)

        ch_client.command(f"OPTIMIZE TABLE {TEST_TABLE} FINAL")
        result = versioned_repo.read_active()
        active_ids = [r["id"] for r in result.rows]
        assert 400 in active_ids
        assert 401 not in active_ids

    def test_read_active_returns_query_result(self, versioned_repo):
        from axiom.olap.clickhouse.result.models import QueryResult

        result = versioned_repo.read_active()
        assert isinstance(result, QueryResult)


class TestDeduplicatedCount:
    def test_deduplicated_count_counts_distinct_ids(self, versioned_repo, ch_client):
        versioned_repo.append_version({"id": 500, "name": "a"}, version=1)
        versioned_repo.append_version({"id": 500, "name": "a_v2"}, version=2)
        versioned_repo.append_version({"id": 501, "name": "b"}, version=1)

        ch_client.command(f"OPTIMIZE TABLE {TEST_TABLE} FINAL")
        count = versioned_repo.deduplicated_count("id")
        assert count >= 2


class TestAsyncVersionedRepository:
    async def test_append_version_async(self, async_versioned_repo):
        result = await async_versioned_repo.append_version({"id": 1, "name": "async_v1"}, version=1)
        assert result.success is True

    async def test_soft_delete_raises_config_error_async(self, async_ch_client):
        repo = AsyncVersionedClickHouseRepository(
            client=async_ch_client,
            table=f"{TEST_TABLE}_async",
            version_column="version",
            is_deleted_column=None,
        )
        with pytest.raises(ClickHouseConfigError):
            await repo.soft_delete("id", 1, version=99)

    async def test_get_latest_with_final_async(self, async_versioned_repo, async_ch_client):
        await async_versioned_repo.append_version({"id": 200, "name": "v1"}, version=1)
        await async_versioned_repo.append_version({"id": 200, "name": "v2"}, version=2)
        await async_ch_client.command(f"OPTIMIZE TABLE {TEST_TABLE}_async FINAL")

        result = await async_versioned_repo.get_latest_with_final()
        assert result.row_count >= 1

    async def test_read_active_async(self, async_versioned_repo, async_ch_client):
        await async_versioned_repo.append_version({"id": 300, "name": "active"}, version=1)
        await async_versioned_repo.soft_delete("id", 300, version=2)
        await async_ch_client.command(f"OPTIMIZE TABLE {TEST_TABLE}_async FINAL")

        result = await async_versioned_repo.read_active()
        active_ids = [r["id"] for r in result.rows]
        assert 300 not in active_ids
