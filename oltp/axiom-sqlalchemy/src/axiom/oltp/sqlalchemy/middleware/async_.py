"""axiom.oltp.sqlalchemy.middleware.async_ — Async ASGI middleware for SQLAlchemy session scoping."""

import uuid
from typing import Any

from axiom.oltp.sqlalchemy.postgres.context import reset_session_context, set_session_context


class AsyncSQLAlchemyMiddleware:
    """Raw ASGI middleware that scopes an async SQLAlchemy session to each request."""

    def __init__(self, app: Any) -> None:
        """Initialize AsyncSQLAlchemyMiddleware.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Handle an ASGI request with a scoped session context.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive channel.
            send: ASGI send channel.
        """
        if scope["type"] not in ("http", "https"):
            await self.app(scope, receive, send)
            return

        session_id = str(uuid.uuid4())
        token = set_session_context(session_id)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_session_context(token)
