"""axiom.objectstore.s3.async_ — Async S3 object storage client (aiobotocore)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from secrets import token_hex

from loguru import logger

from axiom.objectstore.abs import AbstractAsyncObjectStore
from axiom.objectstore.s3.config import S3Config
from axiom.objectstore.s3.exception import S3InternalError, S3ObjectNotFoundError


class AsyncS3ObjectStore(AbstractAsyncObjectStore):
    """Async S3-compatible object storage client powered by aiobotocore.

    Args:
        config: S3 connection configuration.
    """

    def __init__(self, config: S3Config) -> None:
        """Initialise the async S3 client.

        Args:
            config: S3 connection configuration.
        """
        self._config = config

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[object]:
        """Yield a temporary aiobotocore S3 client session.

        Yields:
            An aiobotocore S3 client.
        """
        import aiobotocore.session  # type: ignore[import-untyped]

        session = aiobotocore.session.get_session()
        async with session.create_client(
            self._config.service_name,
            region_name=self._config.region_name,
            endpoint_url=self._config.endpoint_url,
            aws_access_key_id=self._config.aws_access_key_id,
            aws_secret_access_key=self._config.aws_secret_access_key,
        ) as client:
            yield client

    def _make_key(self, name: str | None) -> str:
        """Return a storage key, generating a unique one when *name* is omitted.

        Args:
            name: Explicit key, or ``None`` to generate a random hex key.

        Returns:
            The resolved storage key (with optional prefix applied).
        """
        key = name if name is not None else token_hex(16)
        prefix = self._config.key_prefix
        return f"{prefix}{key}" if prefix else key

    async def upload(
        self,
        data: bytes,
        name: str | None = None,
        content_disposition: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to S3 and return the stored key.

        Args:
            data: Raw bytes to upload.
            name: Optional explicit key; if omitted a unique name is generated.
            content_disposition: Optional Content-Disposition header value.
            content_type: MIME type of the object.

        Returns:
            The key under which the object was stored.

        Raises:
            S3InternalError: If the S3 operation fails unexpectedly.
        """
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        key = self._make_key(name)
        extra: dict[str, str] = {"ContentType": content_type}
        if content_disposition:
            extra["ContentDisposition"] = content_disposition

        try:
            async with self._client() as client:
                await client.put_object(
                    Bucket=self._config.bucket_name,
                    Key=key,
                    Body=data,
                    **extra,
                )
        except ClientError as exc:
            logger.error("S3 upload failed: key={} error={}", key, exc)
            raise S3InternalError(str(exc)) from exc

        logger.info("S3 upload succeeded: key={} size={}", key, len(data))
        return key

    async def get(self, name: str) -> bytes:
        """Download an object from S3 by key.

        Args:
            name: Key of the object to retrieve.

        Returns:
            Raw bytes of the stored object.

        Raises:
            S3ObjectNotFoundError: If no object exists with the given key.
            S3InternalError: If the S3 operation fails unexpectedly.
        """
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        try:
            async with self._client() as client:
                response = await client.get_object(
                    Bucket=self._config.bucket_name,
                    Key=name,
                )
                return await response["Body"].read()
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404"):
                raise S3ObjectNotFoundError(f"Object not found: {name}") from exc
            raise S3InternalError(str(exc)) from exc

    async def delete(self, name: str) -> None:
        """Delete an object from S3.

        Args:
            name: Key of the object to delete.

        Raises:
            S3ObjectNotFoundError: If no object exists with the given key.
            S3InternalError: If the S3 operation fails unexpectedly.
        """
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        if not await self.exists(name):
            raise S3ObjectNotFoundError(f"Object not found: {name}")

        try:
            async with self._client() as client:
                await client.delete_object(
                    Bucket=self._config.bucket_name,
                    Key=name,
                )
        except ClientError as exc:
            raise S3InternalError(str(exc)) from exc

        logger.info("S3 delete succeeded: key={}", name)

    async def exists(self, name: str) -> bool:
        """Check whether an S3 object exists.

        Args:
            name: Key of the object to check.

        Returns:
            ``True`` if the object exists, ``False`` otherwise.

        Raises:
            S3InternalError: If the S3 operation fails unexpectedly.
        """
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        try:
            async with self._client() as client:
                await client.head_object(
                    Bucket=self._config.bucket_name,
                    Key=name,
                )
            return True
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code in ("NoSuchKey", "404", "403"):
                return False
            raise S3InternalError(str(exc)) from exc

    async def get_url(self, name: str) -> str:
        """Return the public URL for an S3 object.

        Args:
            name: Key of the object.

        Returns:
            Public URL string pointing to the object.
        """
        endpoint = self._config.endpoint_url.rstrip("/")
        bucket = self._config.bucket_name
        return f"{endpoint}/{bucket}/{name}"

    async def get_presigned_url(self, name: str, expiration_sec: int = 3600) -> str:
        """Generate a presigned URL granting temporary access to an object.

        Args:
            name: Key of the object.
            expiration_sec: Seconds until the URL expires (default: 3600).

        Returns:
            A presigned URL string.

        Raises:
            S3InternalError: If the S3 operation fails unexpectedly.
        """
        from botocore.exceptions import ClientError  # type: ignore[import-untyped]

        try:
            async with self._client() as client:
                url: str = await client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self._config.bucket_name, "Key": name},
                    ExpiresIn=expiration_sec,
                )
            return url
        except ClientError as exc:
            raise S3InternalError(str(exc)) from exc
