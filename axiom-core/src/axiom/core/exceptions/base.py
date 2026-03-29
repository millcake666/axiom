"""axiom.core.exceptions.base — Base exception and error detail schema."""

from typing import Any

from pydantic import BaseModel


class BaseError(Exception):
    """Base class for all axiom domain errors.

    Subclasses should override code and status_code as class attributes.
    """

    code: str
    status_code: int
    message: str
    details: dict[str, Any]

    def __init__(
        self,
        message: str,
        code: str = "internal_error",
        details: dict[str, Any] | None = None,
        status_code: int = 500,
    ) -> None:
        """Initialize BaseError.

        Args:
            message: Human-readable error description.
            code: Machine-readable error code.
            details: Optional mapping of additional context about the error.
            status_code: HTTP status code.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Initialize subclasses with default code and status_code."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "code"):
            cls.code = "internal_error"
        if not hasattr(cls, "status_code"):
            cls.status_code = 500


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
