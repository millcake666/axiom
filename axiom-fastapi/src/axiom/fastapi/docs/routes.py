"""axiom.fastapi.docs.routes — Configurable Swagger/ReDoc doc routes."""

from pydantic import BaseModel

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)

_DEFAULT_SWAGGER_JS = "https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"
_DEFAULT_SWAGGER_CSS = "https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"
_DEFAULT_REDOC_JS = "https://unpkg.com/redoc@next/bundles/redoc.standalone.js"


class DocsConfig(BaseModel):
    """Configuration for custom docs routes.

    If a URL is None, the FastAPI default CDN URL is used.
    """

    swagger_js_url: str | None = None
    swagger_css_url: str | None = None
    redoc_js_url: str | None = None
    oauth2_redirect_url: str | None = None


def include_docs_routes(app: FastAPI, config: DocsConfig) -> None:
    """Register customizable Swagger/ReDoc routes on the app.

    Args:
        app: FastAPI application instance.
        config: Docs configuration with optional CDN URL overrides.
    """
    swagger_js = config.swagger_js_url or _DEFAULT_SWAGGER_JS
    swagger_css = config.swagger_css_url or _DEFAULT_SWAGGER_CSS
    redoc_js = config.redoc_js_url or _DEFAULT_REDOC_JS
    oauth2_redirect = config.oauth2_redirect_url or "/docs/oauth2-redirect"

    if app.docs_url is not None:

        @app.get(app.docs_url, include_in_schema=False)
        async def swagger_ui() -> object:
            return get_swagger_ui_html(
                openapi_url=app.openapi_url or "/openapi.json",
                title=f"{app.title} - Swagger UI",
                oauth2_redirect_url=oauth2_redirect,
                swagger_js_url=swagger_js,
                swagger_css_url=swagger_css,
            )

        @app.get(oauth2_redirect, include_in_schema=False)
        async def swagger_redirect() -> object:
            return get_swagger_ui_oauth2_redirect_html()

    if app.redoc_url is not None:

        @app.get(app.redoc_url, include_in_schema=False)
        async def redoc() -> object:
            return get_redoc_html(
                openapi_url=app.openapi_url or "/openapi.json",
                title=f"{app.title} - ReDoc",
                redoc_js_url=redoc_js,
            )
