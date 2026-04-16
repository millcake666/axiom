"""axiom.olap.clickhouse.repository.facade.async_typed — Typed async unified ClickHouse repository facade."""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

from axiom.olap.clickhouse.repository.agg.async_ import AsyncClickHouseAggRepository
from axiom.olap.clickhouse.repository.mutation.async_ import AsyncClickHouseMutationManager
from axiom.olap.clickhouse.repository.read.async_typed import AsyncTypedClickHouseReadRepository
from axiom.olap.clickhouse.repository.schema.async_ import AsyncClickHouseSchemaManager
from axiom.olap.clickhouse.repository.write.async_ import AsyncClickHouseWriteRepository
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

RowType = TypeVar("RowType")


class AsyncTypedClickHouseRepository(
    AsyncTypedClickHouseReadRepository[RowType],
    AsyncClickHouseWriteRepository,
    AsyncClickHouseAggRepository,
    Generic[RowType],
):
    """Typed async unified facade: typed reads + untyped writes + aggregation."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
        *,
        row_factory: Callable[[dict[str, Any]], RowType],
    ) -> None:
        """Initialize the async typed facade repository.

        Args:
            client: An asynchronous clickhouse_connect AsyncClient instance.
            table: Default table name.
            database: Optional database name.
            row_factory: Callable that converts a row dict to RowType.
        """
        super().__init__(client=client, table=table, database=database, row_factory=row_factory)
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
        """Lazy-loaded async mutation manager.

        Returns:
            AsyncClickHouseMutationManager instance sharing the same client.
        """
        if self._mutation_manager is None:
            self._mutation_manager = AsyncClickHouseMutationManager(client=self._client)
        return self._mutation_manager

    @classmethod
    async def from_settings(  # type: ignore[override]
        cls,
        settings: ClickHouseSettings,
        table: str,
        database: str | None = None,
        *,
        row_factory: Callable[[dict[str, Any]], RowType],
    ) -> AsyncTypedClickHouseRepository[RowType]:
        """Create an async typed facade from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            table: Default table name.
            database: Optional database name.
            row_factory: Row mapping callable.

        Returns:
            New AsyncTypedClickHouseRepository instance.
        """
        from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory

        client = await ClickHouseClientFactory.create_async_client(settings)
        return cls(client=client, table=table, database=database, row_factory=row_factory)

    @classmethod
    def from_client(  # type: ignore[override]
        cls,
        client: Any,
        table: str,
        database: str | None = None,
        *,
        row_factory: Callable[[dict[str, Any]], RowType],
    ) -> AsyncTypedClickHouseRepository[RowType]:
        """Create an async typed facade from an existing client.

        Args:
            client: An existing asynchronous clickhouse_connect AsyncClient.
            table: Default table name.
            database: Optional database name.
            row_factory: Row mapping callable.

        Returns:
            New AsyncTypedClickHouseRepository instance.
        """
        return cls(client=client, table=table, database=database, row_factory=row_factory)
