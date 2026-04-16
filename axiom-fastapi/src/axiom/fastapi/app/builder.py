"""axiom.fastapi.app.builder — create_app() factory function."""

from axiom.fastapi.app.config import AppConfig
from fastapi import FastAPI


def create_app(config: AppConfig) -> FastAPI:
    """Create and configure a FastAPI application.

    Args:
        config: Application configuration.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title=config.title or "Axiom API",
        version=config.version or "0.1.0",
        description=config.description or "",
        debug=config.debug,
        docs_url=config.docs_url if config.docs_config is None else None,
        redoc_url=config.redoc_url if config.docs_config is None else None,
        openapi_url=config.openapi_url,
        middleware=config.middleware,
    )

    if config.register_default_handlers:
        from axiom.fastapi.exception_handler import register_all_handlers
        from axiom.fastapi.middleware.error import ErrorMiddleware

        register_all_handlers(app)
        app.add_middleware(ErrorMiddleware)  # type: ignore[arg-type]

    for exc_type, handler in config.exception_handlers.items():
        app.add_exception_handler(exc_type, handler)  # type: ignore[arg-type]

    if config.docs_config is not None:
        from axiom.fastapi.docs.routes import include_docs_routes

        include_docs_routes(
            app,
            config.docs_config,
            docs_url=config.docs_url,
            redoc_url=config.redoc_url,
        )

    return app
