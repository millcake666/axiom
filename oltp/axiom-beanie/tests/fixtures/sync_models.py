# ruff: noqa: D101, D104, D106
"""Test document models for axiom-beanie sync tests."""

from axiom.oltp.beanie.base.document import SyncDocument


class SyncUserModel(SyncDocument):
    name: str
    email: str
    age: int

    class Settings:
        name = "sync_users"


class SyncPostModel(SyncDocument):
    title: str
    user_id: str | None = None

    class Settings:
        name = "sync_posts"
