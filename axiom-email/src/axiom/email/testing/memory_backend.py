"""axiom.email.testing.memory_backend — In-memory email backend for testing."""

from axiom.email.models import EmailMessage, SendResult


class InMemoryMailBackend:
    """Synchronous backend that stores sent messages in memory."""

    def __init__(self) -> None:
        """Initialize with an empty message store."""
        self.sent_messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> SendResult:
        """Store the message and return success."""
        self.sent_messages.append(message)
        return SendResult(success=True)

    def clear(self) -> None:
        """Remove all stored messages."""
        self.sent_messages.clear()


class AsyncInMemoryMailBackend:
    """Asynchronous backend that stores sent messages in memory."""

    def __init__(self) -> None:
        """Initialize with an empty message store."""
        self.sent_messages: list[EmailMessage] = []

    async def send(self, message: EmailMessage) -> SendResult:
        """Store the message and return success."""
        self.sent_messages.append(message)
        return SendResult(success=True)

    async def startup(self) -> None:
        """No-op startup."""

    async def shutdown(self) -> None:
        """No-op shutdown."""

    def clear(self) -> None:
        """Remove all stored messages."""
        self.sent_messages.clear()


__all__ = ["AsyncInMemoryMailBackend", "InMemoryMailBackend"]
