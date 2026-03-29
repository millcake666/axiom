"""axiom.core.entities — Base Pydantic schemas and domain dataclasses."""

from axiom.core.entities.domain import BaseDomainDC
from axiom.core.entities.schema import (
    BaseRequestSchema,
    BaseResponseSchema,
    BaseSchema,
    PaginatedResponse,
)

__all__ = [
    "BaseDomainDC",
    "BaseRequestSchema",
    "BaseResponseSchema",
    "BaseSchema",
    "PaginatedResponse",
]
