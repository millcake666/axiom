# ruff: noqa: D103
"""Pytest configuration and fixtures for axiom-sqlalchemy tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from axiom.oltp.sqlalchemy.base.declarative import Base
from tests.fixtures.models import (  # noqa: F401 — register tables
    CommentModel,
    PostModel,
    TagModel,
    UserModel,
)

_ASYNC_URL = "sqlite+aiosqlite:///:memory:"
_SYNC_URL = "sqlite:///:memory:"


@pytest.fixture
async def async_engine():
    engine = create_async_engine(_ASYNC_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
def sync_engine():
    engine = create_engine(_SYNC_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sync_session(sync_engine):
    factory = sessionmaker(sync_engine, expire_on_commit=False)
    with factory() as session:
        yield session
