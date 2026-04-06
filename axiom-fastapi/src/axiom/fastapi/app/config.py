"""axiom.fastapi.app.config — AppConfig for create_app()."""

from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, model_validator


class AppConfig(BaseModel):
    """Configuration for create_app().

    If pyproject_path is set and title/version/description are not provided,
    they are auto-filled from the pyproject.toml via ProjectInfo.
    """

    title: str | None = None
    version: str | None = None
    description: str | None = None
    pyproject_path: str | Path | None = None
    debug: bool = False
    docs_url: str | None = "/docs"
    redoc_url: str | None = "/redoc"
    openapi_url: str | None = "/openapi.json"
    middleware: list[Any] = []
    exception_handlers: dict[type[Exception], Callable[..., Any]] = {}
    register_default_handlers: bool = True
    docs_config: Any | None = None  # DocsConfig | None

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def _fill_from_pyproject(self) -> "AppConfig":
        if self.pyproject_path is not None:
            from axiom.core.project.info import ProjectInfo

            info = ProjectInfo(self.pyproject_path)
            if self.title is None:
                self.title = info.get_name()
            if self.version is None:
                self.version = info.get_version()
            if self.description is None:
                self.description = info.get_description()
        return self
