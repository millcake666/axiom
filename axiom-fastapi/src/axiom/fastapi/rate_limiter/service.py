"""axiom.fastapi.rate_limiter.service — RateLimiterService orchestration and lifespan helpers."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from starlette.requests import Request

from axiom.core.logger import get_logger
from axiom.fastapi.rate_limiter.backend.base import RateLimitBackend
from axiom.fastapi.rate_limiter.backend.memory import InMemoryRateLimitBackend
from axiom.fastapi.rate_limiter.config import RateLimitConfig
from axiom.fastapi.rate_limiter.core.algorithm import FailureStrategy
from axiom.fastapi.rate_limiter.core.context import RequestContext
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy
from axiom.fastapi.rate_limiter.core.result import RateLimitResult
from axiom.fastapi.rate_limiter.exception import RateLimitBackendError
from axiom.fastapi.rate_limiter.key_builder.base import KeyBuilder
from axiom.fastapi.rate_limiter.key_builder.ip import IPKeyBuilder
from axiom.fastapi.rate_limiter.policy_provider.base import PolicyProvider
from axiom.fastapi.rate_limiter.policy_provider.static import StaticPolicyProvider

__all__ = [
    "RateLimiterService",
    "rate_limiter_lifespan",
    "setup_rate_limiter",
]

logger = get_logger("axiom.fastapi.rate_limiter.service")


def _build_context(request: Request) -> RequestContext:
    """Extract a RequestContext from a Starlette Request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"

    return RequestContext(
        path=str(request.url.path),
        method=str(request.method),
        client_ip=client_ip,
        user_id=getattr(request.state, "user_id", None) or None,
        tenant_id=getattr(request.state, "tenant_id", None) or None,
    )


