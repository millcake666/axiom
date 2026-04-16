"""axiom.olap.clickhouse.repository.write.async_ — Asynchronous write ClickHouse repository."""

from __future__ import annotations

from typing import Any

from axiom.core.filter import FilterRequest
from axiom.core.logger import get_logger
from axiom.olap.clickhouse.exception import ClickHouseBulkInsertError, ClickHouseQueryError
from axiom.olap.clickhouse.query.builder import build_where, py_to_ch_type
from axiom.olap.clickhouse.repository.base.async_ import AsyncClickHouseBaseRepository
from axiom.olap.clickhouse.result.models import BulkInsertResult, SingleInsertResult

_logger = get_logger("axiom.olap.clickhouse.repository.write")


def _rows_to_columns(
    rows: list[dict[str, Any]],
    column_names: list[str] | None,
) -> tuple[list[str], list[list[Any]]]:
    """Convert a list of dicts to column-ordered data for clickhouse-connect insert.

    Args:
        rows: List of row dicts.
        column_names: Explicit column order; derived from first row if None.

    Returns:
        Tuple of (column_names_list, data_rows) where data_rows is list of lists.
    """
    if not rows:
        return column_names or [], []
    cols = column_names if column_names is not None else list(rows[0].keys())
    data = [[row.get(c) for c in cols] for row in rows]
    return cols, data


class AsyncClickHouseWriteRepository(AsyncClickHouseBaseRepository):
    """Asynchronous write repository for ClickHouse tables."""

    async def insert(
        self,
        row: dict[str, Any],
        column_names: list[str] | None = None,
    ) -> SingleInsertResult:
        """Insert a single row into the table asynchronously.

        Args:
            row: Row data as a dict.
            column_names: Explicit column order; derived from row keys if None.

        Returns:
            SingleInsertResult indicating success.
        """
        table = self._qualified_table()
        cols, data = _rows_to_columns([row], column_names)
        try:
            await self._client.insert(table, data, column_names=cols)
            return SingleInsertResult(success=True, row=row)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def insert_many(
        self,
        rows: list[dict[str, Any]],
        column_names: list[str] | None = None,
    ) -> BulkInsertResult:
        """Insert multiple rows into the table asynchronously.

        Args:
            rows: List of row dicts.
            column_names: Explicit column order; derived from first row if None.

        Returns:
            BulkInsertResult with inserted count.
        """
        if not rows:
            return BulkInsertResult(inserted=0, failed=0, errors=[])
        table = self._qualified_table()
        cols, data = _rows_to_columns(rows, column_names)
        try:
            await self._client.insert(table, data, column_names=cols)
            return BulkInsertResult(inserted=len(rows), failed=0, errors=[])
        except Exception as exc:
            return BulkInsertResult(
                inserted=0,
                failed=len(rows),
                errors=[str(exc)],
            )

    async def insert_chunked(
        self,
        rows: list[dict[str, Any]],
        chunk_size: int = 10_000,
        column_names: list[str] | None = None,
    ) -> BulkInsertResult:
        """Insert rows in chunks asynchronously.

        Args:
            rows: List of row dicts.
            chunk_size: Number of rows per chunk.
            column_names: Explicit column order; derived from first row if None.

        Returns:
            BulkInsertResult aggregating all chunk results.
        """
        if not rows:
            return BulkInsertResult(inserted=0, failed=0, errors=[])
        table = self._qualified_table()
        cols = column_names if column_names is not None else list(rows[0].keys())
        total_inserted = 0
        failed_chunks: list[int] = []
        errors: list[str] = []

        for chunk_idx, start in enumerate(range(0, len(rows), chunk_size)):
            chunk = rows[start : start + chunk_size]
            _, data = _rows_to_columns(chunk, cols)
            try:
                await self._client.insert(table, data, column_names=cols)
                total_inserted += len(chunk)
            except Exception as exc:
                failed_chunks.append(chunk_idx)
                errors.append(str(exc))

        if failed_chunks:
            raise ClickHouseBulkInsertError(
                f"Failed to insert {len(failed_chunks)} chunk(s)",
                failed_chunks=failed_chunks,
            )
        return BulkInsertResult(inserted=total_inserted, failed=0, errors=[])

    async def execute_command(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> int:
        """Execute a raw DML command asynchronously.

        Args:
            query: SQL command.
            params: Optional named parameters dict.

        Returns:
            0 for async mutations.
        """
        result = await self.execute(query, params)
        try:
            return int(result) if result is not None else 0
        except (TypeError, ValueError):
            return 0

    async def update_by_filter(
        self,
        filters: FilterRequest,
        values: dict[str, Any],
    ) -> int:
        """Update rows matching filters asynchronously using ALTER TABLE UPDATE.

        .. warning::
            This operation creates an asynchronous mutation in ClickHouse.
            It is NOT a cheap row-level update. See MutationManager to track status.

        Args:
            filters: Filter conditions selecting rows to update.
            values: Dict of column → new_value assignments.

        Returns:
            0 (ClickHouse mutations are async; use MutationManager to track).
        """
        table = self._qualified_table()
        _logger.warning(
            "update_by_filter creates an async mutation — NOT a cheap row-level update",
            table=table,
        )
        where_clause, params = build_where(filters)
        set_parts: list[str] = []
        for i, (col, val) in enumerate(values.items()):
            key = f"upd_{i}"
            params[key] = val
            set_parts.append(f"{col} = {{{key}:{py_to_ch_type(val)}}}")
        set_clause = ", ".join(set_parts)
        query = f"ALTER TABLE {table} UPDATE {set_clause} WHERE {where_clause}"
        return await self.execute_command(query, params)

    async def delete_by_filter(self, filters: FilterRequest) -> int:
        """Delete rows matching filters asynchronously using ALTER TABLE DELETE.

        .. warning::
            This operation creates an asynchronous mutation in ClickHouse.
            It is NOT a cheap row-level update. See MutationManager to track status.

        Args:
            filters: Filter conditions selecting rows to delete.

        Returns:
            0 (ClickHouse mutations are async; use MutationManager to track).
        """
        table = self._qualified_table()
        _logger.warning(
            "delete_by_filter creates an async mutation — NOT a cheap row-level delete",
            table=table,
        )
        where_clause, params = build_where(filters)
        query = f"ALTER TABLE {table} DELETE WHERE {where_clause}"
        return await self.execute_command(query, params)

    async def upsert(
        self,
        rows: list[dict[str, Any]],
        column_names: list[str] | None = None,
    ) -> BulkInsertResult:
        """Upsert rows via INSERT with deduplication hint.

        ClickHouse does not support true upsert — this is an append with
        deduplication hint. ReplacingMergeTree handles deduplication
        asynchronously. For immediate consistency use FINAL queries.

        Args:
            rows: List of row dicts to upsert.
            column_names: Explicit column order; derived from first row if None.

        Returns:
            BulkInsertResult with inserted count.
        """
        return await self.insert_many(rows, column_names)
