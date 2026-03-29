"""axiom.objectstore.local.exception — Exceptions for the axiom.objectstore.local package."""

from axiom.objectstore.exception import (
    ObjectNotFoundError,
    ObjectStoreInternalError,
)


class LocalObjectNotFoundError(ObjectNotFoundError):
    """Raised when a local disk object does not exist."""

    code = "local_object_not_found"


class LocalInternalError(ObjectStoreInternalError):
    """Raised when an unexpected local disk error occurs."""

    code = "local_internal_error"


__all__ = [
    "LocalObjectNotFoundError",
    "LocalInternalError",
]
