# ruff: noqa: S608
"""Integration tests for ClickHouseSchemaManager."""

from __future__ import annotations

import pytest

from axiom.olap.clickhouse.repository.schema.sync_ import ClickHouseSchemaManager

TEST_TABLE = "test_schema_table"

CREATE_DDL = f"""
CREATE TABLE IF NOT EXISTS {TEST_TABLE} (
    id UInt64,
    name String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY id
"""


@pytest.fixture(scope="module")
def schema_manager(ch_client):
    yield ClickHouseSchemaManager(client=ch_client)
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")


class TestTableExists:
    def test_table_does_not_exist(self, schema_manager):
        assert schema_manager.table_exists("nonexistent_table_xyz_abc") is False

    def test_table_exists_after_create(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        assert schema_manager.table_exists(TEST_TABLE) is True


class TestListTables:
    def test_lists_tables(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        tables = schema_manager.list_tables()
        assert isinstance(tables, list)
        assert TEST_TABLE in tables


class TestDescribeTable:
    def test_describe_returns_table_info(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        info = schema_manager.describe_table(TEST_TABLE)
        assert info.name == TEST_TABLE
        col_names = [c.name for c in info.columns]
        assert "id" in col_names
        assert "name" in col_names


class TestGetCreateTableDdl:
    def test_returns_ddl_string(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        ddl = schema_manager.get_create_table_ddl(TEST_TABLE)
        assert TEST_TABLE in ddl
        assert "MergeTree" in ddl


class TestDropTable:
    def test_drop_if_exists(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        schema_manager.drop_table(TEST_TABLE, if_exists=True)
        assert schema_manager.table_exists(TEST_TABLE) is False

    def test_drop_if_exists_nonexistent(self, schema_manager):
        # Should not raise
        schema_manager.drop_table("nonexistent_xyz_table", if_exists=True)


class TestTruncateTable:
    def test_truncate_empties_table(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        from datetime import datetime

        ch_client.insert(
            TEST_TABLE,
            [[1, "test", datetime.now()]],
            column_names=["id", "name", "created_at"],
        )
        schema_manager.truncate_table(TEST_TABLE)
        result = ch_client.query(f"SELECT COUNT(*) as cnt FROM {TEST_TABLE}")
        rows = list(result.named_results())
        assert rows[0]["cnt"] == 0
        ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")


class TestOptimizeTable:
    def test_optimize_runs_without_error(self, schema_manager, ch_client):
        ch_client.command(CREATE_DDL)
        schema_manager.optimize_table(TEST_TABLE)
        ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")
