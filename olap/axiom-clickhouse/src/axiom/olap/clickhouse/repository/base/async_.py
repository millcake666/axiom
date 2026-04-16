"""axiom.olap.clickhouse.repository.base.async_ — Asynchronous ClickHouse base repository."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axiom.core.logger import get_logger
from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.query.builder import validate_identifier
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

if TYPE_CHECKING:
    from typing_extensions import Self


class AsyncClickHouseBaseRepository:
    """Base asynchronous repository providing low-level ClickHouse access."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
    ) -> None:
        """Initialize the async base repository.

        Args:
            client: An asynchronous clickhouse_connect AsyncClient instance.
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
        """Return the fully-qualified table name.

        Returns:
            Qualified table name string.
        """
        if self._database:
            return f"{self._database}.{self._table}"
        return self._table

    async def execute(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a DDL/DML command asynchronously.

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
            return await self._client.command(query, parameters=params, settings=settings)
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def _fetch_all(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query asynchronously and return all rows as dicts.

        Args:
            query: SELECT SQL query.
            params: Optional named parameters dict.

        Returns:
            List of row dicts with column names as keys.

        Raises:
            ClickHouseQueryError: If the query fails.
        """
        try:
            result = await self._client.query(query, parameters=params)
            return list(result.named_results())  # type: ignore[no-any-return]
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    async def _fetch_one(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a SELECT query asynchronously and return the first row or None.

        Args:
            query: SELECT SQL query.
            params: Optional named parameters dict.

        Returns:
            First row dict or None if no rows returned.

        Raises:
            ClickHouseQueryError: If the query fails.
        """
        rows = await self._fetch_all(query, params)
        return rows[0] if rows else None

    async def _fetch_scalar(
        self,
        query: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a SELECT query asynchronously and return the first scalar value.

        Args:
            query: SELECT SQL query returning a single scalar value.
            params: Optional named parameters dict.

        Returns:
            Scalar value or None if no rows returned.

        Raises:
            ClickHouseQueryError: If the query fails.
        """
        row = await self._fetch_one(query, params)
        if row is None:
            return None
        return next(iter(row.values()), None)

    @classmethod
    async def from_settings(
        cls,
        settings: ClickHouseSettings,
        table: str,
        database: str | None = None,
    ) -> Self:
        """Create an async repository instance from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            table: Default table name.
            database: Optional database name.

        Returns:
            New async repository instance connected to ClickHouse.
        """
        client = await ClickHouseClientFactory.create_async_client(settings)
        return cls(client=client, table=table, database=database)
