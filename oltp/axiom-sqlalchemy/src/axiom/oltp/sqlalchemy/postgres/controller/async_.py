# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg,name-defined"
"""axiom.oltp.sqlalchemy.postgres.controller.async_ — Async PostgreSQL controller."""

from collections.abc import Sequence
from typing import Any

from axiom.core.exceptions.http import NotFoundError, UnprocessableError
from axiom.oltp.sqlalchemy.base.controller.async_ import AsyncSQLAlchemyController
from axiom.oltp.sqlalchemy.base.declarative import Base


class AsyncPostgresController[ModelType: Base](AsyncSQLAlchemyController):
    """Async PostgreSQL controller — ready-to-use with AsyncPostgresRepository."""

    @AsyncSQLAlchemyController.transactional
    async def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Insert or update a record matched by *attributes*, returning the result."""
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited")
        result = await self.repository.create_or_update_by(
            attributes=attributes,
            update_fields=update_fields,
        )
        if result is None:
            raise NotFoundError("Failed to insert or update")
        return result  # type: ignore[return-value]

    @AsyncSQLAlchemyController.transactional
    async def create_or_update(self, model: ModelType) -> ModelType:
        """Persist *model*, inserting it if new or updating if it already exists."""
        return await self.repository.create_or_update(model=model)

    @AsyncSQLAlchemyController.transactional
    async def create_or_update_many(self, models: Sequence) -> list[ModelType]:
        """Bulk insert-or-update *models* and return the persisted instances."""
        return await self.repository.create_or_update_many(models=models)
