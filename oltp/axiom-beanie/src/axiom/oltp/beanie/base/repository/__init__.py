"""axiom.oltp.beanie.base.repository — Concrete Beanie repository."""

from axiom.oltp.beanie.base.repository.async_ import AsyncBeanieRepository
from axiom.oltp.beanie.base.repository.sync import SyncMongoRepository

__all__ = ["AsyncBeanieRepository", "SyncMongoRepository"]
