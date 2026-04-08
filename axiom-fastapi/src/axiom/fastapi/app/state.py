"""axiom.fastapi.app.state — Typed accessor for FastAPI app.state."""

from typing import Any, TypeVar, cast

__all__ = [
    "AppStateManager",
]

T = TypeVar("T")


class AppStateManager:
    """Typed accessor for FastAPI application state.

    Provides a consistent, type-safe API for storing and retrieving values from
    ``app.state``. Reusable across any sub-system (rate limiter, cache, tracer, etc.)
    that attaches its own state to the application.

    Example::

        def get_rate_limiter(request: Request) -> RateLimiterService:
            return AppStateManager(request.app).get("rate_limiter", RateLimiterService)
    """

    def __init__(self, app: object) -> None:
        """Initialize with a FastAPI application instance.

        Args:
            app: FastAPI application (or any object with a ``state`` attribute).
        """
        self._app = app

    def set(self, key: str, value: Any) -> None:
        """Store a value in ``app.state`` under the given key.

        Args:
            key: Attribute name on ``app.state``.
            value: Value to store.
        """
        setattr(self._app.state, key, value)  # type: ignore[attr-defined]

    def get(self, key: str, typ: type[T]) -> T:
        """Retrieve and type-cast a value from ``app.state``.

        Args:
            key: Attribute name on ``app.state``.
            typ: Expected type. Used for static type-checker cast only — no runtime
                 validation is performed.

        Returns:
            The stored value cast to ``typ``.

        Raises:
            RuntimeError: If the key is absent or set to ``None``.
        """
        value = getattr(self._app.state, key, None)  # type: ignore[attr-defined]
        if value is None:
            raise RuntimeError(
                f"'{key}' is not initialized in app.state. "
                "Ensure the component is set up before the first request "
                "(e.g. inside a lifespan context manager).",
            )
        return cast(T, value)
