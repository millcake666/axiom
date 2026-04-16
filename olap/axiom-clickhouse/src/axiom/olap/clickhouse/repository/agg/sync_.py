# ruff: noqa: S608
"""axiom.olap.clickhouse.repository.agg.sync_ — Synchronous aggregation ClickHouse repository."""

from __future__ import annotations

from typing import Any

from axiom.core.filter import FilterRequest
from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.query.builder import (
    build_group_by,
    build_having,
    build_limit_offset,
    build_order_by,
    build_select_metrics,
    build_time_bucket,
    build_where,
    validate_identifier,
)
from axiom.olap.clickhouse.query.specs import AggregateSpec, GroupBySpec, MetricSpec
from axiom.olap.clickhouse.repository.base.sync_ import ClickHouseBaseRepository
from axiom.olap.clickhouse.result.models import AggregateResult


class ClickHouseAggRepository(ClickHouseBaseRepository):
    """Synchronous aggregation repository for ClickHouse analytical queries."""

    def aggregate(
        self,
        spec: AggregateSpec,
        settings: dict[str, Any] | None = None,
    ) -> AggregateResult:
        """Execute an aggregation query from a full AggregateSpec.

        Args:
            spec: Aggregation specification with metrics, group-by, filters, etc.
            settings: Optional ClickHouse query settings.

        Returns:
            AggregateResult with rows as dicts.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}

        select_clause = build_select_metrics(spec.metrics)
        if spec.group_by:
            group_fields = build_group_by(spec.group_by)
            select_clause = f"{group_fields}, {select_clause}"

        query = f"SELECT {select_clause} FROM {table}"  # nosec B608

        if spec.group_by:
            query += f" GROUP BY {build_group_by(spec.group_by)}"

        if spec.having:
            having_clause, having_params = build_having(spec.having)
            # Remap having param keys to avoid collision with where params
            remapped: dict[str, Any] = {}
            for k, v in having_params.items():
                new_key = f"h{k[1:]}" if k.startswith("p") else k
                remapped[new_key] = v
            having_clause_remapped = having_clause
            for old_k, new_k in zip(having_params.keys(), remapped.keys()):
                having_clause_remapped = having_clause_remapped.replace(
                    f"{{{old_k}}}",
                    f"{{{new_k}}}",
                )
            query += f" HAVING {having_clause_remapped}"
            params.update(remapped)

        if spec.order_by:
            order_clause = build_order_by(spec.order_by)
            if order_clause:
                query += f" ORDER BY {order_clause}"

        if spec.page:
            query += f" {build_limit_offset(spec.page)}"

        try:
            result = self._client.query(query, parameters=params or None, settings=settings)
            rows = list(result.named_results())
            return AggregateResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    def count_by(
        self,
        group_by: GroupBySpec,
        filters: FilterRequest | None = None,
    ) -> list[dict[str, Any]]:
        """Count rows grouped by specified fields.

        Args:
            group_by: Fields to group by.
            filters: Optional filter conditions.

        Returns:
            List of dicts with group fields and a 'count' key.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        group_clause = build_group_by(group_by)
        group_fields = build_group_by(group_by)
        query = f"SELECT {group_fields}, COUNT(*) AS count FROM {table}"  # nosec B608
        if filters:
            where_clause, params = build_where(filters)
            query += f" WHERE {where_clause}"
        query += f" GROUP BY {group_clause}"
        return self._fetch_all(query, params or None)

    def sum_by(
        self,
        field: str,
        group_by: GroupBySpec,
        filters: FilterRequest | None = None,
    ) -> list[dict[str, Any]]:
        """Sum a numeric field grouped by specified fields.

        Args:
            field: Numeric column to sum.
            group_by: Fields to group by.
            filters: Optional filter conditions.

        Returns:
            List of dicts with group fields and a 'sum' key.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        field = validate_identifier(field)
        group_clause = build_group_by(group_by)
        group_fields = build_group_by(group_by)
        query = f"SELECT {group_fields}, SUM({field}) AS sum FROM {table}"  # nosec B608
        if filters:
            where_clause, params = build_where(filters)
            query += f" WHERE {where_clause}"
        query += f" GROUP BY {group_clause}"
        return self._fetch_all(query, params or None)

    def top_n(
        self,
        field: str,
        n: int,
        metric: MetricSpec,
        filters: FilterRequest | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch the top N values of a field by a given metric.

        Args:
            field: Field to group by for top-N.
            n: Number of top results to return.
            metric: Metric to sort by (descending).
            filters: Optional filter conditions.

        Returns:
            List of top-N row dicts.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        field = validate_identifier(field)
        metric_expr = f"{metric.function.value}({metric.field}) AS {metric.alias}"
        query = f"SELECT {field}, {metric_expr} FROM {table}"  # nosec B608
        if filters:
            where_clause, params = build_where(filters)
            query += f" WHERE {where_clause}"
        query += f" GROUP BY {field} ORDER BY {metric.alias} DESC LIMIT {n}"
        return self._fetch_all(query, params or None)

    def time_series(
        self,
        time_field: str,
        interval: str,
        metrics: list[MetricSpec],
        filters: FilterRequest | None = None,
    ) -> AggregateResult:
        """Execute a time-series aggregation query.

        Args:
            time_field: Name of the datetime column to bucket.
            interval: Time bucket interval (e.g., '1h', '1d').
            metrics: List of metrics to aggregate per bucket.
            filters: Optional filter conditions.

        Returns:
            AggregateResult with time-bucketed rows.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        bucket_expr = build_time_bucket(time_field, interval)
        metrics_expr = build_select_metrics(metrics)
        query = f"SELECT {bucket_expr} AS time_bucket, {metrics_expr} FROM {table}"  # nosec B608
        if filters:
            where_clause, params = build_where(filters)
            query += f" WHERE {where_clause}"
        query += " GROUP BY time_bucket ORDER BY time_bucket ASC"
        try:
            result = self._client.query(query, parameters=params or None)
            rows = list(result.named_results())
            return AggregateResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    def execute_analytical(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> AggregateResult:
        """Execute a raw analytical query and return an AggregateResult.

        Args:
            query: Raw SQL analytical query.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            AggregateResult with all returned rows.
        """
        try:
            result = self._client.query(query, parameters=params, settings=settings)
            rows = list(result.named_results())
            return AggregateResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc
