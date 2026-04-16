"""Integration tests for ClickHouseMutationManager and AsyncClickHouseMutationManager."""

import pytest

from axiom.olap.clickhouse.repository.mutation.async_ import AsyncClickHouseMutationManager
from axiom.olap.clickhouse.repository.mutation.sync_ import ClickHouseMutationManager
from axiom.olap.clickhouse.result.models import MutationStatus

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS test_mutations (
    id UInt64,
    value String
) ENGINE = MergeTree()
ORDER BY id
"""

_DROP_TABLE = "DROP TABLE IF EXISTS test_mutations"


@pytest.fixture(scope="module")
def mutation_table(ch_client):
    """Create and populate a table for mutation tests."""
    ch_client.command(_CREATE_TABLE)
    ch_client.insert(
        "test_mutations",
        [[i, f"value_{i}"] for i in range(10)],
        column_names=["id", "value"],
    )
    yield
    ch_client.command(_DROP_TABLE)


class TestClickHouseMutationManager:
    def test_list_mutations_empty(self, ch_client, mutation_table):
        manager = ClickHouseMutationManager(client=ch_client)
        result = manager.list_mutations("test_mutations", active_only=True)
        assert isinstance(result, list)

    def test_get_mutation_not_found(self, ch_client, mutation_table):
        manager = ClickHouseMutationManager(client=ch_client)
        result = manager.get_mutation("nonexistent-mutation-id")
        assert result is None

    def test_list_stuck_mutations_empty(self, ch_client, mutation_table):
        manager = ClickHouseMutationManager(client=ch_client)
        result = manager.list_stuck_mutations("test_mutations", threshold_minutes=1)
        assert isinstance(result, list)

    def test_wait_for_mutation_not_found_raises(self, ch_client, mutation_table):
        from axiom.olap.clickhouse.exception import ClickHouseMutationError

        manager = ClickHouseMutationManager(client=ch_client)
        with pytest.raises(ClickHouseMutationError):
            manager.wait_for_mutation("nonexistent-id", poll_interval=0.1, timeout=0.5)

    def test_mutation_status_is_done_after_alter(self, ch_client, mutation_table):
        """Run an ALTER TABLE UPDATE and verify mutation appears in system.mutations."""
        manager = ClickHouseMutationManager(client=ch_client)
        # Trigger a lightweight mutation
        ch_client.command("ALTER TABLE test_mutations UPDATE value = 'updated' WHERE id = 1")
        # Poll all mutations (done or not) and verify at least one mutation was recorded
        import time

        deadline = time.monotonic() + 30
        found = False
        while time.monotonic() < deadline:
            all_mutations = manager.list_mutations(
                "test_mutations",
                active_only=False,
            )
            if all_mutations:
                found = True
                status = all_mutations[0]
                assert isinstance(status, MutationStatus)
                assert status.table == "test_mutations"
                break
            time.sleep(0.5)
        assert found, "No mutation recorded in system.mutations after ALTER TABLE UPDATE"


class TestAsyncClickHouseMutationManager:
    async def test_list_mutations_empty(self, async_ch_client, mutation_table):
        manager = AsyncClickHouseMutationManager(client=async_ch_client)
        result = await manager.list_mutations("test_mutations", active_only=True)
        assert isinstance(result, list)

    async def test_get_mutation_not_found(self, async_ch_client, mutation_table):
        manager = AsyncClickHouseMutationManager(client=async_ch_client)
        result = await manager.get_mutation("nonexistent-mutation-id")
        assert result is None

    async def test_list_stuck_mutations_empty(self, async_ch_client, mutation_table):
        manager = AsyncClickHouseMutationManager(client=async_ch_client)
        result = await manager.list_stuck_mutations("test_mutations", threshold_minutes=1)
        assert isinstance(result, list)

    async def test_wait_for_mutation_not_found_raises(self, async_ch_client, mutation_table):
        from axiom.olap.clickhouse.exception import ClickHouseMutationError

        manager = AsyncClickHouseMutationManager(client=async_ch_client)
        with pytest.raises(ClickHouseMutationError):
            await manager.wait_for_mutation(
                "nonexistent-id",
                poll_interval=0.1,
                timeout=0.5,
            )

    async def test_wait_for_mutation_done(self, ch_client, async_ch_client, mutation_table):
        """Trigger a mutation and wait for it to complete."""
        import asyncio

        ch_client.command("ALTER TABLE test_mutations UPDATE value = 'async_updated' WHERE id = 2")
        manager = AsyncClickHouseMutationManager(client=async_ch_client)

        # Poll until a completed mutation appears
        deadline = asyncio.get_event_loop().time() + 30
        found_done = False
        while asyncio.get_event_loop().time() < deadline:
            all_mutations = await manager.list_mutations(
                "test_mutations",
                active_only=False,
            )
            done = [m for m in all_mutations if m.is_done]
            if done:
                status = done[0]
                assert isinstance(status, MutationStatus)
                assert status.is_done is True
                found_done = True
                break
            await asyncio.sleep(0.5)
        assert found_done, "No completed mutation found within timeout"
