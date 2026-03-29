# ruff: noqa: D101, D104, D106
"""Test document models for axiom-beanie tests."""

from typing import Optional

from beanie import Document, Link
from pydantic import Field

from axiom.oltp.beanie.base.mixin.timestamp import TimestampMixin


class UserDocument(TimestampMixin, Document):
    name: str
    email: str
    age: int

    class Settings:
        name = "users"


class PostDocument(TimestampMixin, Document):
    title: str
    content: Optional[str] = Field(default=None)
    user: Link[UserDocument] | None = Field(default=None)

    class Settings:
        name = "posts"


class CommentDocument(TimestampMixin, Document):
    text: str
    rating: int = Field(default=0)
    post: Link[PostDocument] | None = Field(default=None)

    class Settings:
        name = "comments"
