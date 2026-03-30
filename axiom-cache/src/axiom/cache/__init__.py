"""axiom.cache — Caching abstractions with in-memory and Redis backends."""

__version__ = "0.1.0"

from axiom.cache.base import AsyncCacheBackend, SyncCacheBackend
from axiom.cache.decorators.cached import cached
from axiom.cache.decorators.invalidate import invalidate
from axiom.cache.exception import (
    AxiomCacheError,
    CacheConnectionError,
    CacheError,
    CacheKeyError,
    CacheNotInitializedError,
    CacheSerializationError,
)
from axiom.cache.inmemory import AsyncInMemoryCache, SyncInMemoryCache
from axiom.cache.key_maker import KeyMaker
from axiom.cache.key_maker.function_key_maker import FunctionKeyMaker
from axiom.cache.manager import CacheManager
from axiom.cache.redis import AsyncRedisCache, SyncRedisCache
from axiom.cache.schemas import CacheInvalidateParams, ConvertParam
from axiom.cache.serialization import SerializationStrategy, SerializerType, get_serializer
from axiom.cache.ttl import TTL

__all__ = [
    "AsyncCacheBackend",
    "AsyncInMemoryCache",
    "AsyncRedisCache",
    "AxiomCacheError",
    "CacheConnectionError",
    "CacheError",
    "CacheInvalidateParams",
    "CacheKeyError",
    "CacheManager",
    "CacheNotInitializedError",
    "CacheSerializationError",
    "ConvertParam",
    "FunctionKeyMaker",
    "KeyMaker",
    "SerializationStrategy",
    "SerializerType",
    "SyncCacheBackend",
    "SyncInMemoryCache",
    "SyncRedisCache",
    "TTL",
    "cached",
    "get_serializer",
    "invalidate",
]
