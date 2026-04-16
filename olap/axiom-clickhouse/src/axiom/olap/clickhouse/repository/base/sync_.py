"""axiom.olap.clickhouse.repository.base.sync_ — Synchronous ClickHouse base repository."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axiom.core.logger import get_logger
from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.query.builder import validate_identifier
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

if TYPE_CHECKING:
    from typing_extensions import Self


class ClickHouseBaseRepository:
    """Base synchronous repository providing low-level ClickHouse access."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
    ) -> None:
        """Initialize the base repository.

        Args:
            client: A synchronous clickhouse_connect client instance.
            table: Default table name for queries.
            database: Optional database name to qualify table references.
        """
        validate_identifier(table)
        if database:
            validate_identifier(database)
        self._client = client
        self._table = table
        self._database = database
        self._logger = get_logger("axiom.olap.clickhouse.repository")

    def _qualified_table(self) -> str:
        """Return the fully-qualified table name (database.table or just table).

        Returns:
            Qualified table name string.
        """
        if self._database:
            return f"{self._database}.{self._table}"
        return self._table

    def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a DDL/DML command (non-SELECT).

        Args:
            query: SQL command to execute.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            Command result from clickhouse_connect.

        Raises:
            ClickHouseQueryError: If the command fails.
        """
        try:
            return self._client.command(query, parameters=params, settings=settings)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    def _fetch_all(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return all rows as dicts.

        Args:
            query: SELECT SQL query.
            params: Optional named parameters dict.

        Returns:
            List of row dicts with column names as keys.

        Raises:
            ClickHouseQueryError: If the query fails.
        """
        try:
            result = self._client.query(query, parameters=params)
            return list(result.named_results())  # type: ignore[no-any-return]
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    def _fetch_one(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a SELECT query and return the first row or None.

        Args:
            query: SELECT SQL query.
            params: Optional named parameters dict.

        Returns:
            First row dict or None if no rows returned.

        Raises:
            ClickHouseQueryError: If the query fails.
        """
        rows = self._fetch_all(query, params)
        return rows[0] if rows else None

    def _fetch_scalar(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a SELECT query and return the first column of the first row.

        Args:
            query: SELECT SQL query returning a single scalar value.
            params: Optional named parameters dict.

        Returns:
            Scalar value or None if no rows returned.

        Raises:
            ClickHouseQueryError: If the query fails.
        """
        row = self._fetch_one(query, params)
        if row is None:
            return None
        return next(iter(row.values()), None)

    @classmethod
    def from_settings(
        cls,
        settings: ClickHouseSettings,
        table: str,
        database: str | None = None,
    ) -> Self:
        """Create a repository instance from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            table: Default table name.
            database: Optional database name.

        Returns:
            New repository instance connected to ClickHouse.
        """
        client = ClickHouseClientFactory.create_sync_client(settings)
        return cls(client=client, table=table, database=database)
