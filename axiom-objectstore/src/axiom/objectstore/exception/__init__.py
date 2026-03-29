"""axiom.objectstore.exception — Exceptions for the axiom.objectstore package."""

from axiom.core.exceptions.base import BaseError
from axiom.core.exceptions.http import InternalError, NotFoundError


class ObjectStoreError(BaseError):
    """Base exception for all object store errors."""

    code = "object_store_error"


class ObjectNotFoundError(NotFoundError):
    """Raised when an object does not exist in the store."""

    code = "object_not_found"


class ObjectStoreInternalError(InternalError):
    """Raised when an unexpected storage backend error occurs."""

    code = "object_store_internal_error"


__all__ = [
    "ObjectStoreError",
    "ObjectNotFoundError",
    "ObjectStoreInternalError",
]
