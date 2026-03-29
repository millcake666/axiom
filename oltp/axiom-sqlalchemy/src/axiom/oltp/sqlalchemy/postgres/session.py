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
        """Initialise the routing session.

        Args:
            engines: Dict with ``"writer"`` and ``"reader"`` ``AsyncEngine`` values.
            *args: Positional arguments forwarded to ``Session.__init__``.
            **kwargs: Keyword arguments forwarded to ``Session.__init__``.
        """
        super().__init__(*args, **kwargs)
        self.engines = engines

    def get_bind(
        self,
        mapper=None,
        clause=None,
        **_kw,
    ):
        """Return the appropriate engine based on the statement type.

        Args:
            mapper: Optional mapper hint (unused).
            clause: The SQL clause being executed.
            **_kw: Additional keyword arguments (ignored).

        Returns:
            The writer's sync engine for mutating statements or during flush;
            the reader's sync engine otherwise.
        """
        if self._flushing or isinstance(clause, Update | Delete | Insert):
            return self.engines["writer"].sync_engine
        return self.engines["reader"].sync_engine
