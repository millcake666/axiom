"""axiom.olap.clickhouse.repository.read.typed — Typed synchronous read repository."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Callable, Generic, TypeVar

from axiom.core.filter import FilterRequest
from axiom.olap.clickhouse.exception import ClickHouseRowMappingError
from axiom.olap.clickhouse.query.specs import CHQuerySpec
from axiom.olap.clickhouse.repository.read.sync_ import ClickHouseReadRepository
from axiom.olap.clickhouse.result.models import PagedResult, QueryResult

RowType = TypeVar("RowType")


def _map_row(
    factory: Callable[[dict[str, Any]], RowType],
    row: dict[str, Any],
    index: int,
) -> RowType:
    """Apply a row factory, wrapping any exception in ClickHouseRowMappingError.

    Args:
        factory: Callable that maps a dict to RowType.
        row: Row dict to map.
        index: Row index for error reporting.

    Returns:
        Mapped row of type RowType.

    Raises:
        ClickHouseRowMappingError: If the factory raises any exception.
    """
    try:
        return factory(row)
    except Exception as exc:
        raise ClickHouseRowMappingError(
            str(exc),
            row_index=index,
        ) from exc


class TypedClickHouseReadRepository(ClickHouseReadRepository, Generic[RowType]):
    """Synchronous typed read repository that maps rows via a factory callable."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
        *,
        row_factory: Callable[[dict[str, Any]], RowType],
    ) -> None:
        """Initialize the typed read repository.

        Args:
            client: A synchronous clickhouse_connect client instance.
            table: Default table name.
            database: Optional database name.
            row_factory: Callable that converts a row dict to RowType.
        """
        super().__init__(client=client, table=table, database=database)
        self._row_factory = row_factory

    def fetch_all(  # type: ignore[override]
        self,
        spec: CHQuerySpec | None = None,
        settings: dict[str, Any] | None = None,
    ) -> QueryResult[RowType]:
        """Fetch all rows, mapped through row_factory.

        Args:
            spec: Optional query specification.
            settings: Optional ClickHouse query settings.

        Returns:
            QueryResult with typed rows.
        """
        raw = super().fetch_all(spec, settings)
        rows = [_map_row(self._row_factory, r, i) for i, r in enumerate(raw.rows)]
        return QueryResult(rows=rows, row_count=raw.row_count, query_id=raw.query_id)

    def fetch_one(  # type: ignore[override]
        self,
        filters: FilterRequest,
        settings: dict[str, Any] | None = None,
    ) -> RowType | None:
        """Fetch the first row matching filters, mapped through row_factory.

        Args:
            filters: Filter conditions to apply.
            settings: Optional ClickHouse query settings.

        Returns:
            Mapped row or None.
        """
        raw = super().fetch_one(filters, settings)
        if raw is None:
            return None
        return _map_row(self._row_factory, raw, 0)

    def fetch_paged(  # type: ignore[override]
        self,
        spec: CHQuerySpec,
        settings: dict[str, Any] | None = None,
    ) -> PagedResult[RowType]:
        """Fetch a page of results, mapped through row_factory.

        Args:
            spec: Query specification including pagination.
            settings: Optional ClickHouse query settings.

        Returns:
            PagedResult with typed rows.
        """
        # Call the untyped parent fetch_all directly to avoid double-mapping:
        # super().fetch_paged() calls self.fetch_all() which is already overridden to return RowType.
        total = self.count(spec.filters)
        raw_result = ClickHouseReadRepository.fetch_all(self, spec, settings)
        rows = [_map_row(self._row_factory, r, i) for i, r in enumerate(raw_result.rows)]
        offset = spec.page.offset if spec.page else 0
        limit = spec.page.limit if spec.page else len(rows)
        return PagedResult(
            rows=rows,
            total=total,
            offset=offset,
            limit=limit,
            query_id=raw_result.query_id,
        )

    def fetch_by_id(  # type: ignore[override]
        self,
        id_column: str,
        id_value: Any,
        settings: dict[str, Any] | None = None,
    ) -> RowType | None:
        """Fetch a row by ID, mapped through row_factory.

        Args:
            id_column: Name of the ID column.
            id_value: Value to match.
            settings: Optional ClickHouse query settings.

        Returns:
            Mapped row or None.
        """
        raw = super().fetch_by_id(id_column, id_value, settings)
        if raw is None:
            return None
        return _map_row(self._row_factory, raw, 0)

    def get_by_id(  # type: ignore[override]
        self,
        id_column: str,
        id_value: Any,
    ) -> RowType | None:
        """Alias for fetch_by_id, mapped through row_factory.

        Args:
            id_column: Name of the ID column.
            id_value: Value to match.

        Returns:
            Mapped row or None.
        """
        return self.fetch_by_id(id_column, id_value)

    def execute_select(  # type: ignore[override]
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> QueryResult[RowType]:
        """Execute a raw SELECT query and return typed rows.

        Args:
            query: Raw SELECT SQL query.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            QueryResult with typed rows.
        """
        raw = super().execute_select(query, params, settings)
        rows = [_map_row(self._row_factory, r, i) for i, r in enumerate(raw.rows)]
        return QueryResult(rows=rows, row_count=raw.row_count, query_id=raw.query_id)

    def stream(  # type: ignore[override]
        self,
        query: str,
        params: dict[str, Any] | None = None,
        chunk_size: int = 1000,
    ) -> Iterator[list[RowType]]:
        """Stream typed rows in blocks.

        Args:
            query: SELECT SQL query to stream.
            params: Optional named parameters dict.
            chunk_size: Block size hint (server-determined).

        Yields:
            Lists of typed rows for each block.
        """
        for block in super().stream(query, params, chunk_size):
            yield [_map_row(self._row_factory, r, i) for i, r in enumerate(block)]
