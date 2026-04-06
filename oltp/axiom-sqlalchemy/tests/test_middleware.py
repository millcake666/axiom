"""Tests for SQLAlchemy ASGI middleware."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from axiom.oltp.sqlalchemy.middleware import AsyncSQLAlchemyMiddleware, SyncSQLAlchemyMiddleware
from axiom.oltp.sqlalchemy.postgres.context import get_session_context


def make_async_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AsyncSQLAlchemyMiddleware)  # type: ignore[arg-type]

    @app.get("/ctx")
    async def ctx() -> dict:
        return {"session_id": get_session_context()}

    return app


def make_sync_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SyncSQLAlchemyMiddleware)

    @app.get("/ctx")
    async def ctx() -> dict:
        return {"session_id": get_session_context()}

    return app


def test_async_middleware_sets_context() -> None:
    client = TestClient(make_async_app())
    resp = client.get("/ctx")
    assert resp.status_code == 200
    assert resp.json()["session_id"]


def test_sync_middleware_sets_context() -> None:
    client = TestClient(make_sync_app())
    resp = client.get("/ctx")
    assert resp.status_code == 200
    assert resp.json()["session_id"]
