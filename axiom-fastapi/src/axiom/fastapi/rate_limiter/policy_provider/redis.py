"""axiom.fastapi.rate_limiter.policy_provider.redis — Redis-backed PolicyProvider with versioning."""

import json
from typing import Any

from axiom.core.logger import get_logger
from axiom.fastapi.rate_limiter.core.algorithm import Algorithm
from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import (
    GlobalPolicy,
    IPPolicy,
    PolicyGroup,
    RateLimitPolicy,
    RoutePolicy,
    UserPolicy,
)
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.policy_provider.exception import PolicyProviderError

__all__ = [
    "RedisPolicyProvider",
]

logger = get_logger("axiom.fastapi.rate_limiter.policy_provider.redis")

_POLICY_CLASS_MAP: dict[str, type[RateLimitPolicy]] = {
    "GlobalPolicy": GlobalPolicy,
    "IPPolicy": IPPolicy,
    "RateLimitPolicy": RateLimitPolicy,
    "RoutePolicy": RoutePolicy,
    "UserPolicy": UserPolicy,
}


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------


def _serialize_policy(policy: RateLimitPolicy) -> dict[str, Any]:
    return {
        "type": type(policy).__name__,
        "limit": policy.limit,
        "scope": policy.scope.value,
        "algorithm": policy.algorithm.value,
        "key_prefix": policy.key_prefix,
        "name": policy.name,
    }


def _serialize_group(group: PolicyGroup) -> dict[str, Any]:
    return {
        "type": "PolicyGroup",
        "mode": group.mode,
        "name": group.name,
        "policies": [_serialize_item(p) for p in group.policies],
    }


def _serialize_item(item: RateLimitPolicy | PolicyGroup) -> dict[str, Any]:
    if isinstance(item, PolicyGroup):
        return _serialize_group(item)
    return _serialize_policy(item)


def _deserialize_policy(data: dict[str, Any]) -> RateLimitPolicy:
    cls = _POLICY_CLASS_MAP.get(data.get("type", ""), RateLimitPolicy)
    return cls(
        limit=data["limit"],
        scope=RateLimitScope(data["scope"]),
        algorithm=Algorithm(data.get("algorithm", Algorithm.FIXED_WINDOW.value)),
        key_prefix=data.get("key_prefix", "rl"),
        name=data.get("name", ""),
    )


def _deserialize_group(data: dict[str, Any]) -> PolicyGroup:
    return PolicyGroup(
        mode=data.get("mode", "AND"),
        name=data.get("name", ""),
        policies=[_deserialize_item(p) for p in data.get("policies", [])],
    )


def _deserialize_item(data: dict[str, Any]) -> RateLimitPolicy | PolicyGroup:
    if data.get("type") == "PolicyGroup":
        return _deserialize_group(data)
    return _deserialize_policy(data)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class RedisPolicyProvider:
    """Stores and retrieves rate limit policies from Redis.

    Features:
    - **Versioning**: each ``set_policies()`` increments an integer ``version``
      field, enabling cache invalidation checks.
    - **Env-aware namespacing**: key is ``rl:{env}:policies``, preventing config
      bleed between environments (prod / staging / dev).

    Payload stored in Redis::

        {"version": 12, "policies": [...]}

    For production, wrap with ``CachedPolicyProvider`` to avoid Redis calls on
    every request::

        provider = CachedPolicyProvider(
            RedisPolicyProvider(redis_client, env="prod"),
            ttl=5.0,
        )
    """

    def __init__(self, redis_client: object, env: str = "default") -> None:
        """Initialize with an AsyncRedisClient and environment label.

        Args:
            redis_client: ``AsyncRedisClient`` instance from ``axiom-redis``.
            env: Deployment environment label (e.g. ``'prod'``, ``'staging'``).
                 Injected into the Redis key to prevent cross-environment bleed.
        """
        self._client = redis_client
        self._env = env

    def _key(self) -> str:
        """Return the namespaced Redis key for this environment."""
        return f"rl:{self._env}:policies"

    async def get_version(self) -> int | None:
        """Return the current config version stored in Redis, or ``None`` if absent.

        Useful for checking whether a ``CachedPolicyProvider`` needs invalidation.
        """
        try:
            raw = await self._client.get(self._key())  # type: ignore[attr-defined]
        except Exception:
            return None
        if raw is None:
            return None
        try:
            if isinstance(raw, bytes):
                raw = raw.decode()
            return json.loads(raw).get("version")
        except (json.JSONDecodeError, TypeError):
            return None

    async def get_policies(
        self,
        context: RequestContext,
    ) -> list[RateLimitPolicy | PolicyGroup]:
        """Load and deserialize policies from Redis.

        Args:
            context: Request context (not used for routing in this provider).

        Returns:
            Deserialized policy list. Empty list if no policies are configured.

        Raises:
            PolicyProviderError: On Redis connectivity errors or malformed payload.
        """
        try:
            raw = await self._client.get(self._key())  # type: ignore[attr-defined]
        except Exception as exc:
            raise PolicyProviderError(
                f"Failed to read policies from Redis (key={self._key()}): {exc}",
            ) from exc

        if raw is None:
            return []

        try:
            if isinstance(raw, bytes):
                raw = raw.decode()
            payload = json.loads(raw)
            return [_deserialize_item(item) for item in payload.get("policies", [])]
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise PolicyProviderError(
                f"Malformed policy payload in Redis (key={self._key()}): {exc}",
            ) from exc

    async def set_policies(
        self,
        policies: list[RateLimitPolicy | PolicyGroup],
    ) -> None:
        """Serialize and persist policies to Redis, incrementing the version counter.

        Args:
            policies: Policy list to persist.

        Raises:
            PolicyProviderError: On Redis write failure.
        """
        current_version = (await self.get_version()) or 0
        payload: dict[str, Any] = {
            "version": current_version + 1,
            "policies": [_serialize_item(p) for p in policies],
        }
        try:
            await self._client.set(self._key(), json.dumps(payload))  # type: ignore[attr-defined]
        except Exception as exc:
            raise PolicyProviderError(
                f"Failed to write policies to Redis (key={self._key()}): {exc}",
            ) from exc

        logger.info(
            "rate_limiter.policy_provider.redis.saved",
            env=self._env,
            version=payload["version"],
            policies_count=len(policies),
        )
