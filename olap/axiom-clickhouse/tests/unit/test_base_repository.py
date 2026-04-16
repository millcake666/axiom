"""Unit tests for ClickHouseBaseRepository using a fake synchronous client."""

from __future__ import annotations

from typing import Any

import pytest

from axiom.olap.clickhouse.exception import ClickHouseQueryError
from axiom.olap.clickhouse.repository.base.sync_ import ClickHouseBaseRepository


class FakeQueryResult:
    """Fake query result returned by the fake sync client."""

    def __init__(self, rows: list[dict[str, Any]], query_id: str = "fake-id") -> None:
        self._rows = rows
        self.query_id = query_id

    def named_results(self) -> list[dict[str, Any]]:
        return self._rows


class FakeSyncClient:
    """Test double for a synchronous clickhouse_connect client."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.last_query: str | None = None
        self.last_params: dict[str, Any] | None = None
        self.raise_on_query: Exception | None = None
        self.raise_on_command: Exception | None = None

    def query(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> FakeQueryResult:
        if self.raise_on_query:
            raise self.raise_on_query
        self.last_query = query
        self.last_params = parameters
        return FakeQueryResult(self._rows)

    def command(
        self,
        query: str,
        parameters: dict | None = None,
        settings: dict | None = None,
    ) -> Any:
        if self.raise_on_command:
            raise self.raise_on_command
        self.last_query = query
        self.last_params = parameters
        return None


class TestClickHouseBaseRepository:
    def _make_repo(
        self,
        rows: list[dict] | None = None,
    ) -> tuple[ClickHouseBaseRepository, FakeSyncClient]:
        client = FakeSyncClient(rows or [])
        repo = ClickHouseBaseRepository(client=client, table="events", database="default")
        return repo, client

    def test_qualified_table_with_database(self):
        repo, _ = self._make_repo()
        assert repo._qualified_table() == "default.events"

    def test_qualified_table_without_database(self):
        client = FakeSyncClient()
        repo = ClickHouseBaseRepository(client=client, table="events")
        assert repo._qualified_table() == "events"

    def test_fetch_all_returns_rows(self):
        rows = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
        repo, _ = self._make_repo(rows)
        result = repo._fetch_all("SELECT * FROM events")
        assert result == rows

    def test_fetch_all_raises_on_error(self):
        repo, client = self._make_repo()
        client.raise_on_query = RuntimeError("connection refused")
        with pytest.raises(ClickHouseQueryError, match="connection refused"):
            repo._fetch_all("SELECT 1")

    def test_fetch_one_returns_first_row(self):
        rows = [{"id": 1}, {"id": 2}]
        repo, _ = self._make_repo(rows)
        result = repo._fetch_one("SELECT * FROM events LIMIT 1")
        assert result == {"id": 1}

    def test_fetch_one_returns_none_when_empty(self):
        repo, _ = self._make_repo([])
        result = repo._fetch_one("SELECT * FROM events LIMIT 1")
        assert result is None

    def test_fetch_scalar_returns_value(self):
        repo, _ = self._make_repo([{"count": 42}])
        result = repo._fetch_scalar("SELECT COUNT(*) FROM events")
        assert result == 42

    def test_fetch_scalar_returns_none_when_empty(self):
        repo, _ = self._make_repo([])
        result = repo._fetch_scalar("SELECT COUNT(*) FROM events")
        assert result is None

    def test_execute_calls_command(self):
        repo, client = self._make_repo()
        repo.execute("CREATE TABLE foo (id UInt64) ENGINE = MergeTree ORDER BY id")
        assert client.last_query is not None
        assert "CREATE TABLE" in client.last_query

    def test_execute_raises_on_error(self):
        repo, client = self._make_repo()
        client.raise_on_command = RuntimeError("command failed")
        with pytest.raises(ClickHouseQueryError, match="command failed"):
            repo.execute("DROP TABLE foo")

    def test_execute_passes_params(self):
        repo, client = self._make_repo()
        repo.execute("ALTER TABLE foo UPDATE x = {v}", params={"v": 42})
        assert client.last_params == {"v": 42}
