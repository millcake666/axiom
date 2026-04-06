"""Tests for SQLAlchemy IntegrityError handler."""

from fastapi import FastAPI
from sqlalchemy.exc import IntegrityError
from starlette.testclient import TestClient

from axiom.oltp.sqlalchemy.exception_handler import register_integrity_handler


def make_app(pgcode: str | None = None, exc_name: str | None = None) -> FastAPI:
    app = FastAPI()
    register_integrity_handler(app, use_logger=False)

    @app.get("/trigger")
    async def trigger() -> None:
        orig = Exception("db error")
        if pgcode:
            orig.pgcode = pgcode  # type: ignore[attr-defined]
        elif exc_name:
            orig.__class__ = type(exc_name, (Exception,), {})
        raise IntegrityError("statement", {}, orig)

    return app


def test_unique_violation_returns_409() -> None:
    app = make_app(pgcode="23505")
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/trigger")
    assert resp.status_code == 409
    assert resp.json()["code"] == "db.unique_violation"


def test_foreign_key_violation_returns_404() -> None:
    app = make_app(pgcode="23503")
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/trigger")
    assert resp.status_code == 404


def test_not_null_violation_returns_400() -> None:
    app = make_app(pgcode="23502")
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/trigger")
    assert resp.status_code == 400


def test_unknown_integrity_error_returns_500() -> None:
    app = make_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/trigger")
    assert resp.status_code == 500
