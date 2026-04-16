"""Unit tests for axiom.olap.clickhouse.query.builder."""

import pytest

from axiom.core.filter import (
    FilterGroup,
    FilterParam,
    FilterRequest,
    FilterType,
    QueryOperator,
    SortTypeEnum,
)
from axiom.olap.clickhouse.query.builder import (
    ALLOWED_INTERVALS,
    ClickHouseQueryBuilder,
    build_group_by,
    build_limit_offset,
    build_order_by,
    build_select_columns,
    build_select_metrics,
    build_time_bucket,
    build_where,
)
from axiom.olap.clickhouse.query.specs import (
    AggFunction,
    GroupBySpec,
    MetricSpec,
    PageSpec,
    SortSpec,
)


def make_filter(field: str, op: QueryOperator, value: object) -> FilterRequest:
    """Helper to build a simple FilterRequest with a single FilterParam."""
    return FilterRequest(chain=FilterParam(field=field, operator=op, value=value))


def make_and_filter(params: list[tuple[str, QueryOperator, object]]) -> FilterRequest:
    """Helper to build a FilterRequest with AND-combined FilterParams."""
    items = [FilterParam(field=f, operator=op, value=v) for f, op, v in params]
    if len(items) == 1:
        return FilterRequest(chain=items[0])
    group = FilterGroup(type=FilterType.AND, items=items)
    return FilterRequest(chain=group)


def make_or_filter(params: list[tuple[str, QueryOperator, object]]) -> FilterRequest:
    """Helper to build a FilterRequest with OR-combined FilterParams."""
    items = [FilterParam(field=f, operator=op, value=v) for f, op, v in params]
    group = FilterGroup(type=FilterType.OR, items=items)
    return FilterRequest(chain=group)


class TestBuildWhere:
    def test_equals(self):
        fr = make_filter("status", QueryOperator.EQUALS, "active")
        clause, params = build_where(fr)
        assert "status = {p0:String}" == clause
        assert params["p0"] == "active"

    def test_not_equal(self):
        fr = make_filter("status", QueryOperator.NOT_EQUAL, "deleted")
        clause, params = build_where(fr)
        assert clause == "status != {p0:String}"
        assert params["p0"] == "deleted"

    def test_in(self):
        fr = make_filter("id", QueryOperator.IN, [1, 2, 3])
        clause, params = build_where(fr)
        assert clause == "id IN {p0:Array(Int64)}"
        assert params["p0"] == [1, 2, 3]

    def test_not_in(self):
        fr = make_filter("id", QueryOperator.NOT_IN, [4, 5])
        clause, params = build_where(fr)
        assert clause == "id NOT IN {p0:Array(Int64)}"

    def test_greater(self):
        fr = make_filter("age", QueryOperator.GREATER, 18)
        clause, params = build_where(fr)
        assert clause == "age > {p0:Int64}"
        assert params["p0"] == 18

    def test_equals_or_greater(self):
        fr = make_filter("age", QueryOperator.EQUALS_OR_GREATER, 18)
        clause, params = build_where(fr)
        assert clause == "age >= {p0:Int64}"

    def test_less(self):
        fr = make_filter("age", QueryOperator.LESS, 65)
        clause, params = build_where(fr)
        assert clause == "age < {p0:Int64}"

    def test_equals_or_less(self):
        fr = make_filter("age", QueryOperator.EQUALS_OR_LESS, 65)
        clause, params = build_where(fr)
        assert clause == "age <= {p0:Int64}"

    def test_starts_with(self):
        fr = make_filter("name", QueryOperator.STARTS_WITH, "Jo")
        clause, params = build_where(fr)
        assert clause == "name LIKE {p0:String}"
        assert params["p0"] == "Jo%"

    def test_not_starts_with(self):
        fr = make_filter("name", QueryOperator.NOT_START_WITH, "Jo")
        clause, params = build_where(fr)
        assert clause == "name NOT LIKE {p0:String}"
        assert params["p0"] == "Jo%"

    def test_ends_with(self):
        fr = make_filter("name", QueryOperator.ENDS_WITH, "son")
        clause, params = build_where(fr)
        assert clause == "name LIKE {p0:String}"
        assert params["p0"] == "%son"

    def test_not_ends_with(self):
        fr = make_filter("name", QueryOperator.NOT_END_WITH, "son")
        clause, params = build_where(fr)
        assert clause == "name NOT LIKE {p0:String}"

    def test_contains(self):
        fr = make_filter("description", QueryOperator.CONTAINS, "foo")
        clause, params = build_where(fr)
        assert clause == "description LIKE {p0:String}"
        assert params["p0"] == "%foo%"

    def test_not_contains(self):
        fr = make_filter("description", QueryOperator.NOT_CONTAIN, "foo")
        clause, params = build_where(fr)
        assert clause == "description NOT LIKE {p0:String}"

    def test_like_escaping_percent(self):
        fr = make_filter("name", QueryOperator.CONTAINS, "50%")
        _, params = build_where(fr)
        assert "\\%" in params["p0"]

    def test_like_escaping_underscore(self):
        fr = make_filter("code", QueryOperator.STARTS_WITH, "A_B")
        _, params = build_where(fr)
        assert "\\_" in params["p0"]

    def test_and_grouping(self):
        fr = make_and_filter(
            [
                ("status", QueryOperator.EQUALS, "active"),
                ("age", QueryOperator.GREATER, 18),
            ],
        )
        clause, params = build_where(fr)
        assert "AND" in clause
        assert len(params) == 2

    def test_or_grouping(self):
        fr = make_or_filter(
            [
                ("status", QueryOperator.EQUALS, "active"),
                ("status", QueryOperator.EQUALS, "pending"),
            ],
        )
        clause, params = build_where(fr)
        assert "OR" in clause
        assert len(params) == 2

    def test_invalid_column_name(self):
        fr = make_filter("'; DROP TABLE--", QueryOperator.EQUALS, "x")
        with pytest.raises(ValueError, match="Invalid column name"):
            build_where(fr)

    def test_dotted_column_name(self):
        fr = make_filter("table.column", QueryOperator.EQUALS, "x")
        clause, _ = build_where(fr)
        assert "table.column" in clause


