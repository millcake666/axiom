"""axiom.email.interfaces — Protocol definitions for email backends, renderers and hooks."""

from typing import Any, Protocol, runtime_checkable

from axiom.email.models import EmailMessage, SendResult


@runtime_checkable
class SyncMailBackend(Protocol):
    """Protocol for synchronous email backends."""

    def send(self, message: EmailMessage) -> SendResult:
        """Send an email message synchronously."""
        ...


@runtime_checkable
class AsyncMailBackend(Protocol):
    """Protocol for asynchronous email backends with lifecycle management."""

    async def send(self, message: EmailMessage) -> SendResult:
        """Send an email message asynchronously."""
        ...

    async def startup(self) -> None:
        """Initialize backend resources (connections, pools, etc.)."""
        ...

    async def shutdown(self) -> None:
        """Release backend resources."""
        ...


@runtime_checkable
class TemplateRenderer(Protocol):
    """Protocol for email template renderers."""

    def render(self, template: str, context: dict[str, Any]) -> str:
        """Render a template string with the given context and return HTML."""
        ...


@runtime_checkable
class MailHook(Protocol):
    """Protocol for email sending hooks."""

    def before_send(self, message: EmailMessage) -> None:
        """Called before the message is sent."""
        ...

    def after_send(self, message: EmailMessage, result: SendResult) -> None:
        """Called after the send attempt, regardless of success."""
        ...


__all__ = [
    "AsyncMailBackend",
    "MailHook",
    "SyncMailBackend",
    "TemplateRenderer",
]
