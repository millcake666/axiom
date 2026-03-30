"""axiom.cache.schemas — Pydantic schemas for cache invalidation parameters."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict


class ConvertParam(BaseModel):
    """Maps a wrapped function parameter to a caching function parameter."""

    wrapped_func_param: str
    caching_func_param: str | None = None


class CacheInvalidateParams(BaseModel):
    """Parameters for cache invalidation, linking functions with their param mappings."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    functions: list[Callable[..., Any]]
    params: list[ConvertParam] | None = None
