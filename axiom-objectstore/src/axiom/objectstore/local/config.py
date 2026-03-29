"""axiom.objectstore.local.config — Pydantic config model for local disk storage."""

from pathlib import Path

from pydantic import BaseModel


class LocalDiskConfig(BaseModel):
    """Configuration for local disk object storage.

    Attributes:
        base_dir: Directory on disk where objects are stored.
        base_url: Optional base URL prefix used by :meth:`get_url`.
            When empty, ``file://`` URLs are returned instead.
    """

    base_dir: Path
    base_url: str = ""
