"""axiom.objectstore.s3.exception — Exceptions for the axiom.objectstore.s3 package."""

from axiom.objectstore.exception import (
    ObjectNotFoundError,
    ObjectStoreInternalError,
)


class S3ObjectNotFoundError(ObjectNotFoundError):
    """Raised when an S3 object does not exist."""

    code = "s3_object_not_found"


class S3InternalError(ObjectStoreInternalError):
    """Raised when an unexpected S3 backend error occurs."""

    code = "s3_internal_error"


__all__ = [
    "S3ObjectNotFoundError",
    "S3InternalError",
]
