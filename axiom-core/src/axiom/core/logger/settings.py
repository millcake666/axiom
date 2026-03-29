"""axiom.core.logger.settings — Logger configuration settings."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseSettings):
    """Settings for configuring the loguru logger."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text", "auto"] = "auto"
    LOG_OUTPUT: Literal["stderr", "stdout", "file"] = "stderr"
    LOG_FILE_PATH: str | None = None
    LOG_JSON_FIELDS: list[str] | None = None
    APP_STAGE: str = "dev"


_DEFAULT_JSON_FIELDS = [
    "timestamp",
    "level",
    "message",
    "logger_name",
    "module",
    "function",
    "line",
    "exception",
    "extra",
]