class TestBuildOrderBy:
    def test_empty(self):
        assert build_order_by([]) == ""

    def test_single_asc(self):
        result = build_order_by([SortSpec(field="name")])
        assert result == "name ASC"

    def test_single_desc(self):
        result = build_order_by([SortSpec(field="created_at", direction=SortTypeEnum.desc)])
        assert result == "created_at DESC"

    def test_multiple(self):
        specs = [
            SortSpec(field="name", direction=SortTypeEnum.asc),
            SortSpec(field="age", direction=SortTypeEnum.desc),
        ]
        result = build_order_by(specs)
        assert result == "name ASC, age DESC"

    def test_invalid_column(self):
        with pytest.raises(ValueError):
            build_order_by([SortSpec(field="'; bad")])


class TestBuildLimitOffset:
    def test_default(self):
        result = build_limit_offset(PageSpec())
        assert result == "LIMIT 100 OFFSET 0"

    def test_custom(self):
        result = build_limit_offset(PageSpec(offset=50, limit=25))
        assert result == "LIMIT 25 OFFSET 50"


class TestBuildGroupBy:
    def test_single_field(self):
        result = build_group_by(GroupBySpec(fields=["category"]))
        assert result == "category"

    def test_multiple_fields(self):
        result = build_group_by(GroupBySpec(fields=["region", "category"]))
        assert result == "region, category"

    def test_invalid_field(self):
        with pytest.raises(ValueError):
            build_group_by(GroupBySpec(fields=["bad; field"]))


class TestBuildSelectColumns:
    def test_empty_returns_star(self):
        assert build_select_columns([]) == "*"

    def test_single_column(self):
        assert build_select_columns(["id"]) == "id"

    def test_multiple_columns(self):
        result = build_select_columns(["id", "name", "created_at"])
        assert result == "id, name, created_at"

    def test_invalid_column(self):
        with pytest.raises(ValueError):
            build_select_columns(["id", "'; DROP TABLE--"])


class TestBuildSelectMetrics:
    def test_count(self):
        m = MetricSpec(function=AggFunction.COUNT, field="id", alias="total")
        result = build_select_metrics([m])
        assert result == "COUNT(id) AS total"

    def test_multiple_metrics(self):
        metrics = [
            MetricSpec(function=AggFunction.SUM, field="amount", alias="total_amount"),
            MetricSpec(function=AggFunction.AVG, field="price", alias="avg_price"),
        ]
        result = build_select_metrics(metrics)
        assert "SUM(amount) AS total_amount" in result
        assert "AVG(price) AS avg_price" in result


class TestBuildTimeBucket:
    def test_minute(self):
        result = build_time_bucket("ts", "1m")
        assert "toStartOfMinute(ts)" == result

    def test_hour(self):
        result = build_time_bucket("ts", "1h")
        assert "toStartOfHour(ts)" == result

    def test_day(self):
        result = build_time_bucket("ts", "1d")
        assert "toStartOfDay(ts)" == result

    def test_week(self):
        result = build_time_bucket("event_time", "1w")
        assert "toStartOfWeek(event_time)" == result

    def test_invalid_interval(self):
        with pytest.raises(ValueError, match="not allowed"):
            build_time_bucket("ts", "2d")

    def test_all_allowed_intervals_work(self):
        for interval in ALLOWED_INTERVALS:
            result = build_time_bucket("ts", interval)
            assert result  # non-empty


class TestClickHouseQueryBuilder:
    """Tests for the ClickHouseQueryBuilder class (delegates to module-level functions)."""

    def setup_method(self):
        self.builder = ClickHouseQueryBuilder()

    def test_build_where_equals(self):
        fr = make_filter("status", QueryOperator.EQUALS, "active")
        clause, params = self.builder.build_where(fr)
        assert clause == "status = {p0:String}"
        assert params["p0"] == "active"

    def test_build_order_by(self):
        result = self.builder.build_order_by([SortSpec(field="name")])
        assert result == "name ASC"

    def test_build_order_by_empty(self):
        assert self.builder.build_order_by([]) == ""

    def test_build_limit_offset(self):
        result = self.builder.build_limit_offset(PageSpec(offset=10, limit=50))
        assert result == "LIMIT 50 OFFSET 10"

    def test_build_group_by(self):
        result = self.builder.build_group_by(GroupBySpec(fields=["region", "status"]))
        assert result == "region, status"

    def test_build_having(self):
        fr = make_filter("total", QueryOperator.GREATER, 100)
        clause, params = self.builder.build_having(fr)
        assert clause == "total > {p0:Int64}"
        assert params["p0"] == 100

    def test_build_select_columns_empty(self):
        assert self.builder.build_select_columns([]) == "*"

    def test_build_select_columns(self):
        result = self.builder.build_select_columns(["id", "name"])
        assert result == "id, name"

    def test_build_select_columns_injection_protection(self):
        with pytest.raises(ValueError):
            self.builder.build_select_columns(["id", "'; DROP TABLE--"])
