"""Tests for axiom.objectstore.s3.async_ — AsyncS3ObjectStore."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from axiom.objectstore.s3 import AsyncS3ObjectStore, S3Config
from axiom.objectstore.s3.exception import S3InternalError, S3ObjectNotFoundError


@pytest.fixture()
def config() -> S3Config:
    """Return an S3Config for tests."""
    return S3Config(
        aws_access_key_id=os.environ.get("TEST_S3_ACCESS_KEY_ID", "key"),
        aws_secret_access_key=os.environ.get("TEST_S3_SECRET_ACCESS_KEY", "secret"),
        endpoint_url="https://s3.example.com",
        region_name="us-east-1",
        bucket_name="test-bucket",
        key_prefix="prefix/",
    )


@pytest.fixture()
def store(config: S3Config) -> AsyncS3ObjectStore:
    """Return an AsyncS3ObjectStore for tests."""
    return AsyncS3ObjectStore(config)


def _make_client_error(code: str) -> MagicMock:
    """Build a fake botocore ClientError with the given error code."""
    from botocore.exceptions import ClientError  # type: ignore[import-untyped]

    error_response = {"Error": {"Code": code, "Message": "test"}}
    return ClientError(error_response, "operation")


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


async def test_upload_returns_key(store: AsyncS3ObjectStore) -> None:
    """upload with explicit name returns that name (with prefix)."""
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock(return_value={})
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        key = await store.upload(b"data", name="file.bin")
    assert key == "prefix/file.bin"
    mock_client.put_object.assert_awaited_once()


async def test_upload_generates_key_when_name_none(store: AsyncS3ObjectStore) -> None:
    """upload without name generates a unique hex key."""
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock(return_value={})
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        key = await store.upload(b"data")
    assert key.startswith("prefix/")
    assert len(key) == len("prefix/") + 32  # token_hex(16) → 32 hex chars


async def test_upload_raises_internal_error_on_client_error(store: AsyncS3ObjectStore) -> None:
    """upload wraps ClientError in S3InternalError."""
    err = _make_client_error("InternalError")
    mock_client = AsyncMock()
    mock_client.put_object = AsyncMock(side_effect=err)
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(S3InternalError):
            await store.upload(b"data", name="file.bin")


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


async def test_get_returns_bytes(store: AsyncS3ObjectStore) -> None:
    """get returns raw bytes from S3."""
    body_mock = AsyncMock()
    body_mock.read = AsyncMock(return_value=b"hello")
    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(return_value={"Body": body_mock})
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await store.get("prefix/file.bin")
    assert result == b"hello"


async def test_get_raises_not_found_on_no_such_key(store: AsyncS3ObjectStore) -> None:
    """get raises S3ObjectNotFoundError for NoSuchKey."""
    err = _make_client_error("NoSuchKey")
    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(side_effect=err)
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(S3ObjectNotFoundError):
            await store.get("missing")


async def test_get_raises_internal_error_on_other_error(store: AsyncS3ObjectStore) -> None:
    """get wraps unexpected ClientError in S3InternalError."""
    err = _make_client_error("AccessDenied")
    mock_client = AsyncMock()
    mock_client.get_object = AsyncMock(side_effect=err)
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(S3InternalError):
            await store.get("file")


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------


async def test_exists_returns_true(store: AsyncS3ObjectStore) -> None:
    """exists returns True when head_object succeeds."""
    mock_client = AsyncMock()
    mock_client.head_object = AsyncMock(return_value={})
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        assert await store.exists("file") is True


async def test_exists_returns_false_on_404(store: AsyncS3ObjectStore) -> None:
    """exists returns False when head_object raises 404."""
    err = _make_client_error("404")
    mock_client = AsyncMock()
    mock_client.head_object = AsyncMock(side_effect=err)
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        assert await store.exists("missing") is False


async def test_exists_raises_internal_error_on_other_error(store: AsyncS3ObjectStore) -> None:
    """exists raises S3InternalError for unexpected errors."""
    err = _make_client_error("ServiceUnavailable")
    mock_client = AsyncMock()
    mock_client.head_object = AsyncMock(side_effect=err)
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(S3InternalError):
            await store.exists("file")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


async def test_delete_calls_delete_object(store: AsyncS3ObjectStore) -> None:
    """delete calls delete_object when object exists."""
    mock_client = AsyncMock()
    mock_client.head_object = AsyncMock(return_value={})
    mock_client.delete_object = AsyncMock(return_value={})
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        await store.delete("prefix/file.bin")
    mock_client.delete_object.assert_awaited_once()


async def test_delete_raises_not_found_when_missing(store: AsyncS3ObjectStore) -> None:
    """delete raises S3ObjectNotFoundError when object doesn't exist."""
    with patch.object(store, "exists", AsyncMock(return_value=False)):
        with pytest.raises(S3ObjectNotFoundError):
            await store.delete("missing")


