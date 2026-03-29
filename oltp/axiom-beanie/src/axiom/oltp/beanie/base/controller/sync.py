# mypy: disable-error-code="valid-type,type-arg,attr-defined"
"""axiom.oltp.beanie.base.controller.sync — Sync MongoDB controller."""

from collections.abc import Callable
from typing import Any

from axiom.oltp.beanie.abs.controller.sync import SyncBaseController
from axiom.oltp.beanie.base.document import SyncDocument


class SyncMongoController[ModelType: SyncDocument](SyncBaseController):  # type: ignore[misc]
    """Sync MongoDB controller with pass-through transaction management.

    Concrete implementation of ``SyncBaseController`` for PyMongo-backed
    ``SyncDocument`` models. Executes write operations directly without an
    explicit session; subclass and override ``processing_transaction`` to add
    session or retry logic.
    """

    def processing_transaction(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute a function, re-raising any exception that occurs.

        Args:
            function: The callable to invoke.
            *args: Positional arguments forwarded to ``function``.
            **kwargs: Keyword arguments forwarded to ``function``.

        Returns:
            The return value of ``function``.

        Raises:
            Exception: Any exception raised by ``function`` is re-raised as-is.
        """
        try:
            result = function(self, *args, **kwargs)
        except Exception as exception:
            raise exception
        return result
