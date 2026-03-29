"""Tests for axiom.objectstore.abs — abstract interface contract."""

import pytest

from axiom.objectstore.abs import AbstractAsyncObjectStore, AbstractSyncObjectStore


class _ConcreteAsync(AbstractAsyncObjectStore):
    """Minimal concrete async implementation for testing."""

    async def upload(
        self,
        data: bytes,
        name: str | None = None,
        content_disposition: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        return name or "test-key"

    async def get(self, name: str) -> bytes:
        return b"data"

    async def delete(self, name: str) -> None:
        return None

    async def exists(self, name: str) -> bool:
        return True

    async def get_url(self, name: str) -> str:
        return f"https://example.com/{name}"


class _ConcreteSync(AbstractSyncObjectStore):
    """Minimal concrete sync implementation for testing."""

    def upload(
        self,
        data: bytes,
        name: str | None = None,
        content_disposition: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        return name or "test-key"

    def get(self, name: str) -> bytes:
        return b"data"

    def delete(self, name: str) -> None:
        return None

    def exists(self, name: str) -> bool:
        return True

    def get_url(self, name: str) -> str:
        return f"https://example.com/{name}"


def test_abstract_async_cannot_be_instantiated() -> None:
    """AbstractAsyncObjectStore must not be instantiable directly."""
    with pytest.raises(TypeError):
        AbstractAsyncObjectStore()  # type: ignore[abstract]


def test_abstract_sync_cannot_be_instantiated() -> None:
    """AbstractSyncObjectStore must not be instantiable directly."""
    with pytest.raises(TypeError):
        AbstractSyncObjectStore()  # type: ignore[abstract]


@pytest.mark.asyncio
async def test_concrete_async_upload_with_name() -> None:
    store = _ConcreteAsync()
    key = await store.upload(b"hello", name="my-file.bin")
    assert key == "my-file.bin"


@pytest.mark.asyncio
async def test_concrete_async_upload_without_name() -> None:
    store = _ConcreteAsync()
    key = await store.upload(b"hello")
    assert key == "test-key"


@pytest.mark.asyncio
async def test_concrete_async_get() -> None:
    store = _ConcreteAsync()
    data = await store.get("some-key")
    assert data == b"data"


@pytest.mark.asyncio
async def test_concrete_async_delete() -> None:
    store = _ConcreteAsync()
    result = await store.delete("some-key")
    assert result is None


@pytest.mark.asyncio
async def test_concrete_async_exists() -> None:
    store = _ConcreteAsync()
    assert await store.exists("some-key") is True


@pytest.mark.asyncio
async def test_concrete_async_get_url() -> None:
    store = _ConcreteAsync()
    url = await store.get_url("my-file.bin")
    assert url == "https://example.com/my-file.bin"


def test_concrete_sync_upload_with_name() -> None:
    store = _ConcreteSync()
    key = store.upload(b"hello", name="my-file.bin")
    assert key == "my-file.bin"


def test_concrete_sync_upload_without_name() -> None:
    store = _ConcreteSync()
    key = store.upload(b"hello")
    assert key == "test-key"


def test_concrete_sync_get() -> None:
    store = _ConcreteSync()
    data = store.get("some-key")
    assert data == b"data"


def test_concrete_sync_delete() -> None:
    store = _ConcreteSync()
    result = store.delete("some-key")
    assert result is None


def test_concrete_sync_exists() -> None:
    store = _ConcreteSync()
    assert store.exists("some-key") is True


def test_concrete_sync_get_url() -> None:
    store = _ConcreteSync()
    url = store.get_url("my-file.bin")
    assert url == "https://example.com/my-file.bin"


def test_async_is_subclass_of_abc() -> None:
    from abc import ABC

    assert issubclass(AbstractAsyncObjectStore, ABC)


def test_sync_is_subclass_of_abc() -> None:
    from abc import ABC

    assert issubclass(AbstractSyncObjectStore, ABC)
