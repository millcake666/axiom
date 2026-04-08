"""Shared fixtures for rate limiter integration tests."""

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from axiom.fastapi.rate_limiter.backend.memory import InMemoryRateLimitBackend
from axiom.fastapi.rate_limiter.core.algorithm import FailureStrategy
from axiom.fastapi.rate_limiter.core.policy import IPPolicy
from axiom.fastapi.rate_limiter.exception import RateLimitExceededError
from axiom.fastapi.rate_limiter.key_builder.ip import IPKeyBuilder
from axiom.fastapi.rate_limiter.middleware import RateLimitMiddleware
from axiom.fastapi.rate_limiter.service import RateLimiterService


@pytest.fixture
def memory_backend() -> InMemoryRateLimitBackend:
    """Provide a fresh in-memory backend for each test."""
    return InMemoryRateLimitBackend()


@pytest.fixture
def test_app(memory_backend: InMemoryRateLimitBackend) -> FastAPI:
    """FastAPI app with RateLimitMiddleware using 3 req/min limit."""
    policies = [IPPolicy(limit="3/minute")]
    service = RateLimiterService(
        backend=memory_backend,
        policies=policies,
        key_builder=IPKeyBuilder(),
        failure_strategy=FailureStrategy.FAIL_OPEN,
    )

    app = FastAPI()
    app.state.rate_limiter = service
    app.add_middleware(RateLimitMiddleware, service=service, exempt_paths={"/health"})

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_handler(request: object, exc: RateLimitExceededError) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"code": exc.code, "message": exc.message},
        )

    @app.get("/items")
    async def list_items() -> dict:
        return {"items": []}

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app
