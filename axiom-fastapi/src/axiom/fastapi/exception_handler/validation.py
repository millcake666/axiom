"""axiom.fastapi.exception_handler.validation — Handler for RequestValidationError."""

from starlette.requests import Request

from axiom.core.exceptions.base import ErrorDetail
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def register_validation_handler(app: FastAPI) -> None:
    """Register the RequestValidationError handler on the FastAPI app.

    Args:
        app: FastAPI application instance.
    """

    async def handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(loc) for loc in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        detail = ErrorDetail(
            code="validation_error",
            message="Request validation failed",
            details={"errors": errors},
        )
        return JSONResponse(status_code=422, content=detail.model_dump())

    app.add_exception_handler(RequestValidationError, handler)  # type: ignore[arg-type]
