# mypy: disable-error-code="attr-defined"
"""axiom.oltp.sqlalchemy.base.mixin.as_dict — AsDictMixin for SQLAlchemy models."""

from typing import Any

from sqlalchemy import inspect


class AsDictMixin:
    """Mixin that adds an ``as_dict`` serialisation helper to a model."""

    def as_dict(
        self,
        exclude_none: bool = False,
        exclude_columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Serialise the model's column attributes to a plain dict.

        Args:
            exclude_none: When ``True``, omit columns whose value is ``None``.
            exclude_columns: List of column names to always omit.

        Returns:
            Dict mapping column names to their current values.
        """
        data = {}
        for c in inspect(self).mapper.column_attrs:  # type: ignore[union-attr]
            attr = getattr(self, c.key)
            if exclude_columns and c.key in exclude_columns:
                continue
            if exclude_none:
                if attr is not None:
                    data[c.key] = attr
            else:
                data[c.key] = attr
        return data
