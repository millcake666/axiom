"""axiom.oltp.sqlalchemy.exception_handler — SQLAlchemy exception handlers for FastAPI."""

from axiom.oltp.sqlalchemy.exception_handler.integrity import register_integrity_handler

__all__ = ["register_integrity_handler"]
