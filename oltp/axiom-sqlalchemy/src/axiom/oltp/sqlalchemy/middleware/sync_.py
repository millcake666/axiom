"""axiom.oltp.sqlalchemy.middleware.sync_ — Sync middleware for SQLAlchemy session scoping."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from axiom.oltp.sqlalchemy.postgres.context import reset_session_context, set_session_context


class SyncSQLAlchemyMiddleware(BaseHTTPMiddleware):
    """BaseHTTPMiddleware that scopes a sync SQLAlchemy session to each request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        """Handle a request with a scoped session context.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.

        Returns:
            HTTP response.
        """
        session_id = str(uuid.uuid4())
        token = set_session_context(session_id)
        try:
            response: Response = await call_next(request)
            return response
        finally:
            reset_session_context(token)
