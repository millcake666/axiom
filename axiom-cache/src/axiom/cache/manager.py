"""axiom.cache.manager — CacheManager bundles backend + key_maker."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axiom.cache.base import AsyncCacheBackend, SyncCacheBackend
from axiom.cache.decorators.cached import cached
from axiom.cache.decorators.invalidate import invalidate
from axiom.cache.key_maker import KeyMaker
from axiom.cache.key_maker.function_key_maker import FunctionKeyMaker
from axiom.cache.schemas import CacheInvalidateParams


class CacheManager:
    """Bundles a cache backend and key maker, providing decorator factories."""

    def __init__(
        self,
        backend: AsyncCacheBackend | SyncCacheBackend,
        key_maker: KeyMaker | None = None,
        default_ttl: int = 0,
    ) -> None:
        """Initialize with a backend, optional key maker, and default TTL."""
        self._backend = backend
        self._key_maker = key_maker or FunctionKeyMaker()
        self._default_ttl = default_ttl

    def cached(self, ttl: int | None = None) -> Callable[..., Any]:
        """Return a @cached decorator configured with this manager's settings."""
        return cached(
            self._backend,
            ttl=ttl if ttl is not None else self._default_ttl,
            key_maker=self._key_maker,
        )

    def invalidate(self, *params: CacheInvalidateParams) -> Callable[..., Any]:
        """Return an @invalidate decorator configured with this manager's settings."""
        return invalidate(*params, backend=self._backend, key_maker=self._key_maker)
