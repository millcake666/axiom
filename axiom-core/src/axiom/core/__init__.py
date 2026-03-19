"""axiom.core — Foundation package for all axiom.* packages."""

__version__ = "0.1.0"

from axiom.core.context import (
    REQUEST_CONTEXT,
    BaseContext,
    RequestContext,
    TypedContextVar,
    set_request_context,
)
from axiom.core.entities import (
    BaseDomainDC,
    BaseRequestSchema,
    BaseResponseSchema,
    BaseSchema,
    PaginatedResponse,
)
from axiom.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    BaseError,
    ConflictError,
    ErrorDetail,
    InternalError,
    NotFoundError,
    UnprocessableError,
    ValidationError,
)
from axiom.core.logger import LoggerSettings, configure_logger, get_logger
from axiom.core.settings import AppMixin, BaseAppSettings, DebugMixin, make_env_prefix

__all__ = [
    # logger
    "LoggerSettings",
    "configure_logger",
    "get_logger",
    # settings
    "BaseAppSettings",
    "AppMixin",
    "DebugMixin",
    "make_env_prefix",
    # context
    "TypedContextVar",
    "BaseContext",
    "RequestContext",
    "REQUEST_CONTEXT",
    "set_request_context",
    # exceptions
    "BaseError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "AuthenticationError",
    "AuthorizationError",
    "BadRequestError",
    "UnprocessableError",
    "InternalError",
    "ErrorDetail",
    # entities
    "BaseSchema",
    "BaseRequestSchema",
    "BaseResponseSchema",
    "PaginatedResponse",
    "BaseDomainDC",
]
