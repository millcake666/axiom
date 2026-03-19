"""axiom.core.exceptions — Domain exception hierarchy for axiom packages."""

from typing import Any

from pydantic import BaseModel


class BaseError(Exception):
    """Base class for all axiom domain errors."""

    code: str = "internal_error"
    status_code: int = 500

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize BaseError with message, optional code, details and status_code."""
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details: dict[str, Any] = details or {}


class NotFoundError(BaseError):
    """Resource not found."""

    code = "not_found"
    status_code = 404


class ValidationError(BaseError):
    """Validation failed."""

    code = "validation_error"
    status_code = 422


class ConflictError(BaseError):
    """Resource conflict."""

    code = "conflict"
    status_code = 409


class AuthenticationError(BaseError):
    """Authentication failed."""

    code = "authentication_error"
    status_code = 401


class AuthorizationError(BaseError):
    """Authorization denied."""

    code = "authorization_error"
    status_code = 403


class BadRequestError(BaseError):
    """Bad request."""

    code = "bad_request"
    status_code = 400


class UnprocessableError(BaseError):
    """Unprocessable entity."""

    code = "unprocessable"
    status_code = 422


class InternalError(BaseError):
    """Internal server error."""

    code = "internal_error"
    status_code = 500


class ErrorDetail(BaseModel):
    """Pydantic schema for serializing errors to API responses."""

    code: str
    message: str
    details: dict[str, Any] = {}

    @classmethod
    def from_error(cls, error: BaseError) -> "ErrorDetail":
        """Create ErrorDetail from a BaseError instance."""
        return cls(code=error.code, message=error.message, details=error.details)
