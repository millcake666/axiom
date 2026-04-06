"""Tests for RequestLoggingMiddleware."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from axiom.fastapi.middleware.logging import RequestLoggingMiddleware


def make_app(raise_exc: bool = False) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)  # type: ignore[arg-type]

    @app.get("/hello")
    async def hello() -> dict:
        return {"ok": True}

    return app


def test_basic_request() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/hello")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers


def test_forwarded_request_id() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/hello", headers={"X-Request-ID": "my-id"})
    assert resp.headers["x-request-id"] == "my-id"


def test_non_http_scope_passthrough() -> None:
    # WebSocket connections should not be blocked
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/hello")
    assert resp.status_code == 200
