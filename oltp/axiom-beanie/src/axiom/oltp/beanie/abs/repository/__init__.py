"""axiom.oltp.beanie.abs.repository — Abstract repository interfaces."""

from axiom.oltp.beanie.abs.repository.async_ import AsyncBaseRepository
from axiom.oltp.beanie.abs.repository.sync import SyncBaseRepository

__all__ = ["AsyncBaseRepository", "SyncBaseRepository"]
