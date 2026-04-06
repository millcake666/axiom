"""axiom.cache.base — Abstract cache backend interfaces."""

from abc import ABC, abstractmethod
from typing import Any


class AsyncCacheBackend(ABC):
    """Abstract base class for async cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Retrieve a value by key. Returns None if not found."""

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value under key, optionally expiring after ttl seconds."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a single key."""

    @abstractmethod
    async def delete_by_pattern(self, pattern: str, params: list[str] | None = None) -> None:
        """Remove keys matching pattern, optionally filtered by param substrings."""

    @abstractmethod
    async def delete_all(self) -> None:
        """Remove all keys from the backend."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True if the key exists."""


class SyncCacheBackend(ABC):
    """Abstract base class for synchronous cache backends."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Retrieve a value by key. Returns None if not found."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value under key, optionally expiring after ttl seconds."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove a single key."""

    @abstractmethod
    def delete_by_pattern(self, pattern: str, params: list[str] | None = None) -> None:
        """Remove keys matching pattern, optionally filtered by param substrings."""

    @abstractmethod
    def delete_all(self) -> None:
        """Remove all keys from the backend."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if the key exists."""


__all__ = ["AsyncCacheBackend", "SyncCacheBackend"]
