# mypy: disable-error-code="valid-type,type-arg,attr-defined"
"""axiom.oltp.beanie.base.controller.async_ — Async Beanie controller."""

from collections.abc import Callable
from typing import Any

from axiom.oltp.beanie.abs.controller.async_ import AsyncBaseController
from beanie import Document


class AsyncBeanieController[ModelType: Document](AsyncBaseController):  # type: ignore[misc]
    """Async Beanie controller with pass-through transaction management.

    Concrete implementation of ``AsyncBaseController`` for Beanie ``Document``
    models. Executes write operations directly without an explicit session;
    subclass and override ``processing_transaction`` to add session or
    retry logic.
    """

    async def processing_transaction(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function, re-raising any exception that occurs.

        Args:
            function: The async callable to invoke.
            *args: Positional arguments forwarded to ``function``.
            **kwargs: Keyword arguments forwarded to ``function``.

        Returns:
            The return value of ``function``.

        Raises:
            Exception: Any exception raised by ``function`` is re-raised as-is.
        """
        try:
            result = await function(self, *args, **kwargs)
        except Exception as exception:
            raise exception
        return result
