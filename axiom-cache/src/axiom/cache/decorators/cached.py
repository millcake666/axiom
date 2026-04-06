"""axiom.cache.decorators.cached — @cached decorator for function result caching."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from axiom.cache.base import AsyncCacheBackend, SyncCacheBackend
from axiom.cache.key_maker import KeyMaker
from axiom.cache.key_maker.function_key_maker import FunctionKeyMaker


def cached(
    backend: AsyncCacheBackend | SyncCacheBackend,
    ttl: int = 0,
    key_maker: KeyMaker | None = None,
) -> Callable[..., Any]:
    """Decorator that caches the return value of a function.

    Works with both async and sync functions. TTL of 0 means no expiry.
    """
    _key_maker = key_maker or FunctionKeyMaker(project_name="")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                key = _key_maker.make_key(func, *args, **kwargs)
                if not isinstance(backend, AsyncCacheBackend):
                    raise TypeError(
                        f"Expected AsyncCacheBackend for async function, got {type(backend).__name__}",
                    )
                cached_value = await backend.get(key)
                if cached_value is not None:
                    return cached_value
                result = await func(*args, **kwargs)
                await backend.set(key, result, ttl=ttl or None)
                return result

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                key = _key_maker.make_key(func, *args, **kwargs)
                if not isinstance(backend, SyncCacheBackend):
                    raise TypeError(
                        f"Expected SyncCacheBackend for sync function, got {type(backend).__name__}",
                    )
                cached_value = backend.get(key)
                if cached_value is not None:
                    return cached_value
                result = func(*args, **kwargs)
                backend.set(key, result, ttl=ttl or None)
                return result

            return sync_wrapper

    return decorator
