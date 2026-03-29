"""axiom.core.exceptions.base — Base exception and error detail schema."""

from typing import Any

from pydantic import BaseModel


class BaseError(Exception):
    """Base class for all axiom domain errors.

    Subclasses should override code and status_code as class attributes.
    """

    code: str = "internal_error"
    status_code: int = 500
    message: str
    details: dict[str, Any]

    def __init__(
        self,
        message: str,
        code: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
    ) -> None:
        """Initialize BaseError.

        Args:
            message: Human-readable error description.
            code: Machine-readable error code. Defaults to class attribute.
            details: Optional mapping of additional context about the error.
            status_code: HTTP status code. Defaults to class attribute.
        """
        super().__init__(message)
        self.message = message
        # Use instance-provided value if given, otherwise use class attribute
        self.code = code if code is not None else self.__class__.code
        self.status_code = status_code if status_code is not None else self.__class__.status_code
        self.details = details or {}


class ErrorDetail(BaseModel):
    """Pydantic schema for serializing a BaseError to an API response body."""

    code: str
    message: str
    details: dict[str, Any] = {}

    @classmethod
    def from_error(cls, error: BaseError) -> "ErrorDetail":
        """Create an ErrorDetail from a BaseError instance.

        Args:
            error: Source error to convert.

        Returns:
            ErrorDetail populated from the error's code, message and details.
        """
        return cls(code=error.code, message=error.message, details=error.details)
