"""axiom.fastapi.middleware.logging.middleware — Request/response logging middleware."""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

from axiom.core.context.request import REQUEST_CONTEXT, set_request_context

logger = structlog.get_logger(__name__)

_DEFAULT_REQUEST_ID_HEADER = "X-Request-ID"


class RequestLoggingMiddleware:
    """Raw ASGI middleware that logs incoming requests and outgoing responses.

    Generates or forwards a request ID, sets REQUEST_CONTEXT, and logs
    method/path/status/timing via structlog.
    """

    def __init__(
        self,
        app: Any,
        *,
        request_id_header: str = _DEFAULT_REQUEST_ID_HEADER,
    ) -> None:
        """Initialize RequestLoggingMiddleware.

        Args:
            app: The ASGI application to wrap.
            request_id_header: Header name used to read/write the request ID.
        """
        self.app = app
        self.request_id_header = request_id_header

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        """Handle an ASGI request.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive channel.
            send: ASGI send channel.
        """
        if scope["type"] not in ("http", "https"):
            await self.app(scope, receive, send)
            return

        headers: dict[str, str] = {k.decode(): v.decode() for k, v in scope.get("headers", [])}

        # Resolve request ID
        request_id = headers.get(self.request_id_header.lower()) or str(uuid.uuid4())

        # Resolve client IP
        ip = (
            headers.get("x-forwarded-for")
            or headers.get("x-original-forwarded-for")
            or (scope.get("client") or (None, None))[0]
            or "unknown"
        )
        if "," in ip:
            ip = ip.split(",")[0].strip()

        token = set_request_context(request_id=request_id)
        start = time.perf_counter()

        method = scope.get("method", "")
        path = scope.get("path", "")
        query = scope.get("query_string", b"").decode()

        logger.info(
            "request.incoming",
            method=method,
            path=path,
            query=query,
            ip=ip,
            request_id=request_id,
        )

        status_code = 0
        response_size = 0

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code, response_size
            if message["type"] == "http.response.start":
                status_code = message["status"]
                raw_headers: list[Any] = list(message.get("headers", []))
                raw_headers.append(
                    (self.request_id_header.lower().encode(), request_id.encode()),
                )
                message = {**message, "headers": raw_headers}
            elif message["type"] == "http.response.body":
                response_size += len(message.get("body", b""))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - start
            logger.info(
                "request.outgoing",
                method=method,
                path=path,
                status_code=status_code,
                processing_time=round(elapsed, 4),
                response_size=response_size,
                request_id=request_id,
            )
            REQUEST_CONTEXT.reset(token)
