"""Unit tests for axiom.olap.clickhouse.result.models."""

from datetime import datetime

from axiom.olap.clickhouse.result.models import (
    AggregateResult,
    BulkInsertResult,
    ColumnInfo,
    MutationStatus,
    PagedResult,
    QueryResult,
    SingleInsertResult,
    TableInfo,
)


class TestQueryResult:
    def test_basic(self):
        rows = [{"id": 1}, {"id": 2}]
        r = QueryResult(rows=rows, row_count=2)
        assert r.rows == rows
        assert r.row_count == 2
        assert r.query_id is None

    def test_with_query_id(self):
        r = QueryResult(rows=[], row_count=0, query_id="abc-123")
        assert r.query_id == "abc-123"


class TestPagedResult:
    def test_has_next_true(self):
        r = PagedResult(rows=[], total=100, offset=0, limit=10)
        assert r.has_next is True

    def test_has_next_false_exact(self):
        r = PagedResult(rows=[], total=10, offset=0, limit=10)
        assert r.has_next is False

    def test_has_next_false_over(self):
        r = PagedResult(rows=[], total=5, offset=0, limit=10)
        assert r.has_next is False

    def test_has_next_last_page(self):
        r = PagedResult(rows=[], total=25, offset=20, limit=10)
        assert r.has_next is False

    def test_has_next_middle_page(self):
        r = PagedResult(rows=[], total=50, offset=10, limit=10)
        assert r.has_next is True


class TestBulkInsertResult:
    def test_success_true(self):
        r = BulkInsertResult(inserted=10, failed=0, errors=[])
        assert r.success is True

    def test_success_false(self):
        r = BulkInsertResult(inserted=5, failed=3, errors=["err1", "err2", "err3"])
        assert r.success is False

    def test_all_failed(self):
        r = BulkInsertResult(inserted=0, failed=10, errors=["oops"])
        assert r.success is False
        assert r.inserted == 0


class TestSingleInsertResult:
    def test_success(self):
        r = SingleInsertResult(success=True, row={"id": 1, "name": "test"})
        assert r.success is True
        assert r.row["id"] == 1

    def test_failure(self):
        r = SingleInsertResult(success=False, row={})
        assert r.success is False


class TestMutationStatus:
    def test_done(self):
        m = MutationStatus(
            mutation_id="0000000001",
            table="events",
            command="UPDATE x = 1 WHERE id = 1",
            is_done=True,
            parts_to_do=0,
            create_time=None,
            error=None,
        )
        assert m.is_done is True
        assert m.error is None

    def test_with_error(self):
        m = MutationStatus(
            mutation_id="0000000002",
            table="events",
            command="DELETE WHERE id = 99",
            is_done=False,
            parts_to_do=3,
            create_time=datetime(2026, 1, 1, 12, 0, 0),
            error="some error",
        )
        assert m.error == "some error"
        assert m.parts_to_do == 3


class TestColumnInfo:
    def test_defaults(self):
        c = ColumnInfo(name="id", type="UInt64")
        assert c.default_kind == ""
        assert c.default_expression == ""
        assert c.comment == ""

    def test_full(self):
        c = ColumnInfo(
            name="status",
            type="String",
            default_kind="DEFAULT",
            default_expression="'active'",
            comment="row status",
        )
        assert c.default_kind == "DEFAULT"
        assert c.comment == "row status"


class TestTableInfo:
    def test_creation(self):
        cols = [ColumnInfo(name="id", type="UInt64")]
        t = TableInfo(
            database="default",
            name="events",
            engine="MergeTree",
            create_table_query="CREATE TABLE events ...",
            columns=cols,
        )
        assert t.database == "default"
        assert t.engine == "MergeTree"
        assert len(t.columns) == 1


class TestAggregateResult:
    def test_basic(self):
        rows = [{"category": "a", "count": 10}]
        r = AggregateResult(rows=rows, row_count=1)
        assert r.rows == rows
        assert r.row_count == 1
        assert r.query_id is None
