"""axiom.objectstore.abs — Abstract interfaces for object storage clients."""

from abc import ABC, abstractmethod


class AbstractAsyncObjectStore(ABC):
    """Abstract base class for async object storage clients."""

    @abstractmethod
    async def upload(
        self,
        data: bytes,
        name: str | None = None,
        content_disposition: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload an object to the store and return its key/name.

        Args:
            data: Raw bytes to upload.
            name: Optional explicit key; if omitted a unique name is generated.
            content_disposition: Optional Content-Disposition header value.
            content_type: MIME type of the object.

        Returns:
            The key/name under which the object was stored.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def get(self, name: str) -> bytes:
        """Download an object by its key.

        Args:
            name: Key of the object to retrieve.

        Returns:
            Raw bytes of the stored object.

        Raises:
            ObjectNotFoundError: If no object exists with the given key.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def delete(self, name: str) -> None:
        """Delete an object by its key.

        Args:
            name: Key of the object to delete.

        Raises:
            ObjectNotFoundError: If no object exists with the given key.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def exists(self, name: str) -> bool:
        """Check whether an object exists.

        Args:
            name: Key of the object to check.

        Returns:
            ``True`` if the object exists, ``False`` otherwise.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    async def get_url(self, name: str) -> str:
        """Return the public URL for an object.

        Args:
            name: Key of the object.

        Returns:
            Public URL string pointing to the object.
        """
        raise NotImplementedError  # pragma: no cover


class AbstractSyncObjectStore(ABC):
    """Abstract base class for synchronous object storage clients."""

    @abstractmethod
    def upload(
        self,
        data: bytes,
        name: str | None = None,
        content_disposition: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload an object to the store and return its key/name.

        Args:
            data: Raw bytes to upload.
            name: Optional explicit key; if omitted a unique name is generated.
            content_disposition: Optional Content-Disposition header value.
            content_type: MIME type of the object.

        Returns:
            The key/name under which the object was stored.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get(self, name: str) -> bytes:
        """Download an object by its key.

        Args:
            name: Key of the object to retrieve.

        Returns:
            Raw bytes of the stored object.

        Raises:
            ObjectNotFoundError: If no object exists with the given key.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def delete(self, name: str) -> None:
        """Delete an object by its key.

        Args:
            name: Key of the object to delete.

        Raises:
            ObjectNotFoundError: If no object exists with the given key.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check whether an object exists.

        Args:
            name: Key of the object to check.

        Returns:
            ``True`` if the object exists, ``False`` otherwise.
        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get_url(self, name: str) -> str:
        """Return the public URL for an object.

        Args:
            name: Key of the object.

        Returns:
            Public URL string pointing to the object.
        """
        raise NotImplementedError  # pragma: no cover
