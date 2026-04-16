"""axiom.olap.clickhouse.repository.schema.async_ — Asynchronous ClickHouse schema manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from axiom.core.logger import get_logger
from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.exception import ClickHouseSchemaError
from axiom.olap.clickhouse.result.models import ColumnInfo, TableInfo
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

if TYPE_CHECKING:
    from typing_extensions import Self


class AsyncClickHouseSchemaManager:
    """Asynchronous manager for ClickHouse DDL and schema introspection."""

    def __init__(
        self,
        client: Any,
        database: str | None = None,
    ) -> None:
        """Initialize the async schema manager.

        Args:
            client: An asynchronous clickhouse_connect AsyncClient instance.
            database: Default database for schema operations.
        """
        self._client = client
        self._database = database
        self._logger = get_logger("axiom.olap.clickhouse.repository")

    def _resolve_database(self, database: str | None) -> str | None:
        """Resolve the effective database name."""
        return database if database is not None else self._database

    def _qualified(self, table: str, database: str | None) -> str:
        """Return a fully-qualified table name."""
        db = self._resolve_database(database)
        return f"{db}.{table}" if db else table

    async def table_exists(self, table: str, database: str | None = None) -> bool:
        """Check whether a table exists asynchronously.

        Args:
            table: Table name.
            database: Optional database override.

        Returns:
            True if the table exists.
        """
        db = self._resolve_database(database)
        try:
            if db:
                result = await self._client.query(
                    "SELECT COUNT(*) FROM system.tables WHERE database = {db:String} AND name = {tbl:String}",
                    parameters={"db": db, "tbl": table},
                )
            else:
                result = await self._client.query(
                    "SELECT COUNT(*) FROM system.tables WHERE database = currentDatabase() AND name = {tbl:String}",
                    parameters={"tbl": table},
                )
            rows = list(result.named_results())
            val = next(iter(rows[0].values()), 0) if rows else 0
            return int(val) > 0
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def describe_table(self, table: str, database: str | None = None) -> TableInfo:
        """Describe a table asynchronously.

        Args:
            table: Table name.
            database: Optional database override.

        Returns:
            TableInfo with engine, columns, and create DDL.
        """
        db = self._resolve_database(database) or "default"
        qualified = self._qualified(table, database)
        try:
            col_result = await self._client.query(f"DESCRIBE TABLE {qualified}")
            columns = [
                ColumnInfo(
                    name=row.get("name", ""),
                    type=row.get("type", ""),
                    default_kind=row.get("default_kind", ""),
                    default_expression=row.get("default_expression", ""),
                    comment=row.get("comment", ""),
                )
                for row in col_result.named_results()
            ]
            ddl = await self.get_create_table_ddl(table, database)
            engine_result = await self._client.query(
                "SELECT engine FROM system.tables WHERE database = {db:String} AND name = {tbl:String}",
                parameters={"db": db, "tbl": table},
            )
            engine_rows = list(engine_result.named_results())
            engine = engine_rows[0].get("engine", "") if engine_rows else ""
            return TableInfo(
                database=db,
                name=table,
                engine=engine,
                create_table_query=ddl,
                columns=columns,
            )
        except ClickHouseSchemaError:
            raise
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def get_create_table_ddl(self, table: str, database: str | None = None) -> str:
        """Return the CREATE TABLE DDL asynchronously.

        Args:
            table: Table name.
            database: Optional database override.

        Returns:
            CREATE TABLE statement string.
        """
        qualified = self._qualified(table, database)
        try:
            result = await self._client.command(f"SHOW CREATE TABLE {qualified}")
            return str(result)
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def create_table(self, ddl: str) -> None:
        """Execute a CREATE TABLE DDL statement asynchronously.

        Args:
            ddl: Full CREATE TABLE SQL statement.
        """
        try:
            await self._client.command(ddl)
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def drop_table(
        self,
        table: str,
        database: str | None = None,
        if_exists: bool = True,
    ) -> None:
        """Drop a table asynchronously.

        Args:
            table: Table name.
            database: Optional database override.
            if_exists: If True, use DROP TABLE IF EXISTS.
        """
        qualified = self._qualified(table, database)
        clause = "IF EXISTS " if if_exists else ""
        try:
            await self._client.command(f"DROP TABLE {clause}{qualified}")
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def truncate_table(self, table: str, database: str | None = None) -> None:
        """Truncate all rows from a table asynchronously.

        Args:
            table: Table name.
            database: Optional database override.
        """
        qualified = self._qualified(table, database)
        try:
            await self._client.command(f"TRUNCATE TABLE {qualified}")
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def optimize_table(
        self,
        table: str,
        database: str | None = None,
        final: bool = False,
        deduplicate: bool = False,
    ) -> None:
        """Run OPTIMIZE TABLE asynchronously.

        Args:
            table: Table name.
            database: Optional database override.
            final: If True, add FINAL keyword.
            deduplicate: If True, add DEDUPLICATE keyword.
        """
        qualified = self._qualified(table, database)
        suffix = ""
        if final:
            suffix += " FINAL"
        if deduplicate:
            suffix += " DEDUPLICATE"
        try:
            await self._client.command(f"OPTIMIZE TABLE {qualified}{suffix}")
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    async def list_tables(self, database: str | None = None) -> list[str]:
        """List all tables in a database asynchronously.

        Args:
            database: Optional database override.

        Returns:
            List of table name strings.
        """
        db = self._resolve_database(database)
        try:
            if db:
                result = await self._client.query(
                    "SELECT name FROM system.tables WHERE database = {db:String} ORDER BY name",
                    parameters={"db": db},
                )
            else:
                result = await self._client.query(
                    "SELECT name FROM system.tables WHERE database = currentDatabase() ORDER BY name",
                )
            return [row["name"] for row in result.named_results()]
        except Exception as exc:
            raise ClickHouseSchemaError(str(exc)) from exc

    @classmethod
    async def from_settings(
        cls,
        settings: ClickHouseSettings,
        database: str | None = None,
    ) -> Self:
        """Create an async schema manager from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.
            database: Optional default database.

        Returns:
            New AsyncClickHouseSchemaManager instance.
        """
        client = await ClickHouseClientFactory.create_async_client(settings)
        return cls(client=client, database=database)
