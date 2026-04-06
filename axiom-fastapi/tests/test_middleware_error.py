"""Tests for ErrorMiddleware."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from axiom.fastapi.middleware.error import ErrorMiddleware


def make_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ErrorMiddleware)  # type: ignore[arg-type]

    @app.get("/ok")
    async def ok() -> dict:
        return {"ok": True}

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("boom")

    return app


def test_normal_request() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/ok")
    assert resp.status_code == 200


def test_unhandled_exception_returns_500() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 500
    data = resp.json()
    assert data["code"] == "internal_error"
