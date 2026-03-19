"""axiom.core.context — Per-request context propagation via ContextVar."""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TypedContextVar(Generic[T]):
    """Type-safe wrapper around contextvars.ContextVar."""

    def __init__(self, name: str, type_: type[T], default: T | None = None) -> None:
        """Initialize TypedContextVar with name, type, and optional default."""
        self._name = name
        self._type = type_
        self._has_default = default is not None
        if default is not None:
            self._var: ContextVar[T] = ContextVar(name, default=default)
        else:
            self._var = ContextVar(name)

    def get(self) -> T | None:
        """Return value or None if not set."""
        try:
            return self._var.get()
        except LookupError:
            return None

    def get_or_raise(self) -> T:
        """Return value or raise RuntimeError if not set."""
        try:
            return self._var.get()
        except LookupError as err:
            raise RuntimeError(
                f"Context variable '{self._name}' is not set in the current context. "
                f"Make sure to set it before accessing.",
            ) from err

    def set(self, value: T) -> Token[T]:
        """Set value and return a reset token."""
        return self._var.set(value)

    def reset(self, token: Token[T]) -> None:
        """Reset to previous value using token."""
        self._var.reset(token)

    def is_set(self) -> bool:
        """Return True if value is set in current context."""
        try:
            self._var.get()
            return True
        except LookupError:
            return False


class BaseContext:
    """Abstract base for typed contexts in services."""

    pass


@dataclass
class RequestContext(BaseContext):
    """Per-request context with request ID, user, tenant, and extras."""

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
    """Set request context and return token for reset."""
    ctx = RequestContext(
        request_id=request_id,
        user=user,
        tenant=tenant,
        extra=extra or {},
    )
    return REQUEST_CONTEXT.set(ctx)
