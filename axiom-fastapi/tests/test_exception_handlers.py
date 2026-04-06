"""Tests for exception handlers."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from axiom.core.exceptions.base import BaseError
from axiom.fastapi.exception_handler import register_all_handlers


def make_app() -> FastAPI:
    app = FastAPI()
    register_all_handlers(app)

    @app.get("/domain")
    async def domain() -> None:
        raise BaseError("bad", code="test_error", status_code=400)

    @app.get("/http")
    async def http_err() -> None:
        from starlette.exceptions import HTTPException

        raise HTTPException(status_code=404, detail="not found")

    @app.get("/unhandled")
    async def unhandled() -> None:
        raise RuntimeError("oops")

    return app


def test_domain_handler() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/domain")
    assert resp.status_code == 400
    assert resp.json()["code"] == "test_error"


def test_http_handler() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/http")
    assert resp.status_code == 404
    assert resp.json()["code"] == "http_404"


def test_unhandled_handler() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/unhandled")
    assert resp.status_code == 500
    assert resp.json()["code"] == "internal_error"


def test_validation_handler() -> None:
    app = FastAPI()
    register_all_handlers(app)

    @app.get("/validate")
    async def validate(name: int) -> dict:
        return {"name": name}

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/validate?name=notanint")
    assert resp.status_code == 422
    assert resp.json()["code"] == "validation_error"
