# ruff: noqa: D100, D101, D102
"""Test SQLAlchemy models."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.oltp.sqlalchemy.base.declarative import Base
from axiom.oltp.sqlalchemy.base.mixin.as_dict import AsDictMixin
from axiom.oltp.sqlalchemy.base.mixin.timestamp import TimestampMixin


class UserModel(AsDictMixin, TimestampMixin, Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    age: Mapped[int] = mapped_column(Integer)
    posts: Mapped[list["PostModel"]] = relationship("PostModel", back_populates="user")


class PostModel(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_model.id"))
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="posts", lazy="selectin")
    comments: Mapped[list["CommentModel"]] = relationship("CommentModel", back_populates="post")


class CommentModel(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(500))
    rating: Mapped[int] = mapped_column(Integer, default=0)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("post_model.id"))
    post: Mapped["PostModel"] = relationship(
        "PostModel",
        back_populates="comments",
        lazy="selectin",
    )


class TagModel(Base):
    """Model with no unique constraints — used to test create_or_update_by fallback."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(50))
