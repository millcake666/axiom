"""axiom.email.exception — Exceptions for the axiom.email package."""

from axiom.core.exceptions import BaseError


class AxiomEmailError(BaseError):
    """Base exception for axiom.email."""

    code: str = "email_error"


class EmailSendError(AxiomEmailError):
    """Raised when sending an email fails."""

    code: str = "email_send_error"


class EmailConfigError(AxiomEmailError):
    """Raised when email backend configuration is invalid."""

    code: str = "email_config_error"


class EmailRenderError(AxiomEmailError):
    """Raised when rendering an email template fails."""

    code: str = "email_render_error"


__all__ = [
    "AxiomEmailError",
    "EmailConfigError",
    "EmailRenderError",
    "EmailSendError",
]
