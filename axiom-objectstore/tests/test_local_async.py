"""Tests for axiom.objectstore.local.async_ — AsyncLocalDiskObjectStore."""

from pathlib import Path

import pytest

from axiom.objectstore.local import AsyncLocalDiskObjectStore, LocalDiskConfig
from axiom.objectstore.local.exception import LocalObjectNotFoundError


@pytest.fixture()
def config(tmp_path: Path) -> LocalDiskConfig:
    """Return a LocalDiskConfig backed by a temp directory."""
    return LocalDiskConfig(base_dir=tmp_path / "store")


@pytest.fixture()
def store(config: LocalDiskConfig) -> AsyncLocalDiskObjectStore:
    """Return an AsyncLocalDiskObjectStore for tests."""
    return AsyncLocalDiskObjectStore(config)


# ---------------------------------------------------------------------------
# upload
# ---------------------------------------------------------------------------


async def test_upload_returns_explicit_key(store: AsyncLocalDiskObjectStore) -> None:
    """upload with name returns that name and writes the file."""
    key = await store.upload(b"hello", name="myfile.bin")
    assert key == "myfile.bin"
    assert (store._config.base_dir / "myfile.bin").read_bytes() == b"hello"


async def test_upload_generates_unique_key(store: AsyncLocalDiskObjectStore) -> None:
    """upload without name generates a unique hex key."""
    key1 = await store.upload(b"a")
    key2 = await store.upload(b"b")
    assert len(key1) == 32
    assert key1 != key2


async def test_upload_overwrites_existing_file(store: AsyncLocalDiskObjectStore) -> None:
    """upload with same explicit name overwrites existing content."""
    await store.upload(b"first", name="f.bin")
    await store.upload(b"second", name="f.bin")
    assert (store._config.base_dir / "f.bin").read_bytes() == b"second"


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


async def test_get_returns_bytes(store: AsyncLocalDiskObjectStore) -> None:
    """get returns previously uploaded bytes."""
    await store.upload(b"content", name="f.bin")
    assert await store.get("f.bin") == b"content"


async def test_get_raises_not_found_when_missing(store: AsyncLocalDiskObjectStore) -> None:
    """get raises LocalObjectNotFoundError when file doesn't exist."""
    with pytest.raises(LocalObjectNotFoundError):
        await store.get("nonexistent")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


async def test_delete_removes_file(store: AsyncLocalDiskObjectStore) -> None:
    """delete removes the file from disk."""
    await store.upload(b"data", name="del.bin")
    await store.delete("del.bin")
    assert not (store._config.base_dir / "del.bin").exists()


async def test_delete_raises_not_found_when_missing(store: AsyncLocalDiskObjectStore) -> None:
    """delete raises LocalObjectNotFoundError when file doesn't exist."""
    with pytest.raises(LocalObjectNotFoundError):
        await store.delete("nonexistent")


# ---------------------------------------------------------------------------
# exists
# ---------------------------------------------------------------------------


async def test_exists_returns_true(store: AsyncLocalDiskObjectStore) -> None:
    """exists returns True after upload."""
    await store.upload(b"x", name="e.bin")
    assert await store.exists("e.bin") is True


async def test_exists_returns_false_when_missing(store: AsyncLocalDiskObjectStore) -> None:
    """exists returns False when file doesn't exist."""
    assert await store.exists("missing") is False


# ---------------------------------------------------------------------------
# get_url
# ---------------------------------------------------------------------------


async def test_get_url_with_base_url(tmp_path: Path) -> None:
    """get_url uses base_url when configured."""
    config = LocalDiskConfig(base_dir=tmp_path, base_url="https://cdn.example.com")
    store = AsyncLocalDiskObjectStore(config)
    url = await store.get_url("img/photo.jpg")
    assert url == "https://cdn.example.com/img/photo.jpg"


async def test_get_url_without_base_url(store: AsyncLocalDiskObjectStore) -> None:
    """get_url returns file:// URL when base_url not set."""
    url = await store.get_url("f.bin")
    assert url.startswith("file://")
    assert "f.bin" in url
