# ruff: noqa: D103
"""Test fixtures for axiom-beanie integration tests."""

import mongomock
import pytest
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient

from tests.fixtures.models import CommentDocument, PostDocument, UserDocument

# Patch mongomock Database.list_collection_names to accept extra kwargs
# that beanie passes (authorizedCollections, nameOnly) which mongomock ignores.
_original_list_collection_names = mongomock.Database.list_collection_names


def _patched_list_collection_names(self, session=None, **_kwargs):  # noqa: ANN001, ANN201
    return _original_list_collection_names(self, session=session)


mongomock.Database.list_collection_names = _patched_list_collection_names


@pytest.fixture
async def motor_client():
    client = AsyncMongoMockClient()
    yield client
    client.close()


@pytest.fixture
async def beanie_init(motor_client):
    await init_beanie(
        database=motor_client.get_database("test_db"),
        document_models=[UserDocument, PostDocument, CommentDocument],
    )
    yield
    await UserDocument.find_all().delete()
    await PostDocument.find_all().delete()
    await CommentDocument.find_all().delete()


@pytest.fixture
def session():
    return None


@pytest.fixture
def sync_db():
    client = mongomock.MongoClient()
    db = client["test_sync_db"]
    yield db
    for col in db.list_collection_names():
        db[col].delete_many({})
    client.close()
