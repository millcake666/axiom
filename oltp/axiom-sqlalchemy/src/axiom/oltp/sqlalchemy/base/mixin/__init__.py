"""axiom.oltp.sqlalchemy.base.mixin — SQLAlchemy model mixins."""

from axiom.oltp.sqlalchemy.base.mixin.as_dict import AsDictMixin
from axiom.oltp.sqlalchemy.base.mixin.timestamp import TimestampMixin

__all__ = ["AsDictMixin", "TimestampMixin"]
