"""axiom.core.context.request — Per-request context dataclass and helpers."""

from contextvars import Token
from dataclasses import dataclass, field
from typing import Any

from axiom.core.context.var import TypedContextVar


class BaseContext:
    """Abstract base for typed context objects propagated via ContextVar."""


@dataclass
class RequestContext(BaseContext):
    """Per-request context carrying request ID, user, tenant, and extras."""

    request_id: str
    user: Any | None = None
    tenant: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


REQUEST_CONTEXT: TypedContextVar[RequestContext] = TypedContextVar(
    "request_context",
    RequestContext,
)


def set_request_context(
    request_id: str,
    user: Any | None = None,
    tenant: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Token[RequestContext]:
    """Populate REQUEST_CONTEXT for the current async context and return a reset token.

    Args:
        request_id: Unique identifier for the request.
        user: Authenticated user object, or None.
        tenant: Tenant identifier, or None.
        extra: Additional key-value pairs to attach to the context.

    Returns:
        Token that can be passed to REQUEST_CONTEXT.reset() to restore the
        previous context value.
    """
    ctx = RequestContext(
        request_id=request_id,
        user=user,
        tenant=tenant,
        extra=extra or {},
    )
    return REQUEST_CONTEXT.set(ctx)
