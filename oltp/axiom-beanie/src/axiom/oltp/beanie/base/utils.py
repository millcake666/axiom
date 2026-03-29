# ruff: noqa: D100, D101, D102, D103
# mypy: disable-error-code="attr-defined"
"""axiom.oltp.beanie.base.utils — Utilities for nested field operations in Beanie."""

from typing import Any, get_args, get_origin

from beanie import Document, Link


def is_link_type(field_type: Any) -> bool:
    """Check if a type is a Link type."""
    origin = get_origin(field_type)
    if origin is Link:
        return True
    # Check for Optional[Link[...]] or Union[..., Link[...], ...]
    for arg in get_args(field_type):
        if arg is not type(None) and get_origin(arg) is Link:
            return True
    return False


def get_linked_document_type(field_type: Any) -> type[Document] | None:
    """Extract the Document type from a Link type."""
    origin = get_origin(field_type)
    if origin is Link:
        args = get_args(field_type)
        return args[0] if args else None

    # Check for Optional[Link[...]] or Union[..., Link[...], ...]
    for arg in get_args(field_type):
        if arg is not type(None):
            arg_origin = get_origin(arg)
            if arg_origin is Link:
                arg_args = get_args(arg)
                return arg_args[0] if arg_args else None
    return None


def resolve_nested_field_type(model: type[Document], field_path: str) -> type:
    """Get the Python type of a nested field in a Beanie document.

    Args:
        model: The starting document model class.
        field_path: Dot-notation field path (e.g., "user.profile.name").

    Returns:
        The Python type of the final field.

    Raises:
        ValueError: If the field path is invalid.
    """
    if "." not in field_path:
        return get_field_type(model, field_path)

    parts = field_path.split(".")
    current_model: type[Document] = model

    for part in parts[:-1]:
        field_type = get_field_type(current_model, part)

        # Try to get the linked document type from Link
        linked_doc = get_linked_document_type(field_type)
        if linked_doc is not None:
            current_model = linked_doc
        elif isinstance(field_type, type) and issubclass(field_type, Document):
            current_model = field_type
        else:
            raise ValueError(f"Cannot traverse into field '{part}' of {current_model.__name__}")

    return get_field_type(current_model, parts[-1])


def get_field_type(model: type[Document], field_name: str) -> type:
    """Get the type of a single field on a Beanie document model.

    Args:
        model: The document model class.
        field_name: The field name.

    Returns:
        The Python type of the field.

    Raises:
        ValueError: If the field does not exist.
    """
    if not hasattr(model, "model_fields") or field_name not in model.model_fields:
        raise ValueError(f"{model.__name__} has no field '{field_name}'")

    field_info = model.model_fields[field_name]
    annotation = field_info.annotation

    if annotation is None:
        raise ValueError(f"Field {field_name} has no type annotation")

    return annotation


def validate_nested_field(
    model: type[Document],
    field_path: str,
    value: Any | None = None,
) -> None:
    """Validate a value against a nested field's type in Beanie.

    Args:
        model: The starting document model class.
        field_path: Dot-notation field path (e.g., "user.profile.name").
        value: The value to validate (None skips type checking).

    Raises:
        ValueError: If the field path is invalid or type mismatch.
    """
    from enum import Enum

    field_type = resolve_nested_field_type(model, field_path)

    # Handle generic types (Optional, Union, etc.)
    origin = get_origin(field_type)

    # Skip validation for dict types (embedded documents or raw dicts)
    if field_type is dict:
        return
    if origin is not None and isinstance(origin, type) and issubclass(origin, dict):
        return

    # Handle Optional types - unwrap to get the actual type
    if origin is not None:
        args = get_args(field_type)
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            field_type = non_none_args[0]
            origin = get_origin(field_type)

    # Handle Link types - skip validation (Link is validated by Beanie)
    if origin is Link:
        return

    # Handle Enum fields
    if isinstance(field_type, type) and issubclass(field_type, Enum):
        if value is not None and all(value != item for item in field_type):
            available = [e for e in field_type]
            raise ValueError(
                f"Value {value!r} is not permissible for field {field_path}. "
                f"Available values: {available}",
            )
        enum_member = next(iter(field_type))
        field_type = type(enum_member.value)

    # Type validation - only validate against concrete types
    if value is not None and isinstance(field_type, type) and origin is None:
        if not isinstance(value, field_type):
            raise ValueError(
                f"Wrong type for field {field_path}: "
                f"expected {field_type.__name__}, "
                f"received {type(value).__name__}",
            )


def get_nested_value(obj: Any, field_path: str) -> Any:
    """Get a value from a nested Beanie document using dot notation.

    Args:
        obj: The document object to traverse.
        field_path: Dot-notation path (e.g., "user.profile.name").

    Returns:
        The value at the nested path.

    Raises:
        AttributeError: If any attribute in the path does not exist.
    """
    parts = field_path.split(".")
    current = obj

    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise AttributeError(f"Cannot access '{part}' on {type(current).__name__}")

    return current


def set_nested_value(obj: Any, field_path: str, value: Any) -> None:
    """Set a value on a nested Beanie document using dot notation.

    Args:
        obj: The document object to traverse.
        field_path: Dot-notation path (e.g., "user.profile.name").
        value: The value to set.

    Raises:
        AttributeError: If any attribute in the path does not exist.
    """
    parts = field_path.split(".")
    current = obj

    for part in parts[:-1]:
        if hasattr(current, part):
            current = getattr(current, part)
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise AttributeError(f"Cannot access '{part}' on {type(current).__name__}")

    if hasattr(current, parts[-1]):
        setattr(current, parts[-1], value)
    elif isinstance(current, dict):
        current[parts[-1]] = value
    else:
        raise AttributeError(f"Cannot set '{parts[-1]}' on {type(current).__name__}")
