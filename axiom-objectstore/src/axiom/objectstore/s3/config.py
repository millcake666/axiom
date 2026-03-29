"""axiom.objectstore.s3.config — Pydantic config models for S3 object storage."""

from __future__ import annotations

from pydantic import BaseModel


class S3Settings(BaseModel):
    """Mixin for ``BaseAppSettings`` that provides S3 configuration fields.

    Intended to be mixed into a ``BaseAppSettings`` subclass to load S3
    credentials and connection parameters from environment variables.

    Attributes:
        S3_AWS_ACCESS_KEY_ID: AWS access key ID.
        S3_AWS_SECRET_ACCESS_KEY: AWS secret access key.
        S3_ENDPOINT_URL: Custom endpoint URL (e.g. for MinIO or other S3-compatible stores).
        S3_REGION_NAME: AWS region name.
        S3_SERVICE_NAME: Service name used in the boto client (default: ``"s3"``).
        S3_BUCKET_NAME: Target bucket name.
        S3_KEY_PREFIX: Optional prefix prepended to all object keys.
        S3_IS_PUBLIC: Whether generated URLs should be public (default: ``True``).
    """

    S3_AWS_ACCESS_KEY_ID: str = ""
    S3_AWS_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION_NAME: str = ""
    S3_SERVICE_NAME: str = "s3"
    S3_BUCKET_NAME: str = ""
    S3_KEY_PREFIX: str = ""
    S3_IS_PUBLIC: bool = True


class S3Config(BaseModel):
    """Configuration for an S3-compatible object storage client.

    Attributes:
        aws_access_key_id: AWS access key ID.
        aws_secret_access_key: AWS secret access key.
        endpoint_url: Custom endpoint URL (e.g. for MinIO or other S3-compatible stores).
        region_name: AWS region name.
        service_name: Service name used in the boto client (default: ``"s3"``).
        bucket_name: Target bucket name.
        key_prefix: Optional prefix prepended to all object keys.
        is_public: Whether generated URLs should be public (default: ``True``).
    """

    aws_access_key_id: str
    aws_secret_access_key: str
    endpoint_url: str
    region_name: str
    service_name: str = "s3"
    bucket_name: str
    key_prefix: str = ""
    is_public: bool = True

    @classmethod
    def from_settings(cls, settings: S3Settings) -> S3Config:
        """Create an ``S3Config`` from an ``S3Settings`` mixin instance.

        Args:
            settings: An ``S3Settings`` (or ``BaseAppSettings`` subclass) instance.

        Returns:
            A populated ``S3Config``.
        """
        return cls(
            aws_access_key_id=settings.S3_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name=settings.S3_REGION_NAME,
            service_name=settings.S3_SERVICE_NAME,
            bucket_name=settings.S3_BUCKET_NAME,
            key_prefix=settings.S3_KEY_PREFIX,
            is_public=settings.S3_IS_PUBLIC,
        )
