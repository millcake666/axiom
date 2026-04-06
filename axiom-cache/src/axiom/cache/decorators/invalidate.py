"""axiom.cache.decorators.invalidate — @invalidate decorator for cache invalidation."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any

from axiom.cache.base import AsyncCacheBackend, SyncCacheBackend
from axiom.cache.key_maker import KeyMaker
from axiom.cache.key_maker.function_key_maker import FunctionKeyMaker
from axiom.cache.schemas import CacheInvalidateParams


def _get_nested_attr(obj: Any, path: str) -> Any:
    """Traverse a dotted attribute path on obj."""
    for part in path.split("."):
        if hasattr(obj, part):
            obj = getattr(obj, part, None)
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def invalidate(
    *invalidate_params: CacheInvalidateParams,
    backend: AsyncCacheBackend | SyncCacheBackend,
    key_maker: KeyMaker | None = None,
) -> Callable[..., Any]:
    """Decorator that invalidates cached entries after the decorated function runs."""
    _key_maker = key_maker or FunctionKeyMaker(project_name="")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = await func(*args, **kwargs)
                if not isinstance(backend, AsyncCacheBackend):
                    raise TypeError(
                        f"Expected AsyncCacheBackend for async function, got {type(backend).__name__}",
                    )
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for inv_param in invalidate_params:
                    for cache_func in inv_param.functions:
                        mask = _key_maker.make_mask_key(cache_func)
                        param_strings: list[str] | None = None
                        if inv_param.params:
                            param_strings = []
                            for cp in inv_param.params:
                                arg_val = bound.arguments.get(cp.wrapped_func_param)
                                param_name = cp.caching_func_param or cp.wrapped_func_param
                                if "." in param_name:
                                    val = _get_nested_attr(
                                        arg_val,
                                        param_name.split(".", 1)[1],
                                    )
                                    short_name = param_name.split(".")[-1]
                                else:
                                    val = arg_val
                                    short_name = param_name
                                param_strings.append(
                                    _key_maker.make_function_param(short_name, val),
                                )
                        await backend.delete_by_pattern(mask, param_strings)
                return result

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                result = func(*args, **kwargs)
                if not isinstance(backend, SyncCacheBackend):
                    raise TypeError(
                        f"Expected SyncCacheBackend for sync function, got {type(backend).__name__}",
                    )
                sig = inspect.signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                for inv_param in invalidate_params:
                    for cache_func in inv_param.functions:
                        mask = _key_maker.make_mask_key(cache_func)
                        param_strings: list[str] | None = None
                        if inv_param.params:
                            param_strings = []
                            for cp in inv_param.params:
                                arg_val = bound.arguments.get(cp.wrapped_func_param)
                                param_name = cp.caching_func_param or cp.wrapped_func_param
                                val = arg_val
                                param_strings.append(
                                    _key_maker.make_function_param(param_name, val),
                                )
                        backend.delete_by_pattern(mask, param_strings)
                return result

            return sync_wrapper

    return decorator
