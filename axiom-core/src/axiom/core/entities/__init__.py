"""axiom.core.entities — Base Pydantic schemas and domain dataclasses."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base Pydantic schema for DTO and response models."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class BaseRequestSchema(BaseModel):
    """Base schema for incoming request payloads."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
    )


class BaseResponseSchema(BaseSchema):
    """Base schema for outgoing response models."""

    def model_response(self) -> dict[str, Any]:
        """Serialize using alias-based serialization."""
        return self.model_dump(by_alias=True)


class PaginatedResponse(BaseResponseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool = False

    def model_post_init(self, __context: Any) -> None:
        """Compute has_next automatically."""
        object.__setattr__(self, "has_next", (self.page * self.page_size) < self.total)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: _serialize_value(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


@dataclass
class BaseDomainDC:
    """Base domain dataclass with identity and timestamps."""

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __eq__(self, other: object) -> bool:  # noqa: D105
        if not isinstance(other, BaseDomainDC):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:  # noqa: D105
        return hash(self.id)

    def to_dict(self) -> dict[str, Any]:
        """Recursively serialize to dict (UUID->str, datetime->ISO)."""
        return {
            f.name: _serialize_value(getattr(self, f.name))
            for f in dataclasses.fields(self)
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseDomainDC:
        """Deserialize from dict. Handles UUID and datetime fields."""
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            if f.type in (UUID, "UUID") or (
                isinstance(f.type, type) and issubclass(f.type, UUID)
            ):
                value = UUID(value) if isinstance(value, str) else value
            elif f.type in (datetime, "datetime") or (
                isinstance(f.type, type) and issubclass(f.type, datetime)
            ):
                value = (
                    datetime.fromisoformat(value) if isinstance(value, str) else value
                )
            kwargs[f.name] = value
        return cls(**kwargs)
