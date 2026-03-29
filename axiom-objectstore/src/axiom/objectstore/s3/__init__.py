"""axiom.objectstore.s3 — S3-compatible object storage (aiobotocore / boto3)."""

from axiom.objectstore.s3.async_ import AsyncS3ObjectStore
from axiom.objectstore.s3.config import S3Config, S3Settings
from axiom.objectstore.s3.sync import SyncS3ObjectStore

__all__ = [
    "AsyncS3ObjectStore",
    "SyncS3ObjectStore",
    "S3Config",
    "S3Settings",
]
