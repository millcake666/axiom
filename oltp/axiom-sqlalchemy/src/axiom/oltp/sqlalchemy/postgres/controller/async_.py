# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg"
"""axiom.oltp.sqlalchemy.postgres.controller.async_ — Async PostgreSQL controller."""

from axiom.oltp.sqlalchemy.base.controller.async_ import AsyncSQLAlchemyController
from axiom.oltp.sqlalchemy.base.declarative import Base


class AsyncPostgresController[ModelType: Base](AsyncSQLAlchemyController):
    """Async PostgreSQL controller — ready-to-use with AsyncPostgresRepository."""
