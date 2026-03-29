"""axiom.oltp.sqlalchemy.base.utils — Utilities for nested field operations."""

from typing import Any

from sqlalchemy import inspect  # type: ignore[attr-defined]
from sqlalchemy.orm import RelationshipProperty


def resolve_nested_relation(model: type, field_path: str) -> tuple[type, str]:
    """Resolve a nested field path to the final model and column name.

    Args:
        model: The starting model class.
        field_path: Dot-notation field path (e.g., "user.profile.name").

    Returns:
        Tuple of (final_model_class, column_name).

    Raises:
        ValueError: If any relation in the path does not exist.
    """
    if "." not in field_path:
        return model, field_path

    parts = field_path.split(".")
    current_model = model

    for rel_name in parts[:-1]:
        if not hasattr(current_model, rel_name):
            raise ValueError(f"{current_model.__name__} has no relation '{rel_name}'")
        attr = getattr(current_model, rel_name)
        if not isinstance(attr.property, RelationshipProperty):
            raise ValueError(f"{current_model.__name__}.{rel_name} is not a relation")
        current_model = attr.property.mapper.class_

    return current_model, parts[-1]


def get_nested_field_type(model: type, field_path: str) -> type:
    """Get the Python type of a nested field.

    Args:
        model: The starting model class.
        field_path: Dot-notation field path (e.g., "user.profile.name").

    Returns:
        The Python type of the final column.

    Raises:
        ValueError: If the field path is invalid.
    """
    final_model, column_name = resolve_nested_relation(model, field_path)
    mapper = inspect(final_model)

    if column_name not in {c.key for c in mapper.columns}:
        raise ValueError(f"{final_model.__name__} has no column '{column_name}'")

    column = getattr(final_model, column_name)
    return column.type.python_type


def validate_nested_field(
    model: type,
    field_path: str,
    value: Any | None = None,
) -> None:
    """Validate a value against a nested field's type.

    Args:
        model: The starting model class.
        field_path: Dot-notation field path (e.g., "user.profile.name").
        value: The value to validate (None skips type checking).

    Raises:
        ValueError: If the field path is invalid or type mismatch.
    """
    from enum import Enum

    final_model, column_name = resolve_nested_relation(model, field_path)
    field_type = get_nested_field_type(model, field_path)

    # Skip validation for dict types (JSON columns)
    if issubclass(field_type, dict):
        return

    # Handle Enum fields
    if issubclass(field_type, Enum):
        if value is not None and all(value != item for item in field_type):
            available = [e for e in field_type]
            raise ValueError(
                f"Value {value!r} is not permissible for field {field_path}. "
                f"Available values: {available}",
            )
        # Get the underlying type of the enum
        enum_member = next(iter(field_type))
        field_type = type(enum_member.value)

    # Type validation
    if value is not None and not isinstance(value, field_type):
        raise ValueError(
            f"Wrong type for field {field_path}: "
            f"expected {field_type.__name__}, "
            f"received {type(value).__name__}",
        )


def get_nested_value(obj: Any, field_path: str) -> Any:
    """Get a value from a nested object using dot notation.

    Args:
        obj: The object to traverse.
        field_path: Dot-notation path (e.g., "user.profile.name").

    Returns:
        The value at the nested path.

    Raises:
        AttributeError: If any attribute in the path does not exist.
    """
    parts = field_path.split(".")
    current = obj

    for part in parts:
        current = getattr(current, part)

    return current


def set_nested_value(obj: Any, field_path: str, value: Any) -> None:
    """Set a value on a nested object using dot notation.

    Args:
        obj: The object to traverse.
        field_path: Dot-notation path (e.g., "user.profile.name").
        value: The value to set.

    Raises:
        AttributeError: If any attribute in the path does not exist.
    """
    parts = field_path.split(".")
    current = obj

    for part in parts[:-1]:
        current = getattr(current, part)

    setattr(current, parts[-1], value)
