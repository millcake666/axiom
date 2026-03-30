"""axiom.redis.exception — Exceptions for the axiom.redis package."""


class AxiomRedisError(Exception):
    """Base exception for axiom.redis."""


class RedisConnectionError(AxiomRedisError):
    """Raised when a Redis connection fails."""


class RedisOperationError(AxiomRedisError):
    """Raised when a Redis operation fails."""


class RedisConfigurationError(AxiomRedisError):
    """Raised when Redis is misconfigured."""
