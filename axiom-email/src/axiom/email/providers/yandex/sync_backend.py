"""axiom.email.providers.yandex.sync_backend — Synchronous Yandex SMTP backend."""

import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from axiom.core.logger import get_logger
from axiom.email.models import EmailMessage, SendResult
from axiom.email.providers.yandex.config import YandexSMTPConfig


def _build_mime(message: EmailMessage, from_address: str) -> MIMEMultipart:
    """Build a MIME message from an EmailMessage."""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = message.subject
    msg["From"] = message.from_ or from_address
    msg["To"] = ", ".join(message.to)

    if message.cc:
        msg["Cc"] = ", ".join(message.cc)
    if message.reply_to:
        msg["Reply-To"] = message.reply_to
    for header_name, header_value in message.headers.items():
        msg[header_name] = header_value

    # Body part
    if message.text and message.html:
        alternative = MIMEMultipart("alternative")
        alternative.attach(MIMEText(message.text, "plain", "utf-8"))
        alternative.attach(MIMEText(message.html, "html", "utf-8"))
        msg.attach(alternative)
    elif message.html:
        msg.attach(MIMEText(message.html, "html", "utf-8"))
    elif message.text:
        msg.attach(MIMEText(message.text, "plain", "utf-8"))

    for attachment in message.attachments:
        part = MIMEApplication(attachment.content)
        disposition = "inline" if attachment.inline else "attachment"
        part.add_header("Content-Disposition", disposition, filename=attachment.filename)
        part.add_header("Content-Type", attachment.content_type, name=attachment.filename)
        if attachment.inline and attachment.content_id:
            part.add_header("Content-ID", f"<{attachment.content_id}>")
        msg.attach(part)

    return msg


class YandexSyncSMTPBackend:
    """Synchronous SMTP backend for Yandex Mail (new connection per send)."""

    def __init__(self, config: YandexSMTPConfig) -> None:
        """Initialize with Yandex SMTP configuration."""
        self._config = config
        self._logger = get_logger("axiom.email.providers.yandex.sync")

    def send(self, message: EmailMessage) -> SendResult:
        """Send an email via Yandex SMTP. Creates a new connection per call."""
        from_address = self._config.get_from_address()
        mime_msg = _build_mime(message, from_address)
        all_recipients = list(message.to) + list(message.cc) + list(message.bcc)

        try:
            conn: smtplib.SMTP
            if self._config.use_tls:
                conn = smtplib.SMTP_SSL(self._config.host, self._config.port)
            else:
                conn = smtplib.SMTP(self._config.host, self._config.port)
                conn.starttls()

            with conn:
                conn.login(self._config.username, self._config.password)
                conn.sendmail(from_address, all_recipients, mime_msg.as_string())
                message_id = mime_msg.get("Message-ID")

            return SendResult(success=True, message_id=message_id)

        except smtplib.SMTPException as exc:
            self._logger.error("SMTP error sending to {to}: {exc}", to=message.to, exc=exc)
            return SendResult(success=False, error=str(exc))
        except OSError as exc:
            self._logger.error("Connection error sending to {to}: {exc}", to=message.to, exc=exc)
            return SendResult(success=False, error=str(exc))


__all__ = ["YandexSyncSMTPBackend"]
