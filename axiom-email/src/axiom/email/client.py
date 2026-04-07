"""axiom.email.client — Synchronous and asynchronous email clients."""

from axiom.core.logger import get_logger
from axiom.email.interfaces import AsyncMailBackend, MailHook, SyncMailBackend, TemplateRenderer
from axiom.email.models import EmailMessage, SendResult


class SyncMailClient:
    """Synchronous email client with hook and renderer support."""

    def __init__(
        self,
        backend: SyncMailBackend,
        renderer: TemplateRenderer | None = None,
        hooks: list[MailHook] | None = None,
    ) -> None:
        """Initialize SyncMailClient."""
        self._backend = backend
        self._renderer = renderer
        self._hooks: list[MailHook] = hooks or []
        self._logger = get_logger("axiom.email.client.sync")

    def send(
        self,
        to: list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
        from_: str | None = None,
    ) -> SendResult:
        """Send an email with a simple API covering 80% of use cases."""
        message = EmailMessage(to=to, subject=subject, text=text, html=html, from_=from_)
        return self.send_message(message)

    def send_message(self, message: EmailMessage) -> SendResult:
        """Send an EmailMessage with full control over all fields."""
        for hook in self._hooks:
            hook.before_send(message)

        try:
            result = self._backend.send(message)
        except Exception as exc:  # noqa: BLE001
            self._logger.error(
                "Unexpected error sending email to {to}: {exc}",
                to=message.to,
                exc=exc,
            )
            result = SendResult(success=False, error=str(exc))

        for hook in self._hooks:
            hook.after_send(message, result)

        return result


class AsyncMailClient:
    """Asynchronous email client with hook, renderer and lifecycle support."""

    def __init__(
        self,
        backend: AsyncMailBackend,
        renderer: TemplateRenderer | None = None,
        hooks: list[MailHook] | None = None,
    ) -> None:
        """Initialize AsyncMailClient."""
        self._backend = backend
        self._renderer = renderer
        self._hooks: list[MailHook] = hooks or []
        self._logger = get_logger("axiom.email.client.async")

    async def startup(self) -> None:
        """Delegate startup to the backend."""
        await self._backend.startup()

    async def shutdown(self) -> None:
        """Delegate shutdown to the backend."""
        await self._backend.shutdown()

    async def send(
        self,
        to: list[str],
        subject: str,
        text: str | None = None,
        html: str | None = None,
        from_: str | None = None,
    ) -> SendResult:
        """Send an email with a simple API covering 80% of use cases."""
        message = EmailMessage(to=to, subject=subject, text=text, html=html, from_=from_)
        return await self.send_message(message)

    async def send_message(self, message: EmailMessage) -> SendResult:
        """Send an EmailMessage with full control over all fields."""
        for hook in self._hooks:
            hook.before_send(message)

        try:
            result = await self._backend.send(message)
        except Exception as exc:  # noqa: BLE001
            self._logger.error(
                "Unexpected error sending email to {to}: {exc}",
                to=message.to,
                exc=exc,
            )
            result = SendResult(success=False, error=str(exc))

        for hook in self._hooks:
            hook.after_send(message, result)

        return result


__all__ = [
    "AsyncMailClient",
    "SyncMailClient",
]
