# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg"
"""axiom.oltp.sqlalchemy.sqlite.controller.async_ — Async SQLite controller."""

from axiom.oltp.sqlalchemy.base.controller.async_ import AsyncSQLAlchemyController
from axiom.oltp.sqlalchemy.base.declarative import Base


class AsyncSQLiteController[ModelType: Base](AsyncSQLAlchemyController):
    """Async SQLite controller — ready-to-use with AsyncSQLiteRepository."""
