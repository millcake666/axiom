# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg"
"""axiom.oltp.sqlalchemy.base.controller.async_ — Async SQLAlchemy controller."""

from collections.abc import Callable
from typing import Any

from axiom.oltp.sqlalchemy.abs.controller.async_ import AsyncBaseController
from axiom.oltp.sqlalchemy.base.declarative import Base


class AsyncSQLAlchemyController[ModelType: Base](AsyncBaseController):
    """Async SQLAlchemy controller with transaction management."""

    async def processing_transaction(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute *function* inside a managed async transaction.

        Commits on success and rolls back on any exception.  Refreshes the
        returned instance(s) after create or update operations.

        Args:
            function: The async repository-calling coroutine to wrap.
            *args: Positional arguments forwarded to *function*.
            **kwargs: Keyword arguments forwarded to *function*.

        Returns:
            Whatever *function* returns.

        Raises:
            Exception: Re-raises any exception after rolling back.
        """
        try:
            result = await function(self, *args, **kwargs)
            await self.repository.session.commit()
            if result is not None and function.__name__.lower() in ["update", "create"]:
                if isinstance(result, list | tuple | set):
                    for res in result:
                        await self.repository.session.refresh(res)
                else:
                    await self.repository.session.refresh(result)
        except Exception as exception:
            await self.repository.session.rollback()
            raise exception
        return result
