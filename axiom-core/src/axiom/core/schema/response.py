# mypy: disable-error-code="call-arg,valid-type,name-defined,type-arg"
"""axiom.core.schema.response — ORM-agnostic CRUD response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class PaginationResponse[T](BaseModel):
    """Generic paginated list response for repository query results."""

    page: int = Field(..., examples=[1])
    page_size: int = Field(..., examples=[10])
    total_pages: int = Field(..., examples=[5])
    total_count: int = Field(..., examples=[50])
    data: list[T] = Field(...)

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )


class CountResponse(BaseModel):
    """Response schema returning a single aggregate count value."""

    count: int = Field(..., examples=[100])

    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True,
    )
