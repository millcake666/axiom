"""Integration tests for rate_limit() FastAPI dependency."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from axiom.fastapi.rate_limiter.backend.memory import InMemoryRateLimitBackend
from axiom.fastapi.rate_limiter.core.algorithm import FailureStrategy
from axiom.fastapi.rate_limiter.core.scope import RateLimitScope
from axiom.fastapi.rate_limiter.dependency import rate_limit
from axiom.fastapi.rate_limiter.exception import RateLimitExceededError
from axiom.fastapi.rate_limiter.key_builder.ip import IPKeyBuilder
from axiom.fastapi.rate_limiter.service import RateLimiterService


@pytest.fixture
def dep_app() -> FastAPI:
    """FastAPI app using rate_limit() dependency directly on a route."""
    backend = InMemoryRateLimitBackend()
    service = RateLimiterService(
        backend=backend,
        policies=[],
        key_builder=IPKeyBuilder(),
        failure_strategy=FailureStrategy.FAIL_OPEN,
    )

    app = FastAPI()
    app.state.rate_limiter = service

    @app.exception_handler(RateLimitExceededError)
    async def handle_rate_limit(request: object, exc: RateLimitExceededError) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"code": exc.code, "message": exc.message},
        )

    @app.get("/limited", dependencies=[Depends(rate_limit("3/minute", scope=RateLimitScope.IP))])
    async def limited_endpoint() -> dict:
        return {"ok": True}

    return app


async def test_dependency_allows_requests_under_limit(dep_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=dep_app), base_url="http://test") as client:
        for _ in range(3):
            response = await client.get("/limited")
            assert response.status_code == 200


async def test_dependency_blocks_after_limit_exceeded(dep_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=dep_app), base_url="http://test") as client:
        for _ in range(3):
            await client.get("/limited")
        response = await client.get("/limited")
        assert response.status_code == 429


async def test_dependency_sets_rate_limit_headers(dep_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=dep_app), base_url="http://test") as client:
        response = await client.get("/limited")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


async def test_dependency_raises_429_via_exception_handler(dep_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=dep_app), base_url="http://test") as client:
        for _ in range(3):
            await client.get("/limited")
        response = await client.get("/limited")
        body = response.json()
        assert body["code"] == "rate_limit_exceeded"
        assert response.status_code == 429
