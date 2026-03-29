# mypy: disable-error-code="attr-defined,untyped-decorator"
"""axiom.oltp.beanie.base.mixin.timestamp — TimestampMixin for Beanie documents."""

from datetime import datetime, timezone

from pydantic import Field

from beanie import Insert, Replace, SaveChanges, before_event


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class TimestampMixin:
    """Mixin that adds created_at and updated_at fields to a Beanie Document."""

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    @before_event([Insert, Replace, SaveChanges])
    def set_updated_at(self) -> None:
        """Refresh ``updated_at`` to the current UTC time before each write."""
        self.updated_at = _utcnow()
