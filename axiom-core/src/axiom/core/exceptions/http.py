# mypy: disable-error-code="misc"
"""axiom.core.exceptions.http — HTTP-aware exception subclasses."""

from axiom.core.exceptions.base import BaseError


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
