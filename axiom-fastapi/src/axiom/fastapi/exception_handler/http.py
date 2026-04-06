"""axiom.fastapi.exception_handler.http — Handler for starlette HTTPException."""

from starlette.exceptions import HTTPException
from starlette.requests import Request

from axiom.core.exceptions.base import ErrorDetail
from fastapi import FastAPI
from fastapi.responses import JSONResponse


def register_http_handler(app: FastAPI) -> None:
    """Register the HTTPException handler on the FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    async def handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = ErrorDetail(
            code=f"http_{exc.status_code}",
            message=str(exc.detail),
            details={},
        )
        return JSONResponse(status_code=exc.status_code, content=detail.model_dump())

    app.add_exception_handler(HTTPException, handler)  # type: ignore[arg-type]
