"""axiom.core.settings.base — Base settings class and composable mixins."""

from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    """Base settings class for all axiom services."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppMixin(BaseModel):
    """Mixin with common application settings."""

    APP_HOST: str = "0.0.0.0"  # noqa: S104  # nosec B104
    APP_PORT: int = 8000
    APP_STAGE: Literal["dev", "staging", "prod"] = "dev"
    APP_NAME: str = "app"


class DebugMixin(BaseModel):
    """Mixin for debug mode toggle."""

    DEBUG: bool = False


def make_env_prefix(name: str) -> str:
    """Convert app name to env prefix: 'my-service' -> 'MY_SERVICE_'."""
    return name.upper().replace("-", "_").replace(" ", "_") + "_"
