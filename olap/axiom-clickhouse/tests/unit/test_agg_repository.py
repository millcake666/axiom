"""Unit tests for ClickHouseAggRepository and AsyncClickHouseAggRepository."""

from __future__ import annotations

from typing import Any

import pytest

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.core.filter.type import SortTypeEnum
from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.query.specs import (
    AggFunction,
    AggregateSpec,
    GroupBySpec,
    MetricSpec,
    PageSpec,
    SortSpec,
)
from axiom.olap.clickhouse.repository.agg.async_ import AsyncClickHouseAggRepository
from axiom.olap.clickhouse.repository.agg.sync_ import ClickHouseAggRepository
from axiom.olap.clickhouse.result.models import AggregateResult

# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class FakeSyncClient:
    """Test double for a synchronous clickhouse_connect client."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.queries: list[str] = []
        self._rows = rows or []
        self.raise_on_query: Exception | None = None

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        self.queries.append(query)
        if self.raise_on_query:
            raise self.raise_on_query

        class _Result:
            def __init__(self, rows: list[dict[str, Any]]) -> None:
                self._rows = rows
                self.query_id = "fake-qid"

            def named_results(self) -> list[dict[str, Any]]:
                return self._rows

        return _Result(self._rows)

    def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        return None


class FakeAsyncClient:
    """Test double for an asynchronous clickhouse_connect client."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.queries: list[str] = []
        self._rows = rows or []
        self.raise_on_query: Exception | None = None

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        self.queries.append(query)
        if self.raise_on_query:
            raise self.raise_on_query

        class _Result:
            def __init__(self, rows: list[dict[str, Any]]) -> None:
                self._rows = rows
                self.query_id = "fake-qid-async"

            def named_results(self) -> list[dict[str, Any]]:
                return self._rows

        return _Result(self._rows)

    async def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        return None


def _make_sync_repo(
    rows: list[dict[str, Any]] | None = None,
) -> tuple[ClickHouseAggRepository, FakeSyncClient]:
    client = FakeSyncClient(rows)
    repo = ClickHouseAggRepository(client=client, table="events")
    return repo, client


def _make_async_repo(
    rows: list[dict[str, Any]] | None = None,
) -> tuple[AsyncClickHouseAggRepository, FakeAsyncClient]:
    client = FakeAsyncClient(rows)
    repo = AsyncClickHouseAggRepository(client=client, table="events")
    return repo, client


