# ruff: noqa: S608
"""Integration tests for ClickHouseWriteRepository."""

from __future__ import annotations

import time

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.olap.clickhouse.repository.write.sync_ import ClickHouseWriteRepository

TEST_TABLE = "test_write_events"

CREATE_DDL = f"""
CREATE TABLE IF NOT EXISTS {TEST_TABLE} (
    id UInt64,
    name String,
    value Float64
) ENGINE = MergeTree()
ORDER BY id
"""


@pytest.fixture(scope="module")
def write_repo(ch_client):
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")
    ch_client.command(CREATE_DDL)
    yield ClickHouseWriteRepository(client=ch_client, table=TEST_TABLE)
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")


@pytest.fixture(autouse=True)
def truncate_table(ch_client):
    yield
    ch_client.command(f"TRUNCATE TABLE {TEST_TABLE}")


class TestInsert:
    def test_insert_single_row(self, write_repo, ch_client):
        result = write_repo.insert({"id": 1, "name": "alice", "value": 10.0})
        assert result.success is True
        qr = ch_client.query(f"SELECT COUNT(*) as cnt FROM {TEST_TABLE}")
        rows = list(qr.named_results())
        assert rows[0]["cnt"] >= 1

    def test_insert_returns_row(self, write_repo):
        row = {"id": 2, "name": "bob", "value": 20.0}
        result = write_repo.insert(row)
        assert result.row == row


class TestInsertMany:
    def test_insert_multiple_rows(self, write_repo, ch_client):
        rows = [
            {"id": 10, "name": "x", "value": 1.0},
            {"id": 11, "name": "y", "value": 2.0},
            {"id": 12, "name": "z", "value": 3.0},
        ]
        result = write_repo.insert_many(rows)
        assert result.success is True
        assert result.inserted == 3
        assert result.failed == 0

    def test_insert_empty_list(self, write_repo):
        result = write_repo.insert_many([])
        assert result.inserted == 0
        assert result.failed == 0


class TestInsertChunked:
    def test_chunked_insert(self, write_repo):
        rows = [{"id": 100 + i, "name": f"user_{i}", "value": float(i)} for i in range(25)]
        result = write_repo.insert_chunked(rows, chunk_size=10)
        assert result.success is True
        assert result.inserted == 25

    def test_chunked_empty(self, write_repo):
        result = write_repo.insert_chunked([], chunk_size=10)
        assert result.inserted == 0


class TestUpsert:
    def test_upsert_rows(self, write_repo):
        rows = [{"id": 200, "name": "upsert_test", "value": 99.0}]
        result = write_repo.upsert(rows)
        assert result.success is True
        assert result.inserted == 1


# ---------------------------------------------------------------------------
# CRUD-like operations (US-010)
# ---------------------------------------------------------------------------

REPLACING_TABLE = "test_write_replacing"

CREATE_REPLACING_DDL = f"""
CREATE TABLE IF NOT EXISTS {REPLACING_TABLE} (
    id UInt64,
    name String,
    version UInt64
) ENGINE = ReplacingMergeTree(version)
ORDER BY id
"""


@pytest.fixture(scope="module")
def replacing_repo(ch_client):
    ch_client.command(f"DROP TABLE IF EXISTS {REPLACING_TABLE}")
    ch_client.command(CREATE_REPLACING_DDL)
    yield ClickHouseWriteRepository(client=ch_client, table=REPLACING_TABLE)
    ch_client.command(f"DROP TABLE IF EXISTS {REPLACING_TABLE}")


@pytest.fixture(autouse=False)
def truncate_replacing(ch_client):
    yield
    ch_client.command(f"TRUNCATE TABLE IF EXISTS {REPLACING_TABLE}")


class TestUpdateByFilter:
    def test_update_creates_mutation(self, write_repo, ch_client):
        """update_by_filter should create an entry in system.mutations."""
        write_repo.insert_many(
            [
                {"id": 300, "name": "before", "value": 1.0},
                {"id": 301, "name": "before", "value": 2.0},
            ],
        )
        filters = FilterRequest(
            chain=FilterParam(field="name", operator=QueryOperator.EQUALS, value="before"),
        )
        write_repo.update_by_filter(filters, {"name": "after"})
        # Wait briefly for mutation to register
        time.sleep(0.5)
        qr = ch_client.query(
            f"SELECT count() as cnt FROM system.mutations WHERE table = '{TEST_TABLE}'",
        )
        rows = list(qr.named_results())
        assert rows[0]["cnt"] >= 1


class TestDeleteByFilter:
    def test_delete_creates_mutation(self, write_repo, ch_client):
        """delete_by_filter should create an async mutation on MergeTree."""
        write_repo.insert_many(
            [
                {"id": 400, "name": "to_delete", "value": 5.0},
            ],
        )
        filters = FilterRequest(
            chain=FilterParam(field="name", operator=QueryOperator.EQUALS, value="to_delete"),
        )
        write_repo.delete_by_filter(filters)
        time.sleep(0.5)
        qr = ch_client.query(
            f"SELECT count() as cnt FROM system.mutations WHERE table = '{TEST_TABLE}'",
        )
        rows = list(qr.named_results())
        assert rows[0]["cnt"] >= 1


class TestUpsertOnReplacingMergeTree:
    def test_upsert_appends_versions(self, replacing_repo, ch_client, truncate_replacing):
        """upsert on ReplacingMergeTree appends both versions; FINAL deduplicates."""
        rows_v1 = [{"id": 1, "name": "v1", "version": 1}]
        rows_v2 = [{"id": 1, "name": "v2", "version": 2}]
        result1 = replacing_repo.upsert(rows_v1)
        result2 = replacing_repo.upsert(rows_v2)
        assert result1.success is True
        assert result2.success is True
        # Before merge: both versions exist
        qr = ch_client.query(f"SELECT count() as cnt FROM {REPLACING_TABLE}")
        rows = list(qr.named_results())
        assert rows[0]["cnt"] >= 1
        # After FINAL: only latest version
        ch_client.command(f"OPTIMIZE TABLE {REPLACING_TABLE} FINAL")
        qr_final = ch_client.query(f"SELECT name FROM {REPLACING_TABLE} FINAL WHERE id = 1")
        final_rows = list(qr_final.named_results())
        assert len(final_rows) == 1
        assert final_rows[0]["name"] == "v2"
