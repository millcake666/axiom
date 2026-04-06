"""axiom.fastapi.app — FastAPI application factory."""

from axiom.fastapi.app.builder import create_app
from axiom.fastapi.app.config import AppConfig

__all__ = ["AppConfig", "create_app"]
