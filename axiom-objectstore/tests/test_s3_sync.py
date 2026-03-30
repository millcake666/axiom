"""Tests for axiom.objectstore.s3.sync — SyncS3ObjectStore."""

import os
from unittest.mock import MagicMock, patch

import pytest

from axiom.objectstore.s3 import S3Config, SyncS3ObjectStore
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
    )


@pytest.fixture()
def store(config: S3Config) -> SyncS3ObjectStore:
    """Return a SyncS3ObjectStore for tests."""
    return SyncS3ObjectStore(config)


def _make_client_error(code: str) -> MagicMock:
    """Build a fake botocore ClientError with the given error code."""
    from botocore.exceptions import ClientError  # type: ignore[import-untyped]

    error_response = {"Error": {"Code": code, "Message": "test"}}
    return ClientError(error_response, "operation")


def _make_mock_boto3_client() -> MagicMock:
    """Return a MagicMock shaped like a boto3 client."""
    return MagicMock()


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


def test_upload_returns_key(store: SyncS3ObjectStore) -> None:
    """upload with explicit name returns that name."""
    mock_client = _make_mock_boto3_client()
    with patch.object(store, "_get_client", return_value=mock_client):
        key = store.upload(b"data", name="file.bin")
    assert key == "file.bin"
    mock_client.put_object.assert_called_once()


def test_upload_generates_key_when_name_none(store: SyncS3ObjectStore) -> None:
    """upload without name generates a unique hex key."""
    mock_client = _make_mock_boto3_client()
    with patch.object(store, "_get_client", return_value=mock_client):
        key = store.upload(b"data")
    assert len(key) == 32  # token_hex(16)


def test_upload_raises_internal_error_on_client_error(store: SyncS3ObjectStore) -> None:
    """upload wraps ClientError in S3InternalError."""
    err = _make_client_error("InternalError")
    mock_client = _make_mock_boto3_client()
    mock_client.put_object.side_effect = err
    with patch.object(store, "_get_client", return_value=mock_client):
        with pytest.raises(S3InternalError):
            store.upload(b"data", name="file.bin")


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_returns_bytes(store: SyncS3ObjectStore) -> None:
    """get returns raw bytes from S3."""
    body_mock = MagicMock()
    body_mock.read.return_value = b"hello"
    mock_client = _make_mock_boto3_client()
    mock_client.get_object.return_value = {"Body": body_mock}
    with patch.object(store, "_get_client", return_value=mock_client):
        result = store.get("file.bin")
    assert result == b"hello"


def test_get_raises_not_found_on_no_such_key(store: SyncS3ObjectStore) -> None:
    """get raises S3ObjectNotFoundError for NoSuchKey."""
    err = _make_client_error("NoSuchKey")
    mock_client = _make_mock_boto3_client()
    mock_client.get_object.side_effect = err
    with patch.object(store, "_get_client", return_value=mock_client):
        with pytest.raises(S3ObjectNotFoundError):
            store.get("missing")


def test_get_raises_internal_error_on_other_error(store: SyncS3ObjectStore) -> None:
    """get wraps unexpected ClientError in S3InternalError."""
    err = _make_client_error("AccessDenied")
    mock_client = _make_mock_boto3_client()
    mock_client.get_object.side_effect = err
    with patch.object(store, "_get_client", return_value=mock_client):
        with pytest.raises(S3InternalError):
            store.get("file")


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------


def test_exists_returns_true(store: SyncS3ObjectStore) -> None:
    """exists returns True when head_object succeeds."""
    mock_client = _make_mock_boto3_client()
    with patch.object(store, "_get_client", return_value=mock_client):
        assert store.exists("file") is True


def test_exists_returns_false_on_404(store: SyncS3ObjectStore) -> None:
    """exists returns False when head_object raises 404."""
    err = _make_client_error("404")
    mock_client = _make_mock_boto3_client()
    mock_client.head_object.side_effect = err
    with patch.object(store, "_get_client", return_value=mock_client):
        assert store.exists("missing") is False


def test_exists_raises_internal_error_on_other_error(store: SyncS3ObjectStore) -> None:
    """exists raises S3InternalError for unexpected errors."""
    err = _make_client_error("ServiceUnavailable")
    mock_client = _make_mock_boto3_client()
    mock_client.head_object.side_effect = err
    with patch.object(store, "_get_client", return_value=mock_client):
        with pytest.raises(S3InternalError):
            store.exists("file")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_calls_delete_object(store: SyncS3ObjectStore) -> None:
    """delete calls delete_object when object exists."""
    mock_client = _make_mock_boto3_client()
    with patch.object(store, "_get_client", return_value=mock_client):
        store.delete("file.bin")
    mock_client.delete_object.assert_called_once()


def test_delete_raises_not_found_when_missing(store: SyncS3ObjectStore) -> None:
    """delete raises S3ObjectNotFoundError when object doesn't exist."""
    with patch.object(store, "exists", return_value=False):
        with pytest.raises(S3ObjectNotFoundError):
            store.delete("missing")


# ---------------------------------------------------------------------------
# get_url
# ---------------------------------------------------------------------------


def test_get_url_returns_public_url(store: SyncS3ObjectStore) -> None:
    """get_url constructs the public URL from endpoint + bucket + key."""
    url = store.get_url("file.bin")
    assert url == "https://s3.example.com/test-bucket/file.bin"


# ---------------------------------------------------------------------------
# get_presigned_url
# ---------------------------------------------------------------------------


def test_get_presigned_url_returns_url(store: SyncS3ObjectStore) -> None:
    """get_presigned_url returns the generated presigned URL."""
    mock_client = _make_mock_boto3_client()
    mock_client.generate_presigned_url.return_value = "https://signed.example.com/obj"
    with patch.object(store, "_get_client", return_value=mock_client):
        url = store.get_presigned_url("file.bin")
    assert url == "https://signed.example.com/obj"


def test_get_presigned_url_raises_internal_error_on_failure(store: SyncS3ObjectStore) -> None:
    """get_presigned_url wraps ClientError in S3InternalError."""
    err = _make_client_error("InternalError")
    mock_client = _make_mock_boto3_client()
    mock_client.generate_presigned_url.side_effect = err
    with patch.object(store, "_get_client", return_value=mock_client):
        with pytest.raises(S3InternalError):
            store.get_presigned_url("file")
