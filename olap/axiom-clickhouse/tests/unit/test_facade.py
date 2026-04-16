"""Unit tests for ClickHouseRepository and AsyncTypedClickHouseRepository facades."""

from __future__ import annotations

from typing import Any

from axiom.olap.clickhouse.repository.facade.async_ import AsyncClickHouseRepository
from axiom.olap.clickhouse.repository.facade.async_typed import AsyncTypedClickHouseRepository
from axiom.olap.clickhouse.repository.facade.sync_ import ClickHouseRepository
from axiom.olap.clickhouse.repository.facade.typed import TypedClickHouseRepository
from axiom.olap.clickhouse.repository.mutation.sync_ import ClickHouseMutationManager
from axiom.olap.clickhouse.repository.schema.sync_ import ClickHouseSchemaManager


class FakeQueryResult:
    def __init__(self, rows: list[dict[str, Any]], query_id: str = "q-1") -> None:
        self._rows = rows
        self.query_id = query_id

    def named_results(self) -> list[dict[str, Any]]:
        return self._rows


class FakeSyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        return FakeQueryResult(self._rows)

    def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        return None

    def insert(
        self,
        table: str,
        data: list,
        column_names: list[str] | None = None,
        settings: dict | None = None,
    ) -> None:
        pass


class FakeAsyncClient:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []

    async def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        return FakeQueryResult(self._rows)

    async def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        return None

    async def insert(
        self,
        table: str,
        data: list,
        column_names: list[str] | None = None,
        settings: dict | None = None,
    ) -> None:
        pass


class TestClickHouseRepositorySync:
    def _make(self, rows: list[dict] | None = None) -> tuple[ClickHouseRepository, FakeSyncClient]:
        client = FakeSyncClient(rows or [])
        repo = ClickHouseRepository(client=client, table="events", database="test_db")
        return repo, client

    def test_from_client(self) -> None:
        client = FakeSyncClient()
        repo = ClickHouseRepository.from_client(client, "events")
        assert repo._table == "events"
        assert repo._database is None

    def test_from_client_with_database(self) -> None:
        client = FakeSyncClient()
        repo = ClickHouseRepository.from_client(client, "events", "mydb")
        assert repo._database == "mydb"

    def test_raw_returns_query_result(self) -> None:
        repo, _ = self._make([{"id": 1}])
        result = repo.raw("SELECT 1")
        assert result.row_count == 1
        assert result.rows[0]["id"] == 1

    def test_raw_command_returns_int(self) -> None:
        repo, _ = self._make()
        result = repo.raw_command("CREATE TABLE t (id UInt64) ENGINE=Memory")
        assert isinstance(result, int)

    def test_schema_lazy_property(self) -> None:
        repo, _ = self._make()
        schema = repo.schema
        assert isinstance(schema, ClickHouseSchemaManager)
        # same instance on second access
        assert repo.schema is schema

    def test_mutations_lazy_property(self) -> None:
        repo, _ = self._make()
        mutations = repo.mutations
        assert isinstance(mutations, ClickHouseMutationManager)
        # same instance on second access
        assert repo.mutations is mutations

    def test_inherits_read_write_agg(self) -> None:
        from axiom.olap.clickhouse.repository.agg.sync_ import ClickHouseAggRepository
        from axiom.olap.clickhouse.repository.read.sync_ import ClickHouseReadRepository
        from axiom.olap.clickhouse.repository.write.sync_ import ClickHouseWriteRepository

        repo, _ = self._make()
        assert isinstance(repo, ClickHouseReadRepository)
        assert isinstance(repo, ClickHouseWriteRepository)
        assert isinstance(repo, ClickHouseAggRepository)


