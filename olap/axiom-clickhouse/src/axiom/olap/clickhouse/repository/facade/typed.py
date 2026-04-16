"""axiom.olap.clickhouse.repository.facade.typed — Typed unified ClickHouse repository facade."""

from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

from axiom.olap.clickhouse.repository.agg.sync_ import ClickHouseAggRepository
from axiom.olap.clickhouse.repository.mutation.sync_ import ClickHouseMutationManager
from axiom.olap.clickhouse.repository.read.typed import TypedClickHouseReadRepository
from axiom.olap.clickhouse.repository.schema.sync_ import ClickHouseSchemaManager
from axiom.olap.clickhouse.repository.write.sync_ import ClickHouseWriteRepository
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

RowType = TypeVar("RowType")


class TypedClickHouseRepository(
    TypedClickHouseReadRepository[RowType],
    ClickHouseWriteRepository,
    ClickHouseAggRepository,
    Generic[RowType],
):
    """Typed unified facade: typed reads + untyped writes + aggregation."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
        *,
        row_factory: Callable[[dict[str, Any]], RowType],
    ) -> None:
        """Initialize the typed facade repository.

        Args:
            client: A synchronous clickhouse_connect client instance.
            table: Default table name.
            database: Optional database name.
            row_factory: Callable that converts a row dict to RowType.
        """
        super().__init__(client=client, table=table, database=database, row_factory=row_factory)
        self._schema_manager: ClickHouseSchemaManager | None = None
        self._mutation_manager: ClickHouseMutationManager | None = None

    @property
    def schema(self) -> ClickHouseSchemaManager:
        """Lazy-loaded schema manager.

        Returns:
            ClickHouseSchemaManager instance sharing the same client.
        """
        if self._schema_manager is None:
            self._schema_manager = ClickHouseSchemaManager(
                client=self._client,
                database=self._database,
            )
        return self._schema_manager

    @property
    def mutations(self) -> ClickHouseMutationManager:
        """Lazy-loaded mutation manager.

        Returns:
            ClickHouseMutationManager instance sharing the same client.
        """
        if self._mutation_manager is None:
            self._mutation_manager = ClickHouseMutationManager(client=self._client)
        return self._mutation_manager

    @classmethod
    def from_settings(  # type: ignore[override]
        cls,
        settings: ClickHouseSettings,
        table: str,
        database: str | None = None,
        *,
        row_factory: Callable[[dict[str, Any]], RowType],
    ) -> TypedClickHouseRepository[RowType]:
        """Create a typed facade from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            table: Default table name.
            database: Optional database name.
            row_factory: Row mapping callable.

        Returns:
            New TypedClickHouseRepository instance.
        """
        from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory

        client = ClickHouseClientFactory.create_sync_client(settings)
        return cls(client=client, table=table, database=database, row_factory=row_factory)