class RateLimiterService:
    """Orchestrates rate limit checks across policies from a PolicyProvider.

    Accepts either a static ``policies`` list (backward-compatible shorthand) or
    a ``PolicyProvider`` instance. When a list is given, it is wrapped internally
    in a ``StaticPolicyProvider``.

    PolicyGroup evaluation:
    - ``AND`` (default): all member policies must pass; short-circuits on first block.
    - ``OR``: at least one member policy must pass; evaluates all, aggregates results.
    """

    def __init__(
        self,
        backend: RateLimitBackend,
        key_builder: KeyBuilder,
        failure_strategy: FailureStrategy = FailureStrategy.FAIL_OPEN,
        policies: list[RateLimitPolicy | PolicyGroup] | None = None,
        policy_provider: PolicyProvider | None = None,
        *,
        enabled: bool = True,
    ) -> None:
        """Initialize service with backend, key builder, and policy source.

        Provide exactly one of ``policies`` or ``policy_provider``.
        If neither is provided, the service starts with an empty policy list
        (all requests allowed).

        Args:
            backend: Storage backend for rate limit counters.
            key_builder: Strategy to extract a storage key from a request.
            failure_strategy: Behavior when the backend is unavailable.
            policies: Static policy list (backward-compatible shorthand).
            policy_provider: Dynamic policy source. Takes precedence over ``policies``
                when both are supplied.
            enabled: If ``False``, ``check_request()`` always returns an empty list
                (no rate limiting). Useful for toggling via ``RATE_LIMIT_ENABLED``.
        """
        self._backend = backend
        self._key_builder = key_builder
        self._failure_strategy = failure_strategy
        self._enabled = enabled

        if policy_provider is not None:
            self._provider: PolicyProvider = policy_provider
        elif policies is not None:
            self._provider = StaticPolicyProvider(policies)
        else:
            self._provider = StaticPolicyProvider([])

    async def check_request(self, request: Request) -> list[RateLimitResult]:
        """Evaluate all policies against the request.

        Fetches the current policy list from the provider, then evaluates each item
        in order. PolicyGroups are evaluated recursively according to their ``mode``.

        Args:
            request: Incoming HTTP request.

        Returns:
            List of ``RateLimitResult`` — one per evaluated policy leaf.
            Empty list if the service is disabled or no policies are configured.
        """
        if not self._enabled:
            return []

        context = _build_context(request)

        try:
            items = await self._provider.get_policies(context)
        except Exception as exc:
            if self._failure_strategy == FailureStrategy.FAIL_CLOSED:
                raise RateLimitBackendError(
                    f"Policy provider failed: {exc}",
                ) from exc
            logger.warning("rate_limiter.provider_error", error=str(exc))
            return []

        results: list[RateLimitResult] = []
        await self._evaluate_items(request, items, results)
        return results

    async def _evaluate_items(
        self,
        request: Request,
        items: list[RateLimitPolicy | PolicyGroup],
        results: list[RateLimitResult],
    ) -> bool:
        """Evaluate a list of items sequentially. Returns True if any item blocks."""
        for item in items:
            blocked = await self._evaluate_item(request, item, results)
            if blocked:
                return True
        return False

    async def _evaluate_item(
        self,
        request: Request,
        item: RateLimitPolicy | PolicyGroup,
        results: list[RateLimitResult],
    ) -> bool:
        """Dispatch to group or policy evaluation. Returns True if blocked."""
        if isinstance(item, PolicyGroup):
            return await self._evaluate_group(request, item, results)
        return await self._evaluate_policy(request, item, results)

    async def _evaluate_policy(
        self,
        request: Request,
        policy: RateLimitPolicy,
        results: list[RateLimitResult],
    ) -> bool:
        """Evaluate a single policy leaf. Returns True if the policy blocks."""
        try:
            key = await self._key_builder.build_key(request, policy)
            result = await self._backend.check(key, policy)
            results.append(result)
            return not result.allowed
        except RateLimitBackendError as exc:
            if self._failure_strategy == FailureStrategy.FAIL_CLOSED:
                raise
            logger.warning(
                "rate_limiter.backend_error",
                policy=policy.name,
                error=str(exc),
            )
            results.append(
                RateLimitResult(
                    allowed=True,
                    key="unknown",
                    limit=0,
                    policy_name=policy.name,
                    remaining=0,
                    reset_at=datetime.now(tz=timezone.utc),
                ),
            )
            return False

    async def _evaluate_group(
        self,
        request: Request,
        group: PolicyGroup,
        results: list[RateLimitResult],
    ) -> bool:
        """Evaluate a PolicyGroup. Returns True if the group blocks the request.

        AND: sequential, short-circuits on first blocking policy.
        OR:  evaluates all policies, allows if at least one passes.
        """
        if group.mode == "AND":
            for item in group.policies:
                blocked = await self._evaluate_item(request, item, results)
                if blocked:
                    return True
            return False

        # OR — evaluate all, allow if any passes
        group_results: list[RateLimitResult] = []
        any_allowed = False
        for item in group.policies:
            item_results: list[RateLimitResult] = []
            blocked = await self._evaluate_item(request, item, item_results)
            group_results.extend(item_results)
            if not blocked:
                any_allowed = True
        results.extend(group_results)
        return not any_allowed

    async def reset_key(self, key: str) -> None:
        """Reset rate limit counters for a key.

        Args:
            key: The storage key to clear.
        """
        await self._backend.reset(key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_backend_and_service(
    config: RateLimitConfig,
    redis_client: object | None = None,
) -> tuple[RateLimitBackend, RateLimiterService]:
    """Construct backend and service from config."""
    from axiom.fastapi.rate_limiter.backend.redis import RedisRateLimitBackend

    if redis_client is not None:
        try:
            connection_kwargs = (
                redis_client._client.connection_pool.connection_kwargs  # type: ignore[union-attr]
            )
            host = connection_kwargs.get("host", "localhost")
            port = connection_kwargs.get("port", 6379)
            db = connection_kwargs.get("db", 0)
            redis_url = f"redis://{host}:{port}/{db}"
        except Exception:
            redis_url = "redis://localhost:6379"
        backend: RateLimitBackend = RedisRateLimitBackend(redis_url, redis_client)
    else:
        backend = InMemoryRateLimitBackend()

    service = RateLimiterService(
        backend=backend,
        key_builder=IPKeyBuilder(),
        failure_strategy=config.failure_strategy,
        policies=list(config.policies),
        enabled=config.enabled,
    )
    return backend, service


@asynccontextmanager
async def rate_limiter_lifespan(
    app: object,
    config: RateLimitConfig,
    redis_client: object | None = None,
) -> AsyncGenerator[RateLimiterService, None]:
    """Async context manager for rate limiter lifecycle management.

    Intended to be composed into a FastAPI lifespan function::

        from contextlib import asynccontextmanager
        from fastapi import FastAPI
        from axiom.fastapi.rate_limiter import rate_limiter_lifespan, RateLimitConfig

        config = RateLimitConfig(policies=[IPPolicy("100/minute")])


        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with rate_limiter_lifespan(app, config):
                yield


        app = FastAPI(lifespan=lifespan)

    On entry: creates backend, attaches service to ``app.state.rate_limiter``,
    calls ``backend.startup()``.
    On exit: calls ``backend.shutdown()``.

    Args:
        app: FastAPI application instance.
        config: Rate limit configuration.
        redis_client: Optional ``AsyncRedisClient`` for Redis backend.

    Yields:
        Configured ``RateLimiterService`` instance.
    """
    from axiom.fastapi.app.state import AppStateManager

    backend, service = _build_backend_and_service(config, redis_client)
    AppStateManager(app).set("rate_limiter", service)
    await backend.startup()
    backend_type = "redis" if redis_client is not None else "memory"
    logger.info(
        "rate_limiter.started",
        backend=backend_type,
        policies_count=len(config.policies),
    )
    try:
        yield service
    finally:
        await backend.shutdown()
        logger.info("rate_limiter.stopped")


async def setup_rate_limiter(
    app: object,
    config: RateLimitConfig,
    redis_client: object | None = None,
) -> RateLimiterService:
    """Wire rate limiting into a FastAPI application without lifecycle management.

    Attaches ``RateLimiterService`` to ``app.state.rate_limiter`` but does NOT
    call ``backend.startup()`` or ``backend.shutdown()``. Use this only in tests
    or when lifecycle is managed by an outer context.

    For production, prefer ``rate_limiter_lifespan()`` which handles
    startup, shutdown, and proper lifespan composition.

    Args:
        app: FastAPI application instance.
        config: Rate limit configuration.
        redis_client: Optional ``AsyncRedisClient``; if provided, uses Redis backend.

    Returns:
        Configured ``RateLimiterService`` instance.
    """
    from axiom.fastapi.app.state import AppStateManager

    backend, service = _build_backend_and_service(config, redis_client)
    AppStateManager(app).set("rate_limiter", service)
    backend_type = "redis" if redis_client is not None else "memory"
    logger.info(
        "rate_limiter.setup",
        backend=backend_type,
        policies_count=len(config.policies),
    )
    return service
