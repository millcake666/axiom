# ruff: noqa: W505, D100, D101, D102, D103, D105, D107
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
