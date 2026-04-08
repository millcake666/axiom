"""axiom.oltp.sqlalchemy.exception_handler.integrity — SQLAlchemy IntegrityError handler."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

from axiom.core.exceptions.base import ErrorDetail
from axiom.core.logger import get_logger
from sqlalchemy.exc import IntegrityError

logger = get_logger(__name__)

_PGCODE_MAP: dict[str, tuple[int, str, str]] = {
    "23505": (409, "db.unique_violation", "A record with this value already exists."),
    "23503": (404, "db.foreign_key_violation", "Referenced record not found."),
    "23502": (400, "db.not_null_violation", "A required field is missing."),
    "23514": (400, "db.check_violation", "A value failed a check constraint."),
}

_EXCEPTION_NAME_MAP: dict[str, tuple[int, str, str]] = {
    "UniqueViolationError": (
        409,
        "db.unique_violation",
        "A record with this value already exists.",
    ),
    "ForeignKeyViolationError": (404, "db.foreign_key_violation", "Referenced record not found."),
    "NotNullViolationError": (400, "db.not_null_violation", "A required field is missing."),
    "CheckViolationError": (400, "db.check_violation", "A value failed a check constraint."),
}


def _resolve_integrity_error(exc: IntegrityError) -> tuple[int, str, str]:
    orig = getattr(exc, "orig", None)
    if orig is not None:
        pgcode = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
        if pgcode and pgcode in _PGCODE_MAP:
            return _PGCODE_MAP[pgcode]
        exc_name = type(orig).__name__
        if exc_name in _EXCEPTION_NAME_MAP:
            return _EXCEPTION_NAME_MAP[exc_name]
    return 500, "db.integrity_error", "A database integrity error occurred."


def register_integrity_handler(app: FastAPI, *, use_logger: bool = True) -> None:
    """Register the IntegrityError exception handler on the FastAPI app.

    Args:
        app: FastAPI application instance.
        use_logger: Whether to log errors via loguru.
    """

    async def handler(request: Request, exc: IntegrityError) -> JSONResponse:
        status_code, code, message = _resolve_integrity_error(exc)
        if use_logger:
            if status_code >= 500:
                logger.opt(exception=exc).error("db.integrity_error")
            else:
                logger.bind(code=code, status_code=status_code).info("db.integrity_error")
        detail = ErrorDetail(code=code, message=message, details={})
        return JSONResponse(status_code=status_code, content=detail.model_dump())

    app.add_exception_handler(IntegrityError, handler)  # type: ignore[arg-type]
