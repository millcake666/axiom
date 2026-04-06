"""axiom.core.entities.schema — Base Pydantic schemas for DTOs and responses."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic schema for DTO and response models.

    Enables ORM-mode, alias population, and enum value coercion.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class BaseRequestSchema(BaseModel):
    """Base schema for incoming request payloads.

    Enables alias population and enum value coercion without ORM-mode.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )


class BaseResponseSchema(BaseSchema):
    """Base schema for outgoing response models."""

    def model_response(self) -> dict[str, Any]:
        """Serialize the model using field aliases.

        Returns:
            Dictionary with alias keys suitable for API responses.
        """
        return self.model_dump(by_alias=True)


class PaginatedResponse(BaseResponseSchema, Generic[T]):
    """Generic paginated response wrapper.

    has_next is computed automatically from page, page_size, and total.
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool = False

    def model_post_init(self, _context: Any) -> None:
        """Compute has_next after model initialization.

        Args:
            _context: Pydantic post-init context (unused).
        """
        object.__setattr__(self, "has_next", (self.page * self.page_size) < self.total)
