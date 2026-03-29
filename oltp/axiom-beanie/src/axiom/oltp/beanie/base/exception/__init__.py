# mypy: disable-error-code="misc"
"""axiom.oltp.beanie.base.exception — Exceptions for the axiom.oltp.beanie.base package."""

from axiom.core.exceptions.base import BaseError


class BeanieOperationError(BaseError):
    """Error during a Beanie document operation."""

    code = "beanie_operation_error"
    status_code = 500


class DocumentNotFoundError(BaseError):
    """Beanie document not found."""

    code = "document_not_found"
    status_code = 404


__all__ = [
    "BeanieOperationError",
    "DocumentNotFoundError",
]
