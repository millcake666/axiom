"""axiom.cache.exception — Exceptions for the axiom.cache package."""


class AxiomCacheError(Exception):
    """Base exception for axiom.cache."""


class CacheError(AxiomCacheError):
    """General cache error."""


class CacheConnectionError(AxiomCacheError):
    """Raised when a connection to the cache backend fails."""


class CacheKeyError(AxiomCacheError):
    """Raised when a cache key is invalid or not found."""


class CacheSerializationError(AxiomCacheError):
    """Raised when serialization or deserialization of a cached value fails."""


class CacheNotInitializedError(AxiomCacheError):
    """Raised when the cache backend is used before being initialized."""
