"""axiom.email.providers.yandex.config — Yandex SMTP configuration."""

from dataclasses import dataclass


@dataclass
class YandexSMTPConfig:
    """Configuration for the Yandex SMTP backend."""

    username: str
    """Yandex account login (used as sender address if from_ not provided)."""

    password: str
    """Yandex account password or application password."""

    host: str = "smtp.yandex.ru"
    """SMTP server hostname."""

    port: int = 465
    """SMTP server port. 465 for SSL, 587 for STARTTLS."""

    use_tls: bool = True
    """If True, use SMTP_SSL (port 465). If False, use STARTTLS (port 587)."""

    default_from: str = ""
    """Default sender address. Falls back to username if empty."""

    validate_certs: bool = True
    """If False, skip TLS certificate validation (for internal/test servers only)."""

    def get_from_address(self) -> str:
        """Return the sender address to use when none is specified."""
        return self.default_from or self.username


__all__ = ["YandexSMTPConfig"]
