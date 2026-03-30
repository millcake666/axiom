"""axiom.cache.key_maker.function_key_maker — Default function-based key generation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from axiom.cache.key_maker import KeyMaker


class FunctionKeyMaker(KeyMaker):
    """Generates cache keys based on function module, qualified name, and arguments."""

    def __init__(self, project_name: str = "") -> None:
        """Initialize with an optional project namespace prefix."""
        self._project_name = project_name

    def make_key(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> str:
        """Generate a unique key encoding function identity and call arguments."""
        params = []
        for arg in args:
            params.append(str(arg))
        for k, v in kwargs.items():
            params.append(f"{k}={v}")
        param_str = ", ".join(params)
        module = function.__module__
        name = function.__qualname__
        return f"{self._project_name}|({param_str})::{module}.{name}"

    def make_mask_key(self, function: Callable[..., Any]) -> str:
        """Generate a wildcard pattern key used for bulk invalidation."""
        module = function.__module__
        name = function.__qualname__
        return f"{self._project_name}|(*)::{module}.{name}"

    def make_function_param(self, name: str, value: Any) -> str:
        """Format a parameter as 'name=value' string."""
        return f"{name}={value}"
