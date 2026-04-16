# ruff: noqa: S608
"""axiom.olap.clickhouse.repository.versioned.async_ — Async versioned/append-only ClickHouse repository."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from axiom.core.filter import FilterRequest
from axiom.olap.clickhouse.exception import ClickHouseConfigError, ClickHouseQueryError
from axiom.olap.clickhouse.query.builder import build_limit_offset, build_where, validate_identifier
from axiom.olap.clickhouse.query.specs import PageSpec
from axiom.olap.clickhouse.repository.base.async_ import AsyncClickHouseBaseRepository
from axiom.olap.clickhouse.result.models import BulkInsertResult, QueryResult, SingleInsertResult


class AsyncVersionedClickHouseRepository(AsyncClickHouseBaseRepository):
    """Async repository for versioned/append-only ClickHouse tables (e.g., ReplacingMergeTree).

    Each mutation is stored as a new row with an incremented version column.
    """

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
        *,
        version_column: str,
        is_deleted_column: str | None = None,
    ) -> None:
        """Initialize the async versioned repository.

        Args:
            client: An asynchronous clickhouse_connect AsyncClient instance.
            table: Table name.
            database: Optional database name.
            version_column: Name of the version column (int or datetime).
            is_deleted_column: Optional soft-delete flag column name.
        """
        super().__init__(client=client, table=table, database=database)
        validate_identifier(version_column)
        if is_deleted_column:
            validate_identifier(is_deleted_column)
        self._version_column = version_column
        self._is_deleted_column = is_deleted_column

    async def append_version(
        self,
        row: dict[str, Any],
        version: int | datetime,
    ) -> SingleInsertResult:
        """Append a new version of a row asynchronously.

        Args:
            row: Row data dict (should include ID fields).
            version: Version value to set on the version column.

        Returns:
            SingleInsertResult indicating success.
        """
        versioned_row = {**row, self._version_column: version}
        table = self._qualified_table()
        cols = list(versioned_row.keys())
        data = [list(versioned_row.values())]
        try:
            await self._client.insert(table, data, column_names=cols)
            return SingleInsertResult(success=True, row=versioned_row)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def append_many_versions(
        self,
        rows: list[dict[str, Any]],
    ) -> BulkInsertResult:
        """Append multiple versioned rows asynchronously.

        Args:
            rows: List of row dicts (each must include version_column).

        Returns:
            BulkInsertResult with inserted count.
        """
        if not rows:
            return BulkInsertResult(inserted=0, failed=0, errors=[])
        table = self._qualified_table()
        cols = list(rows[0].keys())
        data = [list(r.get(c) for c in cols) for r in rows]
        try:
            await self._client.insert(table, data, column_names=cols)
            return BulkInsertResult(inserted=len(rows), failed=0, errors=[])
        except Exception as exc:
            return BulkInsertResult(inserted=0, failed=len(rows), errors=[str(exc)])

    async def get_latest(
        self,
        filters: FilterRequest,
        id_column: str,
    ) -> dict[str, Any] | None:
        """Get the latest version of a row by filtering and ordering by version desc.

        Note: Reads latest version by ORDER BY version DESC LIMIT 1. For ReplacingMergeTree,
        this may not reflect uncommitted merges. Use get_latest_with_final for strong consistency
        at the cost of performance.

        Args:
            filters: Filter conditions to identify the row.
            id_column: ID column name (used for context; not applied to query directly).

        Returns:
            Latest row dict or None.
        """
        table = self._qualified_table()
        where_clause, params = build_where(filters)
        query = (
            f"SELECT * FROM {table} WHERE {where_clause} "  # nosec B608
            f"ORDER BY {self._version_column} DESC LIMIT 1"
        )
        return await self._fetch_one(query, params)

    async def get_latest_with_final(
        self,
        filters: FilterRequest | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Fetch rows using FINAL keyword (forces deduplication for ReplacingMergeTree).

        FINAL forces merge — use only for consistency-critical paths, never in hot query paths.

        Args:
            filters: Optional filter conditions.

        Returns:
            QueryResult with deduplicated rows.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        query = f"SELECT * FROM {table} FINAL"  # nosec B608
        if filters:
            where_clause, params = build_where(filters)
            query += f" WHERE {where_clause}"
        try:
            result = await self._client.query(query, parameters=params or None)
            rows = list(result.named_results())
            return QueryResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def soft_delete(
        self,
        id_column: str,
        id_value: Any,
        version: int | datetime,
    ) -> SingleInsertResult:
        """Append a soft-delete row (sets is_deleted_column to True) asynchronously.

        Args:
            id_column: Name of the ID column.
            id_value: Value of the ID to soft-delete.
            version: New version value for this deletion row.

        Returns:
            SingleInsertResult indicating success.

        Raises:
            ClickHouseConfigError: If is_deleted_column is not configured.
        """
        if not self._is_deleted_column:
            raise ClickHouseConfigError(
                "is_deleted_column not configured for soft delete",
            )
        row = {
            id_column: id_value,
            self._version_column: version,
            self._is_deleted_column: True,
        }
        table = self._qualified_table()
        cols = list(row.keys())
        data = [list(row.values())]
        try:
            await self._client.insert(table, data, column_names=cols)
            return SingleInsertResult(success=True, row=row)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def read_active(
        self,
        filters: FilterRequest | None = None,
        page: PageSpec | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Read active (non-deleted) rows asynchronously, excluding soft-deleted entries.

        Args:
            filters: Optional additional filter conditions.
            page: Optional pagination spec.

        Returns:
            QueryResult with active rows.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        conditions: list[str] = []

        if self._is_deleted_column:
            conditions.append(f"{self._is_deleted_column} = 0")

        if filters:
            where_clause, filter_params = build_where(filters)
            conditions.append(where_clause)
            params.update(filter_params)

        query = f"SELECT * FROM {table} FINAL"  # nosec B608
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        if page:
            query += f" {build_limit_offset(page)}"

        try:
            result = await self._client.query(query, parameters=params or None)
            rows = list(result.named_results())
            return QueryResult(rows=rows, row_count=len(rows), query_id=result.query_id)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def deduplicated_count(
        self,
        id_column: str,
        filters: FilterRequest | None = None,
    ) -> int:
        """Count distinct ID values asynchronously, excluding duplicates from versioning.

        Args:
            id_column: Name of the ID column.
            filters: Optional filter conditions.

        Returns:
            Count of distinct active IDs.
        """
        table = self._qualified_table()
        params: dict[str, Any] = {}
        conditions: list[str] = []

        if self._is_deleted_column:
            conditions.append(f"{self._is_deleted_column} = 0")

        if filters:
            where_clause, filter_params = build_where(filters)
            conditions.append(where_clause)
            params.update(filter_params)

        id_column = validate_identifier(id_column)
        query = f"SELECT COUNT(DISTINCT {id_column}) FROM {table} FINAL"  # nosec B608
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        result = await self._fetch_scalar(query, params or None)
        return int(result) if result is not None else 0
