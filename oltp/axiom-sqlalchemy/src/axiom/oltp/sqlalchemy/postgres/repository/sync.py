# ruff: noqa: W505
# mypy: disable-error-code="valid-type,type-arg,attr-defined,assignment"
"""axiom.oltp.sqlalchemy.postgres.repository.sync — Sync PostgreSQL repository."""

from typing import Any

from axiom.oltp.sqlalchemy.base.declarative import Base
from axiom.oltp.sqlalchemy.base.repository.sync import SyncSQLAlchemyRepository

from sqlalchemy import Select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session


class SyncPostgresRepository[
    ModelType: Base,
    SessionType: Session,
    QueryType: Select,
](SyncSQLAlchemyRepository):
    """Sync PostgreSQL repository with upsert support via pg_insert."""

    def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Insert or update a record using PostgreSQL ``INSERT … ON CONFLICT DO UPDATE``.

        Args:
            attributes: Full set of field values for the record.
            update_fields: Subset of field names to update on conflict.
                Defaults to all non-``None`` keys in *attributes*.

        Returns:
            The inserted or updated model instance.
        """
        for f, v in attributes.items():
            self._validate_params(field=f, value=v)

        conflict_cols = self._get_conflict_fields()

        if not conflict_cols:
            return self.create(attributes)

        stmt = pg_insert(self.model_class).values(**attributes)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={
                field: attributes[field]
                for field in (update_fields or attributes.keys())
                if attributes.get(field) is not None
            },
        ).returning(self.model_class)

        select_stmt = self._query().from_statement(stmt)
        return self._one_or_none(select_stmt)  # type: ignore[return-value]
