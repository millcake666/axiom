"""Unit tests for axiom.olap.clickhouse.query.specs."""

import pytest
from pydantic import ValidationError

from axiom.olap.clickhouse.query.specs import (
    AggFunction,
    AggregateSpec,
    CHQuerySpec,
    GroupBySpec,
    MetricSpec,
    PageSpec,
    SortSpec,
)


class TestPageSpec:
    def test_defaults(self):
        page = PageSpec()
        assert page.offset == 0
        assert page.limit == 100

    def test_custom_values(self):
        page = PageSpec(offset=50, limit=200)
        assert page.offset == 50
        assert page.limit == 200

    def test_limit_min_validation(self):
        with pytest.raises(ValidationError):
            PageSpec(limit=0)

    def test_limit_max_validation(self):
        with pytest.raises(ValidationError):
            PageSpec(limit=10001)

    def test_limit_boundary_min(self):
        page = PageSpec(limit=1)
        assert page.limit == 1

    def test_limit_boundary_max(self):
        page = PageSpec(limit=10000)
        assert page.limit == 10000


class TestSortSpec:
    def test_defaults(self):
        from axiom.core.filter import SortTypeEnum

        spec = SortSpec(field="created_at")
        assert spec.direction == SortTypeEnum.asc

    def test_desc(self):
        from axiom.core.filter import SortTypeEnum

        spec = SortSpec(field="name", direction=SortTypeEnum.desc)
        assert spec.direction == SortTypeEnum.desc

    def test_field_required(self):
        with pytest.raises(ValidationError):
            SortSpec()


class TestMetricSpec:
    def test_creation(self):
        m = MetricSpec(function=AggFunction.COUNT, field="id", alias="total")
        assert m.function == AggFunction.COUNT
        assert m.field == "id"
        assert m.alias == "total"

    def test_all_functions(self):
        for fn in AggFunction:
            m = MetricSpec(function=fn, field="x", alias="y")
            assert m.function == fn


class TestGroupBySpec:
    def test_fields(self):
        g = GroupBySpec(fields=["status", "region"])
        assert g.fields == ["status", "region"]

    def test_empty_fields(self):
        g = GroupBySpec(fields=[])
        assert g.fields == []


class TestAggregateSpec:
    def test_minimal(self):
        metrics = [MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")]
        spec = AggregateSpec(metrics=metrics)
        assert len(spec.metrics) == 1
        assert spec.group_by is None
        assert spec.having is None
        assert spec.page is None

    def test_full(self):
        metrics = [MetricSpec(function=AggFunction.SUM, field="amount", alias="total")]
        group_by = GroupBySpec(fields=["category"])
        page = PageSpec(offset=0, limit=50)
        spec = AggregateSpec(metrics=metrics, group_by=group_by, page=page)
        assert spec.group_by == group_by
        assert spec.page == page


class TestCHQuerySpec:
    def test_empty(self):
        spec = CHQuerySpec()
        assert spec.filters is None
        assert spec.columns is None
        assert spec.order_by is None
        assert spec.page is None

    def test_with_page(self):
        page = PageSpec(offset=10, limit=25)
        spec = CHQuerySpec(page=page)
        assert spec.page == page

    def test_with_columns(self):
        spec = CHQuerySpec(columns=["id", "name", "created_at"])
        assert spec.columns == ["id", "name", "created_at"]
