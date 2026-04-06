"""axiom.fastapi.middleware.error.middleware — Catch-all ASGI error middleware."""

from __future__ import annotations

import json
from typing import Any

import structlog

from axiom.core.exceptions.base import ErrorDetail

logger = structlog.get_logger(__name__)


class ErrorMiddleware:
    """Raw ASGI middleware that catches all unhandled exceptions and returns 500."""

    def __init__(self, app: Any) -> None:
        """Initialize ErrorMiddleware.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Handle an ASGI request, catching any unhandled exceptions.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive channel.
            send: ASGI send channel.
        """
        if scope["type"] not in ("http", "https"):
            await self.app(scope, receive, send)
            return

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            logger.exception("unhandled_exception", exc_info=exc)
            detail = ErrorDetail(
                code="internal_error",
                message="An unexpected error occurred.",
                details={},
            )
            body = json.dumps(detail.model_dump()).encode()
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"content-length", str(len(body)).encode()),
                    ],
                },
            )
            await send({"type": "http.response.body", "body": body})
