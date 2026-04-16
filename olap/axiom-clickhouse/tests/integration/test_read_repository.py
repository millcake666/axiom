# ruff: noqa: S608
"""Integration tests for ClickHouseReadRepository."""

from __future__ import annotations

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator, SortTypeEnum
from axiom.olap.clickhouse.query.specs import CHQuerySpec, PageSpec, SortSpec
from axiom.olap.clickhouse.repository.read.sync_ import ClickHouseReadRepository

TEST_TABLE = "test_read_events"

CREATE_DDL = f"""
CREATE TABLE IF NOT EXISTS {TEST_TABLE} (
    id UInt64,
    name String,
    status String,
    value Float64
) ENGINE = MergeTree()
ORDER BY id
"""

SAMPLE_ROWS = [
    {"id": 1, "name": "alice", "status": "active", "value": 10.5},
    {"id": 2, "name": "bob", "status": "inactive", "value": 20.0},
    {"id": 3, "name": "carol", "status": "active", "value": 30.0},
    {"id": 4, "name": "dave", "status": "active", "value": 5.0},
    {"id": 5, "name": "eve", "status": "inactive", "value": 15.0},
]


@pytest.fixture(scope="module")
def read_repo(ch_client):
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")
    ch_client.command(CREATE_DDL)
    cols = list(SAMPLE_ROWS[0].keys())
    data = [[row[c] for c in cols] for row in SAMPLE_ROWS]
    ch_client.insert(TEST_TABLE, data, column_names=cols)
    yield ClickHouseReadRepository(client=ch_client, table=TEST_TABLE)
    ch_client.command(f"DROP TABLE IF EXISTS {TEST_TABLE}")


class TestFetchAll:
    def test_returns_all_rows(self, read_repo):
        result = read_repo.fetch_all()
        assert result.row_count == 5

    def test_with_columns(self, read_repo):
        spec = CHQuerySpec(columns=["id", "name"])
        result = read_repo.fetch_all(spec)
        for row in result.rows:
            assert set(row.keys()) == {"id", "name"}

    def test_with_page(self, read_repo):
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=2))
        result = read_repo.fetch_all(spec)
        assert result.row_count == 2

    def test_with_order_by_desc(self, read_repo):
        spec = CHQuerySpec(order_by=[SortSpec(field="id", direction=SortTypeEnum.desc)])
        result = read_repo.fetch_all(spec)
        ids = [row["id"] for row in result.rows]
        assert ids == sorted(ids, reverse=True)


class TestFetchOne:
    def test_returns_matching_row(self, read_repo):
        fr = FilterRequest(
            chain=FilterParam(field="name", operator=QueryOperator.EQUALS, value="alice"),
        )
        row = read_repo.fetch_one(fr)
        assert row is not None
        assert row["name"] == "alice"

    def test_returns_none_when_no_match(self, read_repo):
        fr = FilterRequest(
            chain=FilterParam(field="name", operator=QueryOperator.EQUALS, value="nobody"),
        )
        row = read_repo.fetch_one(fr)
        assert row is None


class TestCount:
    def test_total_count(self, read_repo):
        assert read_repo.count() == 5

    def test_filtered_count(self, read_repo):
        fr = FilterRequest(
            chain=FilterParam(field="status", operator=QueryOperator.EQUALS, value="active"),
        )
        assert read_repo.count(fr) == 3


class TestExists:
    def test_exists_true(self, read_repo):
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=1))
        assert read_repo.exists(fr) is True

    def test_exists_false(self, read_repo):
        fr = FilterRequest(chain=FilterParam(field="id", operator=QueryOperator.EQUALS, value=999))
        assert read_repo.exists(fr) is False


class TestFetchPaged:
    def test_paged_result(self, read_repo):
        spec = CHQuerySpec(page=PageSpec(offset=0, limit=2))
        result = read_repo.fetch_paged(spec)
        assert result.total == 5
        assert len(result.rows) == 2
        assert result.has_next is True

    def test_last_page(self, read_repo):
        spec = CHQuerySpec(page=PageSpec(offset=4, limit=10))
        result = read_repo.fetch_paged(spec)
        assert result.has_next is False


class TestFetchById:
    def test_found(self, read_repo):
        row = read_repo.fetch_by_id("id", 2)
        assert row is not None
        assert row["id"] == 2

    def test_not_found(self, read_repo):
        row = read_repo.fetch_by_id("id", 999)
        assert row is None


class TestStream:
    def test_streams_all_rows(self, read_repo):
        all_rows = []
        for block in read_repo.stream(f"SELECT * FROM {TEST_TABLE} ORDER BY id"):
            all_rows.extend(block)
        assert len(all_rows) == 5


class TestExecuteSelect:
    def test_raw_select(self, read_repo):
        result = read_repo.execute_select(f"SELECT id, name FROM {TEST_TABLE} ORDER BY id LIMIT 3")
        assert result.row_count == 3
