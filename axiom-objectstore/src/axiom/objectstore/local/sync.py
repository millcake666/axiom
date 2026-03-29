"""axiom.objectstore.local.sync — Synchronous local disk object storage client."""

from pathlib import Path
from secrets import token_hex

from loguru import logger

from axiom.objectstore.abs import AbstractSyncObjectStore
from axiom.objectstore.local.config import LocalDiskConfig
from axiom.objectstore.local.exception import LocalObjectNotFoundError


class SyncLocalDiskObjectStore(AbstractSyncObjectStore):
    """Synchronous local disk object storage client.

    Args:
        config: Local disk storage configuration.
    """

    def __init__(self, config: LocalDiskConfig) -> None:
        """Initialise the sync local disk client.

        Args:
            config: Local disk storage configuration.
        """
        self._config = config
        self._config.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        """Resolve the full filesystem path for an object key.

        Args:
            name: Object key.

        Returns:
            Absolute :class:`Path` for the object.
        """
        return self._config.base_dir / name

    def _make_key(self, name: str | None) -> str:
        """Return a storage key, generating a unique one when *name* is omitted.

        Args:
            name: Explicit key, or ``None`` to generate a random hex key.

        Returns:
            The resolved storage key.
        """
        return name if name is not None else token_hex(16)

    def upload(
        self,
        data: bytes,
        name: str | None = None,
        content_disposition: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Write bytes to disk and return the stored key.

        Args:
            data: Raw bytes to store.
            name: Optional explicit key; if omitted a unique name is generated.
            content_disposition: Ignored for local storage (kept for interface compatibility).
            content_type: Ignored for local storage (kept for interface compatibility).

        Returns:
            The key under which the object was stored.
        """
        key = self._make_key(name)
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.info("LocalDisk upload succeeded: key={} size={}", key, len(data))
        return key

    def get(self, name: str) -> bytes:
        """Read an object from disk by key.

        Args:
            name: Key of the object to retrieve.

        Returns:
            Raw bytes of the stored object.

        Raises:
            LocalObjectNotFoundError: If no object exists with the given key.
        """
        path = self._path(name)
        if not path.exists():
            raise LocalObjectNotFoundError(f"Object not found: {name}")
        return path.read_bytes()

    def delete(self, name: str) -> None:
        """Delete an object from disk.

        Args:
            name: Key of the object to delete.

        Raises:
            LocalObjectNotFoundError: If no object exists with the given key.
        """
        path = self._path(name)
        if not path.exists():
            raise LocalObjectNotFoundError(f"Object not found: {name}")
        path.unlink()
        logger.info("LocalDisk delete succeeded: key={}", name)

    def exists(self, name: str) -> bool:
        """Check whether an object exists on disk.

        Args:
            name: Key of the object to check.

        Returns:
            ``True`` if the object exists, ``False`` otherwise.
        """
        return self._path(name).exists()

    def get_url(self, name: str) -> str:
        """Return a URL for the object.

        Args:
            name: Key of the object.

        Returns:
            ``{base_url}/{name}`` when *base_url* is configured, otherwise
            a ``file://`` URL pointing to the absolute path.
        """
        if self._config.base_url:
            base = self._config.base_url.rstrip("/")
            return f"{base}/{name}"
        return self._path(name).as_uri()
