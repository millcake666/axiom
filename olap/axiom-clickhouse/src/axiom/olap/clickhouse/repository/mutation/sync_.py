"""axiom.olap.clickhouse.repository.mutation.sync_ — Synchronous ClickHouse mutation manager."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from axiom.core.logger import get_logger
from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.exception import ClickHouseMutationError, ClickHouseQueryError
from axiom.olap.clickhouse.result.models import MutationStatus
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

if TYPE_CHECKING:
    from typing_extensions import Self

_MUTATIONS_QUERY_DB = """
SELECT
    mutation_id,
    table,
    command,
    is_done,
    parts_to_do,
    create_time,
    latest_fail_reason
FROM system.mutations
WHERE database = {db:String} AND table = {tbl:String}
"""

_MUTATIONS_QUERY_CURRENT_DB = """
SELECT
    mutation_id,
    table,
    command,
    is_done,
    parts_to_do,
    create_time,
    latest_fail_reason
FROM system.mutations
WHERE database = currentDatabase() AND table = {tbl:String}
"""

_ACTIVE_FILTER = " AND is_done = 0"


def _row_to_mutation_status(row: dict[str, Any]) -> MutationStatus:
    """Convert a system.mutations row dict to MutationStatus.

    Args:
        row: Row dict from system.mutations query.

    Returns:
        MutationStatus dataclass instance.
    """
    create_time = row.get("create_time")
    if isinstance(create_time, str):
        try:
            create_time = datetime.fromisoformat(create_time)
        except ValueError:
            create_time = None
    return MutationStatus(
        mutation_id=str(row.get("mutation_id", "")),
        table=str(row.get("table", "")),
        command=str(row.get("command", "")),
        is_done=bool(row.get("is_done", False)),
        parts_to_do=int(row.get("parts_to_do", 0)),
        create_time=create_time,
        error=row.get("latest_fail_reason") or None,
    )


class ClickHouseMutationManager:
    """Synchronous manager for monitoring and controlling ClickHouse mutations."""

    def __init__(self, client: Any) -> None:
        """Initialize the mutation manager.

        Args:
            client: A synchronous clickhouse_connect client instance.
        """
        self._client = client
        self._logger = get_logger("axiom.olap.clickhouse.repository")

    def list_mutations(
        self,
        table: str,
        database: str | None = None,
        active_only: bool = True,
    ) -> list[MutationStatus]:
        """List mutations for a table.

        Args:
            table: Table name.
            database: Optional database name.
            active_only: If True, return only pending (not done) mutations.

        Returns:
            List of MutationStatus objects.
        """
        db = database
        if db:
            query = _MUTATIONS_QUERY_DB + (_ACTIVE_FILTER if active_only else "")
            params: dict[str, str] = {"db": db, "tbl": table}
        else:
            query = _MUTATIONS_QUERY_CURRENT_DB + (_ACTIVE_FILTER if active_only else "")
            params = {"tbl": table}
        try:
            result = self._client.query(query, parameters=params)
            return [_row_to_mutation_status(row) for row in result.named_results()]
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    def get_mutation(self, mutation_id: str) -> MutationStatus | None:
        """Fetch a single mutation by its ID.

        Args:
            mutation_id: Mutation identifier.

        Returns:
            MutationStatus or None if not found.
        """
        query = """
SELECT mutation_id, table, command, is_done, parts_to_do, create_time, latest_fail_reason
FROM system.mutations
WHERE mutation_id = {mid:String}
"""
        try:
            result = self._client.query(query, parameters={"mid": mutation_id})
            rows = list(result.named_results())
            return _row_to_mutation_status(rows[0]) if rows else None
        except Exception as exc:
            raise ClickHouseQueryError(str(exc)) from exc

    def wait_for_mutation(
        self,
        mutation_id: str,
        poll_interval: float = 2.0,
        timeout: float = 60.0,
    ) -> MutationStatus:
        """Poll until a mutation completes or timeout is reached.

        Args:
            mutation_id: Mutation identifier to wait for.
            poll_interval: Seconds between polls.
            timeout: Maximum seconds to wait.

        Returns:
            Final MutationStatus when done.

        Raises:
            ClickHouseMutationError: If timeout is reached or mutation has an error.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = self.get_mutation(mutation_id)
            if status is None:
                raise ClickHouseMutationError(
                    f"Mutation {mutation_id!r} not found",
                    mutation_id=mutation_id,
                )
            if status.is_done:
                return status
            if status.error:
                raise ClickHouseMutationError(
                    f"Mutation {mutation_id!r} failed: {status.error}",
                    mutation_id=mutation_id,
                )
            time.sleep(poll_interval)
        raise ClickHouseMutationError(
            f"Mutation {mutation_id!r} timed out after {timeout}s",
            mutation_id=mutation_id,
        )

    def kill_mutation(self, mutation_id: str) -> None:
        """Kill a running mutation.

        Args:
            mutation_id: Mutation identifier to kill.
        """
        try:
            self._client.command(
                "KILL MUTATION WHERE mutation_id = {mid:String}",
                parameters={"mid": mutation_id},
            )
        except Exception as exc:
            raise ClickHouseMutationError(str(exc), mutation_id=mutation_id) from exc

    def list_stuck_mutations(
        self,
        table: str,
        database: str | None = None,
        threshold_minutes: int = 30,
    ) -> list[MutationStatus]:
        """List mutations that have been pending longer than the threshold.

        Args:
            table: Table name.
            database: Optional database name.
            threshold_minutes: Minutes threshold to consider a mutation stuck.

        Returns:
            List of stuck MutationStatus objects.
        """
        all_active = self.list_mutations(table, database, active_only=True)
        now = datetime.now(tz=timezone.utc)
        stuck = []
        for m in all_active:
            if m.create_time is None:
                continue
            ct = m.create_time
            if ct.tzinfo is None:
                ct = ct.replace(tzinfo=timezone.utc)
            elapsed = (now - ct).total_seconds() / 60
            if elapsed >= threshold_minutes:
                stuck.append(m)
        return stuck

    @classmethod
    def from_settings(cls, settings: ClickHouseSettings) -> Self:
        """Create a mutation manager from ClickHouseSettings.

        Args:
            settings: ClickHouse connection settings.

        Returns:
            New ClickHouseMutationManager instance.
        """
        client = ClickHouseClientFactory.create_sync_client(settings)
        return cls(client=client)