def _make_filter(field: str = "status", value: str = "active") -> FilterRequest:
    return FilterRequest(chain=FilterParam(field=field, operator=QueryOperator.EQUALS, value=value))


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestClickHouseAggRepository:
    def test_aggregate_returns_aggregate_result(self) -> None:
        rows = [{"category": "A", "total": 10}]
        repo, client = _make_sync_repo(rows)
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.SUM, field="amount", alias="total")],
            group_by=GroupBySpec(fields=["category"]),
        )
        result = repo.aggregate(spec)
        assert isinstance(result, AggregateResult)
        assert result.row_count == 1
        assert result.rows[0]["total"] == 10

    def test_aggregate_builds_select_with_group_by(self) -> None:
        repo, client = _make_sync_repo()
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")],
            group_by=GroupBySpec(fields=["region"]),
        )
        repo.aggregate(spec)
        assert len(client.queries) == 1
        q = client.queries[0]
        assert "GROUP BY" in q
        assert "region" in q

    def test_aggregate_with_page_spec(self) -> None:
        repo, client = _make_sync_repo()
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")],
            page=PageSpec(offset=10, limit=5),
        )
        repo.aggregate(spec)
        q = client.queries[0]
        assert "LIMIT 5" in q
        assert "OFFSET 10" in q

    def test_aggregate_with_order_by(self) -> None:
        repo, client = _make_sync_repo()
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.SUM, field="val", alias="total")],
            order_by=[SortSpec(field="total", direction=SortTypeEnum.desc)],
        )
        repo.aggregate(spec)
        q = client.queries[0]
        assert "ORDER BY" in q
        assert "DESC" in q

    def test_aggregate_raises_on_query_error(self) -> None:
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("CH error")
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")],
        )
        with pytest.raises(ClickHouseQueryError, match="CH error"):
            repo.aggregate(spec)

    def test_count_by_returns_list_of_dicts(self) -> None:
        rows = [{"status": "ok", "count": 5}]
        repo, client = _make_sync_repo(rows)
        result = repo.count_by(GroupBySpec(fields=["status"]))
        assert len(result) == 1
        assert result[0]["count"] == 5

    def test_count_by_builds_correct_query(self) -> None:
        repo, client = _make_sync_repo()
        repo.count_by(GroupBySpec(fields=["region", "country"]))
        q = client.queries[0]
        assert "COUNT(*)" in q
        assert "GROUP BY" in q
        assert "region" in q
        assert "country" in q

    def test_count_by_with_filters_adds_where(self) -> None:
        repo, client = _make_sync_repo()
        repo.count_by(GroupBySpec(fields=["type"]), filters=_make_filter("active", "1"))
        q = client.queries[0]
        assert "WHERE" in q

    def test_count_by_empty_result(self) -> None:
        repo, client = _make_sync_repo([])
        result = repo.count_by(GroupBySpec(fields=["x"]))
        assert result == []

    def test_sum_by_builds_sum_query(self) -> None:
        repo, client = _make_sync_repo()
        repo.sum_by("revenue", GroupBySpec(fields=["product"]))
        q = client.queries[0]
        assert "SUM(revenue)" in q
        assert "GROUP BY" in q
        assert "product" in q

    def test_sum_by_with_filters(self) -> None:
        repo, client = _make_sync_repo()
        repo.sum_by("amount", GroupBySpec(fields=["cat"]), filters=_make_filter("active", "true"))
        q = client.queries[0]
        assert "WHERE" in q
        assert "SUM(amount)" in q

    def test_top_n_builds_order_by_desc_limit(self) -> None:
        repo, client = _make_sync_repo()
        metric = MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")
        repo.top_n("category", 5, metric)
        q = client.queries[0]
        assert "ORDER BY cnt DESC" in q
        assert "LIMIT 5" in q
        assert "GROUP BY category" in q

    def test_top_n_with_filters(self) -> None:
        repo, client = _make_sync_repo()
        metric = MetricSpec(function=AggFunction.SUM, field="sales", alias="total")
        repo.top_n("product", 3, metric, filters=_make_filter("year", "2024"))
        q = client.queries[0]
        assert "WHERE" in q

    def test_top_n_returns_list(self) -> None:
        rows = [{"category": "A", "cnt": 100}, {"category": "B", "cnt": 50}]
        repo, client = _make_sync_repo(rows)
        metric = MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")
        result = repo.top_n("category", 2, metric)
        assert len(result) == 2

    def test_time_series_builds_time_bucket_query(self) -> None:
        repo, client = _make_sync_repo()
        metrics = [MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")]
        repo.time_series("created_at", "1h", metrics)
        q = client.queries[0]
        assert "time_bucket" in q
        assert "GROUP BY time_bucket" in q

    def test_time_series_raises_on_invalid_interval(self) -> None:
        repo, client = _make_sync_repo()
        metrics = [MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")]
        with pytest.raises((ClickHouseQueryError, ValueError)):
            repo.time_series("ts", "invalid_interval", metrics)

    def test_time_series_returns_aggregate_result(self) -> None:
        rows = [{"time_bucket": "2024-01-01 00:00:00", "cnt": 42}]
        repo, client = _make_sync_repo(rows)
        metrics = [MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")]
        result = repo.time_series("created_at", "1h", metrics)
        assert isinstance(result, AggregateResult)
        assert result.row_count == 1

    def test_time_series_raises_on_query_error(self) -> None:
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("timeout")
        metrics = [MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")]
        with pytest.raises(ClickHouseQueryError, match="timeout"):
            repo.time_series("ts", "1h", metrics)

    def test_execute_analytical_returns_aggregate_result(self) -> None:
        rows = [{"x": 1}]
        repo, client = _make_sync_repo(rows)
        result = repo.execute_analytical("SELECT 1 AS x")
        assert isinstance(result, AggregateResult)
        assert result.rows[0]["x"] == 1
        assert result.query_id == "fake-qid"

    def test_execute_analytical_raises_on_error(self) -> None:
        repo, client = _make_sync_repo()
        client.raise_on_query = RuntimeError("bad query")
        with pytest.raises(ClickHouseQueryError, match="bad query"):
            repo.execute_analytical("SELECT bad syntax")

    def test_aggregate_no_filters_no_where(self) -> None:
        repo, client = _make_sync_repo()
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.AVG, field="score", alias="avg_score")],
        )
        repo.aggregate(spec)
        q = client.queries[0]
        assert "WHERE" not in q


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAsyncClickHouseAggRepository:
    async def test_aggregate_returns_aggregate_result(self) -> None:
        rows = [{"region": "EU", "revenue": 999}]
        repo, client = _make_async_repo(rows)
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.SUM, field="revenue", alias="revenue")],
            group_by=GroupBySpec(fields=["region"]),
        )
        result = await repo.aggregate(spec)
        assert isinstance(result, AggregateResult)
        assert result.row_count == 1

    async def test_aggregate_raises_on_error(self) -> None:
        repo, client = _make_async_repo()
        client.raise_on_query = RuntimeError("async error")
        spec = AggregateSpec(
            metrics=[MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")],
        )
        with pytest.raises(ClickHouseQueryError, match="async error"):
            await repo.aggregate(spec)

    async def test_count_by_empty(self) -> None:
        repo, client = _make_async_repo([])
        result = await repo.count_by(GroupBySpec(fields=["x"]))
        assert result == []

    async def test_count_by_with_filters(self) -> None:
        repo, client = _make_async_repo()
        await repo.count_by(GroupBySpec(fields=["type"]), filters=_make_filter())
        q = client.queries[0]
        assert "WHERE" in q
        assert "COUNT(*)" in q

    async def test_sum_by_builds_query(self) -> None:
        repo, client = _make_async_repo()
        await repo.sum_by("price", GroupBySpec(fields=["category"]))
        q = client.queries[0]
        assert "SUM(price)" in q
        assert "GROUP BY" in q

    async def test_top_n_builds_correct_query(self) -> None:
        repo, client = _make_async_repo()
        metric = MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")
        await repo.top_n("product", 10, metric)
        q = client.queries[0]
        assert "ORDER BY cnt DESC" in q
        assert "LIMIT 10" in q

    async def test_time_series_returns_aggregate_result(self) -> None:
        rows = [{"time_bucket": "2024-01-01", "cnt": 7}]
        repo, client = _make_async_repo(rows)
        metrics = [MetricSpec(function=AggFunction.COUNT, field="id", alias="cnt")]
        result = await repo.time_series("created_at", "1d", metrics)
        assert isinstance(result, AggregateResult)
        assert result.row_count == 1

    async def test_time_series_with_filters(self) -> None:
        repo, client = _make_async_repo()
        metrics = [MetricSpec(function=AggFunction.SUM, field="val", alias="total")]
        await repo.time_series("ts", "1h", metrics, filters=_make_filter("active", "1"))
        q = client.queries[0]
        assert "WHERE" in q

    async def test_execute_analytical_returns_result(self) -> None:
        rows = [{"cnt": 42}]
        repo, client = _make_async_repo(rows)
        result = await repo.execute_analytical("SELECT COUNT(*) AS cnt FROM events")
        assert isinstance(result, AggregateResult)
        assert result.rows[0]["cnt"] == 42

    async def test_execute_analytical_raises_on_error(self) -> None:
        repo, client = _make_async_repo()
        client.raise_on_query = RuntimeError("async bad query")
        with pytest.raises(ClickHouseQueryError, match="async bad query"):
            await repo.execute_analytical("SELECT 1")
