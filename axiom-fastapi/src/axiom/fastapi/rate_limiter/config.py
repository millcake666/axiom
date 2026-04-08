"""axiom.fastapi.rate_limiter.config — Settings and configuration for rate limiting."""

from pydantic import BaseModel, ConfigDict

from axiom.core.settings.base import BaseAppSettings
from axiom.fastapi.rate_limiter.core.algorithm import FailureStrategy
from axiom.fastapi.rate_limiter.core.policy import PolicyGroup, RateLimitPolicy

__all__ = [
    "RateLimitConfig",
    "RateLimitSettings",
]


class RateLimitSettings(BaseAppSettings):
    """Environment-driven settings for rate limiting (loaded from env vars)."""

    RATE_LIMIT_BACKEND: str = "memory"
    RATE_LIMIT_DEFAULT_LIMIT: str = "1000/min"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_ENV: str = "default"
    RATE_LIMIT_EXEMPT_PATHS: list[str] = []
    RATE_LIMIT_FAILURE_STRATEGY: str = "fail_open"
    RATE_LIMIT_KEY_PREFIX: str = "rl"


class RateLimitConfig(BaseModel):
    """Programmatic configuration object for rate limiting.

    Constructed directly in application code or via ``from_settings()``.
    Pass to ``rate_limiter_lifespan()`` or ``setup_rate_limiter()``.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    enabled: bool = True
    env: str = "default"
    exempt_paths: set[str] = set()
    failure_strategy: FailureStrategy = FailureStrategy.FAIL_OPEN
    key_prefix: str = "rl"
    policies: list[RateLimitPolicy | PolicyGroup] = []

    @classmethod
    def from_settings(cls, settings: RateLimitSettings) -> "RateLimitConfig":
        """Create a RateLimitConfig from RateLimitSettings.

        Args:
            settings: Populated RateLimitSettings instance.

        Returns:
            RateLimitConfig with values from the settings object.
        """
        return cls(
            enabled=settings.RATE_LIMIT_ENABLED,
            env=settings.RATE_LIMIT_ENV,
            exempt_paths=set(settings.RATE_LIMIT_EXEMPT_PATHS),
            failure_strategy=FailureStrategy(settings.RATE_LIMIT_FAILURE_STRATEGY),
            key_prefix=settings.RATE_LIMIT_KEY_PREFIX,
            policies=[],
        )
