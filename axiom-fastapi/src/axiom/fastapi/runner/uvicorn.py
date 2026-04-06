"""axiom.fastapi.runner.uvicorn — Uvicorn runner for axiom FastAPI apps."""

from typing import TYPE_CHECKING, Any, Callable

import uvicorn
from pydantic import BaseModel

if TYPE_CHECKING:
    pass


class UvicornSettings(BaseModel):
    """Settings for the uvicorn runner."""

    host: str = "0.0.0.0"  # noqa: S104  # nosec B104
    port: int = 8000
    workers: int = 1
    reload: bool = False
    log_level: str = "info"
    factory: bool = False


def run_uvicorn(app: str | Callable[..., Any], settings: UvicornSettings) -> None:
    """Start the uvicorn server.

    Args:
        app: ASGI application or import string.
        settings: Uvicorn configuration.
    """
    uvicorn.run(
        app,  # type: ignore[arg-type]
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.reload,
        log_level=settings.log_level,
        factory=settings.factory,
    )
