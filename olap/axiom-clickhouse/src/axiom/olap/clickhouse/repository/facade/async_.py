"""axiom.olap.clickhouse.repository.facade.async_ — Asynchronous unified ClickHouse repository facade."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.repository.agg.async_ import AsyncClickHouseAggRepository
from axiom.olap.clickhouse.repository.mutation.async_ import AsyncClickHouseMutationManager
from axiom.olap.clickhouse.repository.read.async_ import AsyncClickHouseReadRepository
from axiom.olap.clickhouse.repository.schema.async_ import AsyncClickHouseSchemaManager
from axiom.olap.clickhouse.repository.write.async_ import AsyncClickHouseWriteRepository
from axiom.olap.clickhouse.result.models import QueryResult
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

if TYPE_CHECKING:
    from typing_extensions import Self


class AsyncClickHouseRepository(
    AsyncClickHouseReadRepository,
    AsyncClickHouseWriteRepository,
    AsyncClickHouseAggRepository,
):
    """Unified asynchronous ClickHouse repository combining read, write, and aggregation."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
    ) -> None:
        """Initialize the async facade repository.

        Args:
            client: An asynchronous clickhouse_connect AsyncClient instance.
            table: Default table name.
            database: Optional database name.
        """
        super().__init__(client=client, table=table, database=database)
        self._schema_manager: AsyncClickHouseSchemaManager | None = None
        self._mutation_manager: AsyncClickHouseMutationManager | None = None

    @property
    def schema(self) -> AsyncClickHouseSchemaManager:
        """Lazy-loaded async schema manager.

        Returns:
            AsyncClickHouseSchemaManager instance sharing the same client.
        """
        if self._schema_manager is None:
            self._schema_manager = AsyncClickHouseSchemaManager(
                client=self._client,
                database=self._database,
            )
        return self._schema_manager

    @property
    def mutations(self) -> AsyncClickHouseMutationManager:
        """Lazy-loaded async mutation manager for tracking ALTER TABLE mutations.

        Returns:
            AsyncClickHouseMutationManager instance sharing the same client.
        """
        if self._mutation_manager is None:
            self._mutation_manager = AsyncClickHouseMutationManager(client=self._client)
        return self._mutation_manager

    async def raw(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Execute a raw SELECT query asynchronously.

        Args:
            query: Raw SQL SELECT query.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            QueryResult with all returned rows.
        """
        return await self.execute_select(query, params, settings)

    async def raw_command(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> int:
        """Execute a raw DDL/DML command asynchronously.

        Args:
            query: SQL command.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            Integer result (0 for most DDL/DML).
        """
        result = await self.execute(query, params, settings)
        try:
            return int(result) if result is not None else 0
        except (TypeError, ValueError):
            return 0

    @classmethod
    async def from_settings(
        cls,
        settings: ClickHouseSettings,
        table: str,
        database: str | None = None,
    ) -> Self:
        """Create an async facade repository from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            table: Default table name.
            database: Optional database name.

        Returns:
            New AsyncClickHouseRepository instance.
        """
        client = await ClickHouseClientFactory.create_async_client(settings)
        return cls(client=client, table=table, database=database)

    @classmethod
    def from_client(
        cls,
        client: Any,
        table: str,
        database: str | None = None,
    ) -> Self:
        """Create an async facade repository from an existing client.

        Args:
            client: An existing asynchronous clickhouse_connect AsyncClient.
            table: Default table name.
            database: Optional database name.

        Returns:
            New AsyncClickHouseRepository instance.
        """
        return cls(client=client, table=table, database=database)
