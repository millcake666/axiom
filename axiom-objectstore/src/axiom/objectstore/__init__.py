"""axiom.objectstore — Object and file storage integrations."""

__version__ = "0.1.0"

from axiom.objectstore.abs import AbstractAsyncObjectStore, AbstractSyncObjectStore
from axiom.objectstore.exception import (
    ObjectNotFoundError,
    ObjectStoreError,
    ObjectStoreInternalError,
)
from axiom.objectstore.local import (
    AsyncLocalDiskObjectStore,
    LocalDiskConfig,
    SyncLocalDiskObjectStore,
)
from axiom.objectstore.s3 import AsyncS3ObjectStore, S3Config, S3Settings, SyncS3ObjectStore

__all__ = [
    "__version__",
    # Abstract interfaces
    "AbstractAsyncObjectStore",
    "AbstractSyncObjectStore",
    # Exceptions
    "ObjectStoreError",
    "ObjectNotFoundError",
    "ObjectStoreInternalError",
    # S3
    "AsyncS3ObjectStore",
    "SyncS3ObjectStore",
    "S3Config",
    "S3Settings",
    # Local disk
    "AsyncLocalDiskObjectStore",
    "SyncLocalDiskObjectStore",
    "LocalDiskConfig",
]
