"""axiom.core.exceptions — Domain exception hierarchy for axiom packages."""

from axiom.core.exceptions.base import BaseError, ErrorDetail
from axiom.core.exceptions.http import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConflictError,
    InternalError,
    NotFoundError,
    UnprocessableError,
    ValidationError,
)

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "BadRequestError",
    "BaseError",
    "ConflictError",
    "ErrorDetail",
    "InternalError",
    "NotFoundError",
    "UnprocessableError",
    "ValidationError",
]