# ---------------------------------------------------------------------------
# get_url
# ---------------------------------------------------------------------------


async def test_get_url_returns_public_url(store: AsyncS3ObjectStore) -> None:
    """get_url constructs the public URL from endpoint + bucket + key."""
    url = await store.get_url("prefix/file.bin")
    assert url == "https://s3.example.com/test-bucket/prefix/file.bin"


# ---------------------------------------------------------------------------
# get_presigned_url
# ---------------------------------------------------------------------------


async def test_get_presigned_url_returns_url(store: AsyncS3ObjectStore) -> None:
    """get_presigned_url returns the generated presigned URL."""
    mock_client = AsyncMock()
    mock_client.generate_presigned_url = AsyncMock(return_value="https://signed.example.com/obj")
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        url = await store.get_presigned_url("prefix/file.bin")
    assert url == "https://signed.example.com/obj"


async def test_get_presigned_url_raises_internal_error_on_failure(
    store: AsyncS3ObjectStore,
) -> None:
    """get_presigned_url wraps ClientError in S3InternalError."""
    err = _make_client_error("InternalError")
    mock_client = AsyncMock()
    mock_client.generate_presigned_url = AsyncMock(side_effect=err)
    with patch.object(store, "_client") as mock_cm:
        mock_cm.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cm.return_value.__aexit__ = AsyncMock(return_value=None)
        with pytest.raises(S3InternalError):
            await store.get_presigned_url("file")


# --- S3Settings / S3Config.from_settings ---


def test_s3_settings_defaults() -> None:
    """S3Settings has correct default values."""
    from axiom.objectstore.s3 import S3Settings

    settings = S3Settings()
    assert settings.S3_SERVICE_NAME == "s3"
    assert settings.S3_KEY_PREFIX == ""
    assert settings.S3_IS_PUBLIC is True


def test_s3_config_from_settings() -> None:
    """S3Config.from_settings creates a config matching the settings values."""
    from axiom.objectstore.s3 import S3Settings

    access_id = os.environ.get("TEST_S3_ACCESS_KEY_ID", "key123")
    access_cred = os.environ.get("TEST_S3_SECRET_ACCESS_KEY", "secret456")

    settings = S3Settings(
        S3_AWS_ACCESS_KEY_ID=access_id,
        S3_AWS_SECRET_ACCESS_KEY=access_cred,
        S3_ENDPOINT_URL="https://minio.example.com",
        S3_REGION_NAME="eu-central-1",
        S3_BUCKET_NAME="my-bucket",
        S3_KEY_PREFIX="uploads/",
        S3_IS_PUBLIC=False,
    )
    cfg = S3Config.from_settings(settings)
    assert cfg.aws_access_key_id == access_id
    assert cfg.aws_secret_access_key == access_cred
    assert cfg.endpoint_url == "https://minio.example.com"
    assert cfg.region_name == "eu-central-1"
    assert cfg.service_name == "s3"
    assert cfg.bucket_name == "my-bucket"
    assert cfg.key_prefix == "uploads/"
    assert cfg.is_public is False
