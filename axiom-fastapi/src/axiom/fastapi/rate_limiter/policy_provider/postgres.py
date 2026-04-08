"""axiom.fastapi.rate_limiter.policy_provider.postgres — SQL-backed PolicyProvider."""

from typing import Any, Protocol, runtime_checkable

from axiom.core.logger import get_logger
from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.policy_provider.exception import PolicyProviderError

__all__ = [
    "PolicyRepository",
    "PostgresPolicyProvider",
]

logger = get_logger("axiom.fastapi.rate_limiter.policy_provider.postgres")


@runtime_checkable
class PolicyRepository(Protocol):
    """Minimal async repository interface for loading raw policy records.

    Implement this with an ``axiom-oltp`` SQLAlchemy repository or any async
    DB client. The provider only calls ``get_all_active()`` and expects a plain
    list of dicts — no ORM models leak into the rate limiter domain.

    Required dict fields per record:

    - ``limit`` (str): e.g. ``"100/minute"``
    - ``scope`` (str): value of ``RateLimitScope`` enum

    Optional fields:

    - ``algorithm`` (str): value of ``Algorithm`` enum, defaults to ``"fixed_window"``
    - ``key_prefix`` (str): defaults to ``"rl"``
    - ``name`` (str): human-readable policy name
    - ``policy_group`` (str): if set, policies sharing the same group name are
      collected into a single ``PolicyGroup(mode="AND")``
    """

    async def get_all_active(self) -> list[dict[str, Any]]:
        """Return all active rate limit policy records as plain dicts."""
        ...


def _build_policy(record: dict[str, Any]) -> RateLimitPolicy:
    """Construct a RateLimitPolicy from a raw DB record dict."""
    return RateLimitPolicy(
        limit=record["limit"],
        scope=RateLimitScope(record["scope"]),
        algorithm=Algorithm(record.get("algorithm", Algorithm.FIXED_WINDOW.value)),
        key_prefix=record.get("key_prefix", "rl"),
        name=record.get("name", ""),
    )


class PostgresPolicyProvider:
    """Loads rate limit policies from a SQL database via a ``PolicyRepository``.

    Not intended for the hot path. Always wrap with ``CachedPolicyProvider``::

        provider = CachedPolicyProvider(
            PostgresPolicyProvider(repo),
            ttl=30.0,
        )

    Records that share the same ``policy_group`` field value are automatically
    collected into a ``PolicyGroup(mode="AND")``.
    """

    def __init__(self, repository: PolicyRepository) -> None:
        """Initialize with a PolicyRepository implementation.

        Args:
            repository: Async repository with ``get_all_active()`` returning raw dicts.
        """
        self._repository = repository

    async def get_policies(
        self,
        context: RequestContext,
    ) -> list[RateLimitPolicy | PolicyGroup]:
        """Load and assemble policies from the database.

        Args:
            context: Request context (not used for filtering in this provider).

        Returns:
            Policy list. Records with a ``policy_group`` field are grouped into
            a ``PolicyGroup(mode="AND")`` keyed by that field value.

        Raises:
            PolicyProviderError: On repository errors.
        """
        try:
            records = await self._repository.get_all_active()
        except Exception as exc:
            raise PolicyProviderError(
                f"Failed to load policies from database: {exc}",
            ) from exc

        ungrouped: list[RateLimitPolicy | PolicyGroup] = []
        groups: dict[str, list[RateLimitPolicy]] = {}

        for record in records:
            group_name = record.get("policy_group")
            policy = _build_policy(record)
            if group_name:
                groups.setdefault(group_name, []).append(policy)
            else:
                ungrouped.append(policy)

        result: list[RateLimitPolicy | PolicyGroup] = list(ungrouped)
        for group_name, group_policies in groups.items():
            typed: list[RateLimitPolicy | PolicyGroup] = list(group_policies)
            result.append(PolicyGroup(policies=typed, mode="AND", name=group_name))

        logger.debug(
            "rate_limiter.policy_provider.postgres.loaded",
            records_count=len(records),
            groups_count=len(groups),
        )
        return result
