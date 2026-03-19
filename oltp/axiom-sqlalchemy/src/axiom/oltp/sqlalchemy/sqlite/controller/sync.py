# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg"
"""axiom.oltp.sqlalchemy.sqlite.controller.sync — Sync SQLite controller."""

from axiom.oltp.sqlalchemy.base.controller.sync import SyncSQLAlchemyController
from axiom.oltp.sqlalchemy.base.declarative import Base


class SyncSQLiteController[ModelType: Base](SyncSQLAlchemyController):
    """Sync SQLite controller — ready-to-use with SyncSQLiteRepository."""
