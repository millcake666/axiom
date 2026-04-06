"""axiom.fastapi.exception_handler.domain — Handler for BaseError domain exceptions."""

from typing import TYPE_CHECKING

import structlog
from starlette.requests import Request

from axiom.core.exceptions.base import BaseError, ErrorDetail
from fastapi import FastAPI
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


async def _domain_handler(request: Request, exc: BaseError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.exception("domain_error", exc_info=exc)
    detail = ErrorDetail.from_error(exc)
    return JSONResponse(status_code=exc.status_code, content=detail.model_dump())


def register_domain_handler(app: FastAPI, *, use_logger: bool = True) -> None:
    """Register the BaseError exception handler on the FastAPI app.

    Args:
        app: FastAPI application instance.
        use_logger: Whether to log errors via structlog.
    """

    async def handler(request: Request, exc: BaseError) -> JSONResponse:
        if use_logger and exc.status_code >= 500:
            logger.exception("domain_error", exc_info=exc)
        detail = ErrorDetail.from_error(exc)
        return JSONResponse(status_code=exc.status_code, content=detail.model_dump())

    app.add_exception_handler(BaseError, handler)  # type: ignore[arg-type]
