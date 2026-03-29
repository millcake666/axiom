"""Tests for axiom.objectstore.local.sync — SyncLocalDiskObjectStore."""

from pathlib import Path

import pytest

from axiom.objectstore.local import LocalDiskConfig, SyncLocalDiskObjectStore
from axiom.objectstore.local.exception import LocalObjectNotFoundError


@pytest.fixture()
def config(tmp_path: Path) -> LocalDiskConfig:
    """Return a LocalDiskConfig backed by a temp directory."""
    return LocalDiskConfig(base_dir=tmp_path / "store")


@pytest.fixture()
def store(config: LocalDiskConfig) -> SyncLocalDiskObjectStore:
    """Return a SyncLocalDiskObjectStore for tests."""
    return SyncLocalDiskObjectStore(config)


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


def test_upload_returns_explicit_key(store: SyncLocalDiskObjectStore) -> None:
    """upload with name returns that name and writes the file."""
    key = store.upload(b"hello", name="myfile.bin")
    assert key == "myfile.bin"
    assert (store._config.base_dir / "myfile.bin").read_bytes() == b"hello"


def test_upload_generates_unique_key(store: SyncLocalDiskObjectStore) -> None:
    """upload without name generates a unique hex key."""
    key1 = store.upload(b"a")
    key2 = store.upload(b"b")
    assert len(key1) == 32
    assert key1 != key2


def test_upload_overwrites_existing_file(store: SyncLocalDiskObjectStore) -> None:
    """upload with same explicit name overwrites existing content."""
    store.upload(b"first", name="f.bin")
    store.upload(b"second", name="f.bin")
    assert (store._config.base_dir / "f.bin").read_bytes() == b"second"


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


def test_get_returns_bytes(store: SyncLocalDiskObjectStore) -> None:
    """get returns previously uploaded bytes."""
    store.upload(b"content", name="f.bin")
    assert store.get("f.bin") == b"content"


def test_get_raises_not_found_when_missing(store: SyncLocalDiskObjectStore) -> None:
    """get raises LocalObjectNotFoundError when file doesn't exist."""
    with pytest.raises(LocalObjectNotFoundError):
        store.get("nonexistent")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


def test_delete_removes_file(store: SyncLocalDiskObjectStore) -> None:
    """delete removes the file from disk."""
    store.upload(b"data", name="del.bin")
    store.delete("del.bin")
    assert not (store._config.base_dir / "del.bin").exists()


def test_delete_raises_not_found_when_missing(store: SyncLocalDiskObjectStore) -> None:
    """delete raises LocalObjectNotFoundError when file doesn't exist."""
    with pytest.raises(LocalObjectNotFoundError):
        store.delete("nonexistent")


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------


def test_exists_returns_true(store: SyncLocalDiskObjectStore) -> None:
    """exists returns True after upload."""
    store.upload(b"x", name="e.bin")
    assert store.exists("e.bin") is True


def test_exists_returns_false_when_missing(store: SyncLocalDiskObjectStore) -> None:
    """exists returns False when file doesn't exist."""
    assert store.exists("missing") is False


# ---------------------------------------------------------------------------
# get_url
# ---------------------------------------------------------------------------


def test_get_url_with_base_url(tmp_path: Path) -> None:
    """get_url uses base_url when configured."""
    config = LocalDiskConfig(base_dir=tmp_path, base_url="https://cdn.example.com")
    store = SyncLocalDiskObjectStore(config)
    url = store.get_url("img/photo.jpg")
    assert url == "https://cdn.example.com/img/photo.jpg"


def test_get_url_without_base_url(store: SyncLocalDiskObjectStore) -> None:
    """get_url returns file:// URL when base_url not set."""
    url = store.get_url("f.bin")
    assert url.startswith("file://")
    assert "f.bin" in url
