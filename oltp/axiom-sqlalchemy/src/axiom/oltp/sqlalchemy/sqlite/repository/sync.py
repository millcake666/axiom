# ruff: noqa: W505, D102
# mypy: disable-error-code="valid-type,type-arg,attr-defined,assignment,arg-type"
"""axiom.oltp.sqlalchemy.sqlite.repository.sync — Sync SQLite repository."""

from collections.abc import Sequence
from typing import Any

from axiom.oltp.sqlalchemy.base.declarative import Base
from axiom.oltp.sqlalchemy.base.repository.sync import SyncSQLAlchemyRepository
from sqlalchemy import Select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session


class SyncSQLiteRepository[
    ModelType: Base,
    SessionType: Session,
    QueryType: Select,
](SyncSQLAlchemyRepository):
    """Sync SQLite repository with SQLite-compatible upsert."""

    def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Insert or update a record using SQLite ``INSERT … ON CONFLICT DO UPDATE``.

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

        stmt = sqlite_insert(self.model_class).values(**attributes)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_={
                field: attributes[field]
                for field in (update_fields or attributes.keys())
                if attributes.get(field) is not None
            },
        ).returning(self.model_class)

        select_stmt = self._query().from_statement(stmt)
        return self._one_or_none(select_stmt)  # type: ignore[return-value, arg-type]

    def create_or_update_many(self, models: Sequence[ModelType]) -> list[ModelType]:
        if not models:
            return []
        conflict_cols = self._get_conflict_fields()
        if not conflict_cols:
            results = []
            for m in models:
                results.append(self.create_or_update(m))
            return results
        rows = [{k: v for k, v in self._model_to_dict(m).items() if v is not None} for m in models]
        stmt = sqlite_insert(self.model_class).values(rows)
        all_non_conflict_keys = {k for row in rows for k in row if k not in conflict_cols}
        update_set = {k: getattr(stmt.excluded, k) for k in all_non_conflict_keys}
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_cols,
            set_=update_set,
        ).returning(self.model_class)
        select_stmt = self._query().from_statement(stmt)
        return self._all(select_stmt)
