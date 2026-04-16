"""axiom.olap.clickhouse.exception — Exceptions for the axiom.olap.clickhouse package."""

from __future__ import annotations

from axiom.core.exceptions import BaseError


class ClickHouseError(BaseError):
    """Base exception for all ClickHouse-related errors."""

    code = "clickhouse_error"
    status_code = 500


class ClickHouseConnectionError(ClickHouseError):
    """Raised when a connection to ClickHouse cannot be established."""

    code = "clickhouse_connection_error"
    status_code = 503


class ClickHouseQueryError(ClickHouseError):
    """Raised when a ClickHouse query fails."""

    code = "clickhouse_query_error"
    status_code = 500


class ClickHouseRowMappingError(ClickHouseError):
    """Raised when a row cannot be mapped to a target type."""

    code = "clickhouse_row_mapping_error"
    status_code = 500

    def __init__(
        self,
        message: str,
        row_index: int = 0,
        field: str | None = None,
    ) -> None:
        """Initialize ClickHouseRowMappingError.

        Args:
            message: Human-readable error description.
            row_index: Index of the row that failed mapping.
            field: Name of the field that caused the error.
        """
        super().__init__(message, details={"row_index": row_index, "field": field})
        self.row_index = row_index
        self.field = field


class ClickHouseBulkInsertError(ClickHouseError):
    """Raised when a bulk insert operation partially or fully fails."""

    code = "clickhouse_bulk_insert_error"
    status_code = 500

    def __init__(
        self,
        message: str,
        failed_chunks: list[int] | None = None,
    ) -> None:
        """Initialize ClickHouseBulkInsertError.

        Args:
            message: Human-readable error description.
            failed_chunks: List of chunk indices that failed.
        """
        super().__init__(message, details={"failed_chunks": failed_chunks or []})
        self.failed_chunks = failed_chunks or []


class ClickHouseMutationError(ClickHouseError):
    """Raised when a ClickHouse mutation (ALTER TABLE UPDATE/DELETE) fails."""

    code = "clickhouse_mutation_error"
    status_code = 500

    def __init__(
        self,
        message: str,
        mutation_id: str = "",
    ) -> None:
        """Initialize ClickHouseMutationError.

        Args:
            message: Human-readable error description.
            mutation_id: Identifier of the failed mutation.
        """
        super().__init__(message, details={"mutation_id": mutation_id})
        self.mutation_id = mutation_id


class ClickHouseSchemaError(ClickHouseError):
    """Raised when a schema operation fails."""

    code = "clickhouse_schema_error"
    status_code = 500


class ClickHouseConfigError(ClickHouseError):
    """Raised when ClickHouse configuration is invalid."""

    code = "clickhouse_config_error"
    status_code = 500


class ClickHouseImportError(ClickHouseError):
    """Raised when a required ClickHouse import cannot be loaded."""

    code = "clickhouse_import_error"
    status_code = 500


__all__ = [
    "ClickHouseError",
    "ClickHouseConnectionError",
    "ClickHouseQueryError",
    "ClickHouseRowMappingError",
    "ClickHouseBulkInsertError",
    "ClickHouseMutationError",
    "ClickHouseSchemaError",
    "ClickHouseConfigError",
    "ClickHouseImportError",
]
