# ruff: noqa: S608
"""axiom.olap.clickhouse.repository.read.async_ — Asynchronous read-only ClickHouse repository."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from axiom.core.filter import FilterRequest
from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.query.builder import (
    build_limit_offset,
    build_order_by,
    build_select_columns,
    build_where,
    py_to_ch_type,
    validate_identifier,
)
from axiom.olap.clickhouse.query.specs import CHQuerySpec
from axiom.olap.clickhouse.repository.base.async_ import AsyncClickHouseBaseRepository
from axiom.olap.clickhouse.result.models import PagedResult, QueryResult


class AsyncClickHouseReadRepository(AsyncClickHouseBaseRepository):
    """Asynchronous read-only repository for ClickHouse tables."""

    async def fetch_all(
        self,
        spec: CHQuerySpec | None = None,
        settings: dict[str, Any] | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Fetch all rows matching the query spec asynchronously.

        Args:
            spec: Optional query specification.
            settings: Optional ClickHouse query settings.

        Returns:
            QueryResult containing all matching rows.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}

        if spec and spec.columns:
            select_clause = build_select_columns(spec.columns)
        else:
            select_clause = "*"

        query = f"SELECT {select_clause} FROM {table}"  # nosec B608

        if spec and spec.filters:
            where_clause, where_params = build_where(spec.filters)
            query += f" WHERE {where_clause}"
            params.update(where_params)

        if spec and spec.order_by:
            order_clause = build_order_by(spec.order_by)
            if order_clause:
                query += f" ORDER BY {order_clause}"

        if spec and spec.page:
            query += f" {build_limit_offset(spec.page)}"

        try:
            result = await self._client.query(query, parameters=params or None, settings=settings)
            rows = list(result.named_results())
            return QueryResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def fetch_one(
        self,
        filters: FilterRequest,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch the first row matching the given filters asynchronously.

        Args:
            filters: Filter conditions to apply.
            settings: Optional ClickHouse query settings.

        Returns:
            First matching row dict or None.
        """
        table = self._qualified_table()
        where_clause, params = build_where(filters)
        query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 1"  # nosec B608
        try:
            result = await self._client.query(
                query,
                parameters=params or None,
                settings=settings,
            )
            rows = list(result.named_results())
            return rows[0] if rows else None
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def fetch_scalar(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a query asynchronously and return the first scalar value.

        Args:
            query: SQL query returning a single scalar.
            params: Optional named parameters dict.

        Returns:
            Scalar value or None.
        """
        return await self._fetch_scalar(query, params)

    async def count(self, filters: FilterRequest | None = None) -> int:
        """Count rows matching optional filters asynchronously.

        Args:
            filters: Optional filter conditions.

        Returns:
            Row count as integer.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        query = f"SELECT COUNT(*) FROM {table}"  # nosec B608
        if filters:
            where_clause, params = build_where(filters)
            query += f" WHERE {where_clause}"
        result = await self._fetch_scalar(query, params or None)
        return int(result) if result is not None else 0

    async def exists(self, filters: FilterRequest) -> bool:
        """Check if any row matches the given filters asynchronously.

        Args:
            filters: Filter conditions to check.

        Returns:
            True if at least one row matches.
        """
        return await self.count(filters) > 0

    async def fetch_paged(
        self,
        spec: CHQuerySpec,
        settings: dict[str, Any] | None = None,
    ) -> PagedResult[dict[str, Any]]:
        """Fetch a page of results with total count asynchronously.

        Args:
            spec: Query specification including pagination.
            settings: Optional ClickHouse query settings.

        Returns:
            PagedResult with rows and total count.
        """
        total = await self.count(spec.filters)
        result = await self.fetch_all(spec, settings)
        offset = spec.page.offset if spec.page else 0
        limit = spec.page.limit if spec.page else len(result.rows)
        return PagedResult(
            rows=result.rows,
            total=total,
            offset=offset,
            limit=limit,
            query_id=result.query_id,
        )

    async def fetch_by_id(
        self,
        id_column: str,
        id_value: Any,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Fetch a single row by its ID column value asynchronously.

        Args:
            id_column: Name of the ID column.
            id_value: Value to match.
            settings: Optional ClickHouse query settings.

        Returns:
            Row dict or None if not found.
        """
        table = self._qualified_table()
        id_column = validate_identifier(id_column)
        ch_type = py_to_ch_type(id_value)
        query = f"SELECT * FROM {table} WHERE {id_column} = {{p0:{ch_type}}} LIMIT 1"  # nosec B608
        try:
            result = await self._client.query(
                query,
                parameters={"p0": id_value},
                settings=settings,
            )
            rows = list(result.named_results())
            return rows[0] if rows else None
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def get_by_id(
        self,
        id_column: str,
        id_value: Any,
    ) -> dict[str, Any] | None:
        """Alias for fetch_by_id without settings parameter.

        Args:
            id_column: Name of the ID column.
            id_value: Value to match.

        Returns:
            Row dict or None if not found.
        """
        return await self.fetch_by_id(id_column, id_value)

    async def stream(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        chunk_size: int = 1000,
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Stream query results in blocks asynchronously.

        Args:
            query: SELECT SQL query to stream.
            params: Optional named parameters dict.
            chunk_size: Unused — block size is determined by ClickHouse server.

        Yields:
            Lists of row dicts for each block returned by ClickHouse.
        """
        try:
            result = await self._client.query(query, parameters=params)
            rows = list(result.named_results())
            for i in range(0, len(rows), chunk_size):
                yield rows[i : i + chunk_size]
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def execute_select(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Execute a raw SELECT query asynchronously and return a QueryResult.

        Args:
            query: Raw SELECT SQL query.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            QueryResult with all returned rows.
        """
        try:
            result = await self._client.query(query, parameters=params, settings=settings)
            rows = list(result.named_results())
            return QueryResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc
