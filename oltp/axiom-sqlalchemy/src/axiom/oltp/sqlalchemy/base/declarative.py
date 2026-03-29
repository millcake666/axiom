"""axiom.oltp.sqlalchemy.base.declarative — Declarative base class."""

import re

from axiom.oltp.sqlalchemy.base.meta import meta

from sqlalchemy.orm import DeclarativeBase, declared_attr


def to_snake(camel: str) -> str:
    """Convert PascalCase, camelCase, or kebab-case string to snake_case."""
    snake = re.sub(
        r"([A-Z]+)([A-Z][a-z])",
        lambda m: f"{m.group(1)}_{m.group(2)}",
        camel,
    )
    snake = re.sub(r"([a-z])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    snake = re.sub(r"([0-9])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    snake = re.sub(r"([a-z])([0-9])", lambda m: f"{m.group(1)}_{m.group(2)}", snake)
    snake = snake.replace("-", "_")
    return snake.lower()


class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy models."""

    metadata = meta  # type: ignore[misc]
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Derive the table name by converting the class name to snake_case.

        Returns:
            The snake_case table name for this model.
        """
        return to_snake(cls.__name__)
