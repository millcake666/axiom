"""axiom.olap.clickhouse.result.models — Typed result models for ClickHouse query responses."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class QueryResult(Generic[T]):
    """Result of a SELECT query returning typed rows."""

    rows: list[T]
    row_count: int
    query_id: str | None = None


@dataclass(frozen=True)
class PagedResult(Generic[T]):
    """Paginated query result with total count."""

    rows: list[T]
    total: int
    offset: int
    limit: int
    query_id: str | None = None

    @property
    def has_next(self) -> bool:
        """Return True if there are more rows beyond the current page."""
        return self.offset + self.limit < self.total


@dataclass(frozen=True)
class AggregateResult:
    """Result of an aggregation query."""

    rows: list[dict[str, Any]]
    row_count: int
    query_id: str | None = None


@dataclass(frozen=True)
class BulkInsertResult:
    """Result of a bulk insert operation."""

    inserted: int
    failed: int
    errors: list[str]

    @property
    def success(self) -> bool:
        """Return True if no rows failed to insert."""
        return self.failed == 0


@dataclass(frozen=True)
class SingleInsertResult:
    """Result of a single row insert operation."""

    success: bool
    row: dict[str, Any]


@dataclass(frozen=True)
class MutationStatus:
    """Status of a ClickHouse mutation (ALTER TABLE UPDATE/DELETE)."""

    mutation_id: str
    table: str
    command: str
    is_done: bool
    parts_to_do: int
    create_time: datetime | None
    error: str | None


@dataclass(frozen=True)
class ColumnInfo:
    """Metadata about a single ClickHouse table column."""

    name: str
    type: str
    default_kind: str = ""
    default_expression: str = ""
    comment: str = ""


@dataclass(frozen=True)
class TableInfo:
    """Metadata about a ClickHouse table."""

    database: str
    name: str
    engine: str
    create_table_query: str
    columns: list[ColumnInfo]


__all__ = [
    "AggregateResult",
    "BulkInsertResult",
    "ColumnInfo",
    "MutationStatus",
    "PagedResult",
    "QueryResult",
    "SingleInsertResult",
    "TableInfo",
]
