"""axiom.cache.key_maker — Pluggable cache key generation."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class KeyMaker(ABC):
    """Abstract base class for cache key generation strategies."""

    @abstractmethod
    def make_key(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Generate a unique cache key for the function call."""

    @abstractmethod
    def make_mask_key(self, function: Callable[..., Any]) -> str:
        """Generate a wildcard pattern key for the function (used for invalidation)."""

    @abstractmethod
    def make_function_param(self, name: str, value: Any) -> str:
        """Format a single function parameter as a string for inclusion in a key."""


__all__ = ["KeyMaker"]
