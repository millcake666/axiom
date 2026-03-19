# ruff: noqa: D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="type-arg,no-untyped-def"
"""axiom.oltp.sqlalchemy.postgres.session — RoutingSession for read/write splitting."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Delete, Insert, Update


class RoutingSession(Session):
    """Optional routing session for read/write splitting.

    Routes write operations (INSERT/UPDATE/DELETE/flush) to writer engine
    and read operations to reader engine.
    """

    def __init__(
        self,
        engines: dict[str, AsyncEngine],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.engines = engines

    def get_bind(
        self,
        mapper=None,
        clause=None,
        **kw,
    ):
        if self._flushing or isinstance(clause, Update | Delete | Insert):
            return self.engines["writer"].sync_engine
        return self.engines["reader"].sync_engine
