"""axiom.fastapi.exception_handler.unhandled — Catch-all exception handler."""

import structlog
from starlette.requests import Request

from axiom.core.exceptions.base import ErrorDetail
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


def register_unhandled_handler(app: FastAPI, *, use_logger: bool = True) -> None:
    """Register the catch-all Exception handler on the FastAPI app.

    Args:
        app: FastAPI application instance.
        use_logger: Whether to log errors via structlog.
    """

    async def handler(request: Request, exc: Exception) -> JSONResponse:
        if use_logger:
            logger.exception("unhandled_exception", exc_info=exc)
        detail = ErrorDetail(
            code="internal_error",
            message="An unexpected error occurred.",
            details={},
        )
        return JSONResponse(status_code=500, content=detail.model_dump())

    app.add_exception_handler(Exception, handler)  # type: ignore[arg-type]
