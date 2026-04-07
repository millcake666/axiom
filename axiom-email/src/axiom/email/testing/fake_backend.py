"""axiom.email.testing.fake_backend — No-op email backend for testing."""

from axiom.email.models import EmailMessage, SendResult


class FakeMailBackend:
    """Synchronous no-op backend. Always reports success without sending."""

    def send(self, message: EmailMessage) -> SendResult:
        """Return success without sending anything."""
        return SendResult(success=True)


class AsyncFakeMailBackend:
    """Asynchronous no-op backend. Always reports success without sending."""

    async def send(self, message: EmailMessage) -> SendResult:
        """Return success without sending anything."""
        return SendResult(success=True)

    async def startup(self) -> None:
        """No-op startup."""

    async def shutdown(self) -> None:
        """No-op shutdown."""


__all__ = ["AsyncFakeMailBackend", "FakeMailBackend"]
