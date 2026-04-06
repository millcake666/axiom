"""axiom.redis.settings — Redis connection settings."""

from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    """Settings for Redis connection configuration."""

    REDIS_URL: str = "redis://localhost:6379"
    REDIS_USE_CLUSTER: bool = False
    REDIS_MAX_CONNECTIONS: int | None = None
    REDIS_SOCKET_TIMEOUT: float | None = None
    REDIS_DECODE_RESPONSES: bool = False
