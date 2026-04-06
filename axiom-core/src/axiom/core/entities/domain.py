"""axiom.core.entities.domain — Base domain dataclass with identity and timestamps."""

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


def _serialize_value(value: Any) -> Any:
    """Recursively convert a value to a JSON-safe primitive.

    Args:
        value: Value to convert.

    Returns:
        JSON-safe representation of value.
    """
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _serialize_value(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, (list, dict)):
        return (
            [_serialize_value(v) for v in value]
            if isinstance(value, list)
            else {k: _serialize_value(v) for k, v in value.items()}
        )
    return value


@dataclass
class BaseDomainDC:
    """Base domain dataclass with UUID identity and UTC timestamps.

    Equality and hashing are based solely on id.
    """

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
        """Recursively serialize to a JSON-safe dict.

        UUID fields are converted to str; datetime fields to ISO-8601 strings.

        Returns:
            Dictionary representation of this dataclass.
        """
        return {f.name: _serialize_value(getattr(self, f.name)) for f in dataclasses.fields(self)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseDomainDC":
        """Construct an instance from a plain dict.

        String values are coerced to UUID or datetime where the field type
        requires it.

        Args:
            data: Dictionary of field values.

        Returns:
            New instance populated from data.
        """
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            if f.type in (UUID, "UUID") or (isinstance(f.type, type) and issubclass(f.type, UUID)):
                value = UUID(value) if isinstance(value, str) else value
            elif f.type in (datetime, "datetime") or (
                isinstance(f.type, type) and issubclass(f.type, datetime)
            ):
                value = datetime.fromisoformat(value) if isinstance(value, str) else value
            kwargs[f.name] = value
        return cls(**kwargs)
