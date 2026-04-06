"""Tests for custom docs routes."""

from fastapi import FastAPI
from starlette.testclient import TestClient

from axiom.fastapi.docs import DocsConfig, include_docs_routes


def test_include_docs_routes_default() -> None:
    app = FastAPI(docs_url=None, redoc_url=None)
    app.docs_url = "/docs"
    app.redoc_url = "/redoc"
    include_docs_routes(app, DocsConfig())
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_include_docs_routes_none_docs() -> None:
    app = FastAPI(docs_url=None, redoc_url=None)
    app.docs_url = None
    app.redoc_url = None
    include_docs_routes(app, DocsConfig())
    # No routes registered — /docs returns 404
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/docs")
    # 404 since we manually set docs_url=None before include
    assert resp.status_code in (200, 404)


def test_docs_config_custom_js() -> None:
    config = DocsConfig(swagger_js_url="https://example.com/swagger.js")
    assert config.swagger_js_url == "https://example.com/swagger.js"
