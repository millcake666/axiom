# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg"
"""axiom.oltp.sqlalchemy.base.controller.sync — Sync SQLAlchemy controller."""

from collections.abc import Callable
from typing import Any

from axiom.oltp.sqlalchemy.abs.controller.sync import SyncBaseController
from axiom.oltp.sqlalchemy.base.declarative import Base


class SyncSQLAlchemyController[ModelType: Base](SyncBaseController):
    """Sync SQLAlchemy controller with transaction management."""

    def processing_transaction(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute *function* inside a managed sync transaction.

        Commits on success and rolls back on any exception.  Refreshes the
        returned instance(s) after create or update operations.

        Args:
            function: The sync repository-calling callable to wrap.
            *args: Positional arguments forwarded to *function*.
            **kwargs: Keyword arguments forwarded to *function*.

        Returns:
            Whatever *function* returns.

        Raises:
            Exception: Re-raises any exception after rolling back.
        """
        try:
            result = function(self, *args, **kwargs)
            self.repository.session.commit()
            if result is not None and function.__name__.lower() in ["update", "create"]:
                if isinstance(result, list | tuple | set):
                    for res in result:
                        self.repository.session.refresh(res)
                else:
                    self.repository.session.refresh(result)
        except Exception as exception:
            self.repository.session.rollback()
            raise exception
        return result
