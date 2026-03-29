"""axiom.oltp.beanie.base.document — Base sync document model."""

from pydantic import BaseModel, ConfigDict


class SyncDocument(BaseModel):
    """Base class for sync MongoDB document models."""

    id: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)
