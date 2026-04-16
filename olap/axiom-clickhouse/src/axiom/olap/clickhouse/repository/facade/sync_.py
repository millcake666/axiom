"""axiom.olap.clickhouse.repository.facade.sync_ — Synchronous unified ClickHouse repository facade."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.repository.agg.sync_ import ClickHouseAggRepository
from axiom.olap.clickhouse.repository.mutation.sync_ import ClickHouseMutationManager
from axiom.olap.clickhouse.repository.read.sync_ import ClickHouseReadRepository
from axiom.olap.clickhouse.repository.schema.sync_ import ClickHouseSchemaManager
from axiom.olap.clickhouse.repository.write.sync_ import ClickHouseWriteRepository
from axiom.olap.clickhouse.result.models import QueryResult
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

if TYPE_CHECKING:
    from typing_extensions import Self


class ClickHouseRepository(
    ClickHouseReadRepository,
    ClickHouseWriteRepository,
    ClickHouseAggRepository,
):
    """Unified synchronous ClickHouse repository combining read, write, and aggregation."""

    def __init__(
        self,
        client: Any,
        table: str,
        database: str | None = None,
    ) -> None:
        """Initialize the facade repository.

        Args:
            client: A synchronous clickhouse_connect client instance.
            table: Default table name.
            database: Optional database name.
        """
        super().__init__(client=client, table=table, database=database)
        self._schema_manager: ClickHouseSchemaManager | None = None
        self._mutation_manager: ClickHouseMutationManager | None = None

    @property
    def schema(self) -> ClickHouseSchemaManager:
        """Lazy-loaded schema manager for DDL operations.

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
        """Lazy-loaded mutation manager for tracking ALTER TABLE mutations.

        Returns:
            ClickHouseMutationManager instance sharing the same client.
        """
        if self._mutation_manager is None:
            self._mutation_manager = ClickHouseMutationManager(client=self._client)
        return self._mutation_manager

    def raw(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Execute a raw SELECT query and return a QueryResult.

        Args:
            query: Raw SQL SELECT query.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            QueryResult with all returned rows.
        """
        return self.execute_select(query, params, settings)

    def raw_command(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        settings: dict[str, Any] | None = None,
    ) -> int:
        """Execute a raw DDL/DML command and return result as int.

        Args:
            query: SQL command.
            params: Optional named parameters dict.
            settings: Optional ClickHouse query settings.

        Returns:
            Integer result (0 for most DDL/DML).
        """
        result = self.execute(query, params, settings)
        try:
            return int(result) if result is not None else 0
        except (TypeError, ValueError):
            return 0

    @classmethod
    def from_settings(
        cls,
        settings: ClickHouseSettings,
        table: str,
        database: str | None = None,
    ) -> Self:
        """Create a facade repository from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            table: Default table name.
            database: Optional database name.

        Returns:
            New ClickHouseRepository instance.
        """
        client = ClickHouseClientFactory.create_sync_client(settings)
        return cls(client=client, table=table, database=database)

    @classmethod
    def from_client(
        cls,
        client: Any,
        table: str,
        database: str | None = None,
    ) -> Self:
        """Create a facade repository from an existing client.

        Args:
            client: An existing synchronous clickhouse_connect client.
            table: Default table name.
            database: Optional database name.

        Returns:
            New ClickHouseRepository instance.
        """
        return cls(client=client, table=table, database=database)
