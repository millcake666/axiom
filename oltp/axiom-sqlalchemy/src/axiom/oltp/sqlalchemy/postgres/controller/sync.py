# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg"
"""axiom.oltp.sqlalchemy.postgres.controller.sync — Sync PostgreSQL controller."""

from axiom.oltp.sqlalchemy.base.controller.sync import SyncSQLAlchemyController
from axiom.oltp.sqlalchemy.base.declarative import Base


class SyncPostgresController[ModelType: Base](SyncSQLAlchemyController):
    """Sync PostgreSQL controller — ready-to-use with SyncPostgresRepository."""
