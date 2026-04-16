# ruff: noqa: S608
"""Integration tests for ClickHouseRepository facade."""

from __future__ import annotations

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.olap.clickhouse.query.specs import CHQuerySpec, PageSpec
from axiom.olap.clickhouse.repository.facade.sync_ import ClickHouseRepository

TEST_TABLE = "test_facade_events"

CREATE_DDL = f"""
CREATE TABLE IF NOT EXISTS {TEST_TABLE} (
    id UInt64,
    category String,
    amount Float64
) ENGINE = MergeTree()
ORDER BY id
"""

SAMPLE_ROWS = [
    {"id": 1, "category": "A", "amount": 100.0},
    {"id": 2, "category": "B", "amount": 200.0},
    {"id": 3, "category": "A", "amount": 150.0},
    {"id": 4, "category": "C", "amount": 50.0},
    {"id": 5, "category": "B", "amount": 75.0},
]


@pytest.fixture(scope="module")
def facade_repo(ch_client):
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")
    ch_client.command(CREATE_DDL)
    cols = list(SAMPLE_ROWS[0].keys())
    data = [[row[c] for c in cols] for row in SAMPLE_ROWS]
    ch_client.insert(TEST_TABLE, data, column_names=cols)
    yield ClickHouseRepository(client=ch_client, table=TEST_TABLE)
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")


class TestFacadeRead:
    def test_fetch_all(self, facade_repo):
        result = facade_repo.fetch_all()
        assert result.row_count == 5

    def test_count(self, facade_repo):
        assert facade_repo.count() == 5

    def test_exists(self, facade_repo):
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        assert facade_repo.exists(fr) is True

    def test_paged(self, facade_repo):
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=3))
        result = facade_repo.fetch_paged(spec)
        assert len(result.rows) == 3
        assert result.total == 5
        assert result.has_next is True


class TestFacadeRaw:
    def test_raw_select(self, facade_repo):
        result = facade_repo.raw(f"SELECT id, amount FROM {TEST_TABLE} ORDER BY id LIMIT 2")
        assert result.row_count == 2

    def test_raw_command(self, facade_repo):
        result = facade_repo.raw_command("SELECT 1")
        assert isinstance(result, int)


class TestFacadeSchema:
    def test_schema_property(self, facade_repo):
        schema = facade_repo.schema
        assert schema is not None
        # schema manager is same instance on second access (lazy)
        assert facade_repo.schema is schema

    def test_schema_table_exists(self, facade_repo):
        assert facade_repo.schema.table_exists(TEST_TABLE) is True


class TestFacadeMutations:
    def test_mutations_property(self, facade_repo):
        mutations = facade_repo.mutations
        assert mutations is not None
        assert facade_repo.mutations is mutations

    def test_list_mutations(self, facade_repo):
        mutations = facade_repo.mutations.list_mutations(TEST_TABLE)
        assert isinstance(mutations, list)


class TestFacadeFromClient:
    def test_from_client(self, ch_client):
        repo = ClickHouseRepository.from_client(ch_client, TEST_TABLE)
        assert repo._table == TEST_TABLE
        result = repo.fetch_all()
        assert result.row_count == 5