class TestTypedClickHouseRepository:
    def _make(self, rows: list[dict] | None = None) -> TypedClickHouseRepository[dict]:
        client = FakeSyncClient(rows or [])
        return TypedClickHouseRepository(
            client=client,
            table="events",
            row_factory=lambda r: r,
        )

    def test_row_factory_applied(self) -> None:
        repo = TypedClickHouseRepository(
            client=FakeSyncClient([{"x": 10}]),
            table="t",
            row_factory=lambda r: {"mapped": r["x"]},
        )
        result = repo.fetch_all()
        assert result.rows[0] == {"mapped": 10}

    def test_schema_lazy_property(self) -> None:
        repo = self._make()
        schema = repo.schema
        assert isinstance(schema, ClickHouseSchemaManager)
        assert repo.schema is schema

    def test_mutations_lazy_property(self) -> None:
        repo = self._make()
        mutations = repo.mutations
        assert isinstance(mutations, ClickHouseMutationManager)
        assert repo.mutations is mutations


class TestAsyncClickHouseRepository:
    def _make(
        self,
        rows: list[dict] | None = None,
    ) -> tuple[AsyncClickHouseRepository, FakeAsyncClient]:
        client = FakeAsyncClient(rows or [])
        repo = AsyncClickHouseRepository(client=client, table="events")
        return repo, client

    async def test_raw_returns_query_result(self) -> None:
        repo, _ = self._make([{"id": 1}])
        result = await repo.raw("SELECT 1")
        assert result.row_count == 1

    async def test_raw_command_returns_int(self) -> None:
        repo, _ = self._make()
        result = await repo.raw_command("SELECT 1")
        assert isinstance(result, int)

    def test_schema_lazy_property(self) -> None:
        from axiom.olap.clickhouse.repository.schema.async_ import AsyncClickHouseSchemaManager

        repo, _ = self._make()
        schema = repo.schema
        assert isinstance(schema, AsyncClickHouseSchemaManager)
        assert repo.schema is schema

    def test_mutations_lazy_property(self) -> None:
        from axiom.olap.clickhouse.repository.mutation.async_ import AsyncClickHouseMutationManager

        repo, _ = self._make()
        mutations = repo.mutations
        assert isinstance(mutations, AsyncClickHouseMutationManager)
        assert repo.mutations is mutations

    def test_from_client(self) -> None:
        client = FakeAsyncClient()
        repo = AsyncClickHouseRepository.from_client(client, "t", "db")
        assert repo._table == "t"
        assert repo._database == "db"


class TestAsyncTypedClickHouseRepository:
    def _make(self, rows: list[dict] | None = None) -> AsyncTypedClickHouseRepository[dict]:
        client = FakeAsyncClient(rows or [])
        return AsyncTypedClickHouseRepository(
            client=client,
            table="events",
            row_factory=lambda r: r,
        )

    async def test_row_factory_applied(self) -> None:
        repo = AsyncTypedClickHouseRepository(
            client=FakeAsyncClient([{"x": 10}]),
            table="t",
            row_factory=lambda r: {"mapped": r["x"]},
        )
        result = await repo.fetch_all()
        assert result.rows[0] == {"mapped": 10}

    def test_schema_lazy_property(self) -> None:
        from axiom.olap.clickhouse.repository.schema.async_ import AsyncClickHouseSchemaManager

        repo = self._make()
        schema = repo.schema
        assert isinstance(schema, AsyncClickHouseSchemaManager)
        assert repo.schema is schema

    def test_mutations_lazy_property(self) -> None:
        from axiom.olap.clickhouse.repository.mutation.async_ import AsyncClickHouseMutationManager

        repo = self._make()
        mutations = repo.mutations
        assert isinstance(mutations, AsyncClickHouseMutationManager)
        assert repo.mutations is mutations

    def test_from_client(self) -> None:
        client = FakeAsyncClient()
        repo = AsyncTypedClickHouseRepository.from_client(
            client,
            "t",
            "db",
            row_factory=lambda r: r,
        )
        assert repo._table == "t"
        assert repo._database == "db"


class TestPublicAPI:
    """Verify that all facade classes are exported from the top-level package."""

    def test_imports(self) -> None:
        from axiom.olap.clickhouse import (  # noqa: F401
            AsyncClickHouseRepository,
            AsyncTypedClickHouseRepository,
            ClickHouseRepository,
            TypedClickHouseRepository,
        )
