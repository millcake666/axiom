"""axiom.oltp.sqlalchemy.abs.repository — Abstract repository classes."""

from axiom.oltp.sqlalchemy.abs.repository.async_ import AsyncBaseRepository
from axiom.oltp.sqlalchemy.abs.repository.sync import SyncBaseRepository

__all__ = ["AsyncBaseRepository", "SyncBaseRepository"]
