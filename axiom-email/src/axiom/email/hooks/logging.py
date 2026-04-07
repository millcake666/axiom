"""axiom.email.hooks.logging — Logging hook for email sending observability."""

from axiom.core.logger import get_logger

from axiom.email.models import EmailMessage, SendResult


class LoggingHook:
    """Hook that logs email sending activity without exposing sensitive data."""

    def __init__(self) -> None:
        """Initialize LoggingHook."""
        self._logger = get_logger("axiom.email.hooks.logging")

    def before_send(self, message: EmailMessage) -> None:
        """Log message metadata before sending (no body, no passwords)."""
        self._logger.info(
            "Sending email: to={to} subject={subject!r} attachments={n}",
            to=message.to,
            subject=message.subject,
            n=len(message.attachments),
        )

    def after_send(self, message: EmailMessage, result: SendResult) -> None:
        """Log send result after the attempt."""
        if result.success:
            self._logger.info(
                "Email sent successfully: to={to} message_id={message_id}",
                to=message.to,
                message_id=result.message_id,
            )
        else:
            self._logger.warning(
                "Email send failed: to={to} error_type={error_type}",
                to=message.to,
                error_type=type(result.error).__name__ if result.error else "unknown",
            )


__all__ = ["LoggingHook"]
