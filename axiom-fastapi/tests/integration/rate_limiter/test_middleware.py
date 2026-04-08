"""Integration tests for RateLimitMiddleware using httpx.AsyncClient."""

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


async def test_first_n_requests_return_200(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        for _ in range(3):
            response = await client.get("/items")
            assert response.status_code == 200


async def test_n_plus_1_request_returns_429(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        for _ in range(3):
            await client.get("/items")
        response = await client.get("/items")
        assert response.status_code == 429
        body = response.json()
        assert body["code"] == "rate_limit_exceeded"


async def test_rate_limit_headers_present(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/items")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers


async def test_429_response_has_retry_after_header(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        for _ in range(3):
            await client.get("/items")
        response = await client.get("/items")
        assert response.status_code == 429
        assert "Retry-After" in response.headers


async def test_exempt_path_bypasses_rate_limit(test_app: FastAPI) -> None:
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Exhaust the limit
        for _ in range(4):
            await client.get("/items")
        # Exempt path should still return 200
        response = await client.get("/health")
        assert response.status_code == 200
