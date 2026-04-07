"""axiom.email.models — Data models for email messages."""

from dataclasses import dataclass, field


@dataclass
class EmailAddress:
    """An email address with optional display name."""

    email: str
    """The email address (e.g. 'user@example.com')."""

    name: str = ""
    """Optional display name (e.g. 'John Doe')."""

    def __str__(self) -> str:
        """Return formatted address string."""
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class Attachment:
    """A file attachment for an email message."""

    filename: str
    """The filename as it will appear in the email."""

    content: bytes
    """Raw file content."""

    content_type: str = "application/octet-stream"
    """MIME content type of the attachment."""

    inline: bool = False
    """If True, embed as inline content (e.g. images in HTML)."""

    content_id: str = ""
    """Content-ID for inline attachments (used in HTML src)."""


@dataclass
class EmailMessage:
    """A complete email message ready to be sent."""

    to: list[str]
    """List of recipient email addresses."""

    subject: str
    """Email subject line."""

    text: str | None = None
    """Plain text body."""

    html: str | None = None
    """HTML body."""

    from_: str | None = None
    """Sender email address. If None, the backend default is used."""

    cc: list[str] = field(default_factory=list)
    """CC recipients."""

    bcc: list[str] = field(default_factory=list)
    """BCC recipients."""

    reply_to: str | None = None
    """Reply-To address."""

    headers: dict[str, str] = field(default_factory=dict)
    """Additional SMTP headers."""

    attachments: list[Attachment] = field(default_factory=list)
    """File attachments."""


@dataclass
class SendResult:
    """Result of a send operation."""

    success: bool
    """True if the message was sent successfully."""

    message_id: str | None = None
    """The Message-ID assigned by the server, if available."""

    error: str | None = None
    """Human-readable error description if success is False."""


__all__ = [
    "Attachment",
    "EmailAddress",
    "EmailMessage",
    "SendResult",
]
