# ruff: noqa: D100, D101, D102, D103
"""Tests for nested field access in Beanie repositories and controllers."""

import pytest

from axiom.core.exceptions.http import ValidationError
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator
from axiom.oltp.beanie.base.controller.async_ import AsyncBeanieController
from axiom.oltp.beanie.base.repository.async_ import AsyncBeanieRepository
from axiom.oltp.beanie.base.utils import resolve_nested_field_type, validate_nested_field
from tests.fixtures.models import CommentDocument, PostDocument, UserDocument


class TestNestedFieldUtils:
    """Test utility functions for nested field resolution in Beanie."""

    def test_resolve_nested_field_type_single_level(self):
        """Test getting type of a single-level field."""
        field_type = resolve_nested_field_type(UserDocument, "name")
        assert field_type is str

    def test_resolve_nested_field_type_two_levels(self):
        """Test getting type of a two-level nested field."""
        # PostDocument.user is Link[UserDocument], so user.email should be str
        field_type = resolve_nested_field_type(PostDocument, "user.email")
        assert field_type is str

    def test_resolve_nested_field_type_three_levels(self):
        """Test getting type of a three-level nested field."""
        # CommentDocument.post is Link[PostDocument], post.user is Link[UserDocument]
        field_type = resolve_nested_field_type(CommentDocument, "post.user.age")
        assert field_type is int

    def test_validate_nested_field_valid(self):
        """Test validating a valid nested field value."""
        # Should not raise
        validate_nested_field(PostDocument, "user.name", "Alice")
        validate_nested_field(CommentDocument, "post.user.age", 25)

    def test_validate_nested_field_invalid_type(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Wrong type"):
            validate_nested_field(PostDocument, "user.age", "not_an_int")

    def test_validate_nested_field_none_value(self):
        """Test that None value skips type checking."""
        # Should not raise for None values
        validate_nested_field(PostDocument, "user.name", None)

    def test_resolve_nested_field_type_invalid_field(self):
        """Test that invalid field raises ValueError."""
        with pytest.raises(ValueError, match="has no field"):
            resolve_nested_field_type(UserDocument, "nonexistent")

    def test_validate_nested_field_link_type(self):
        """Test that Link types are handled correctly."""
        # Link fields should not raise validation errors for None
        # Direct Link field validation skips type checking
        validate_nested_field(PostDocument, "user", None)
        # And should handle Link type without error for actual Link instances
        # (Beanie handles Link validation at the Pydantic level)


@pytest.mark.asyncio
class TestNestedFieldRepository:
    """Test nested field access in Beanie repository layer."""

    @pytest.fixture
    async def repo(self, session, beanie_init):
        return AsyncBeanieRepository(model=CommentDocument, db_session=session)

    @pytest.fixture
    async def controller(self, session, beanie_init):
        repo = AsyncBeanieRepository(model=CommentDocument, db_session=session)
        return AsyncBeanieController(
            model=CommentDocument,
            repository=repo,
            exclude_fields=[],
        )

    @pytest.fixture
    async def setup_data(self, beanie_init):
        """Create test data with nested relationships."""
        user = UserDocument(name="John", email="john@example.com", age=30)
        await user.insert()

        post = PostDocument(title="Test Post", content="Test content", user=user)
        await post.insert()

        comment = CommentDocument(text="Great post!", rating=5, post=post)
        await comment.insert()

        return user, post, comment

    async def test_validate_nested_field_in_update(self, repo, setup_data):
        """Test that nested field validation works in update."""
        user, post, comment = setup_data

        # This should work - updating a regular field
        updated = await repo.update(comment, {"rating": 10})
        assert updated.rating == 10

    async def test_get_model_field_type_nested(self, repo):
        """Test _get_model_field_type with nested paths."""
        field_type = repo._get_model_field_type(CommentDocument, "post.user.age")
        assert field_type is int

    async def test_validate_params_nested_valid(self, repo):
        """Test _validate_params with valid nested field."""
        # Should not raise
        repo._validate_params("post.user.name", "Alice")
        repo._validate_params("post.user.age", 25)

    async def test_validate_params_nested_invalid(self, repo):
        """Test _validate_params with invalid nested field type."""
        with pytest.raises(ValidationError, match="Wrong type"):
            repo._validate_params("post.user.age", "not_an_int")

    async def test_resolve_field_relation_nested(self, repo):
        """Test _resolve_field_relation with nested paths."""
        # Test with post.user.name path from CommentDocument
        model, column = repo._resolve_field_relation("post.user.name")
        # Should resolve to UserDocument
        assert model is UserDocument
        assert column == "name"

        # Test simpler path
        model2, column2 = repo._resolve_field_relation("post.title")
        assert model2 is PostDocument
        assert column2 == "title"


@pytest.mark.asyncio
class TestNestedFieldController:
    """Test nested field access in Beanie controller layer."""

    @pytest.fixture
    async def controller(self, session, beanie_init):
        repo = AsyncBeanieRepository(model=CommentDocument, db_session=session)
        return AsyncBeanieController(
            model=CommentDocument,
            repository=repo,
            exclude_fields=[],
        )

    @pytest.fixture
    async def setup_data(self, beanie_init):
        """Create test data with nested relationships."""
        user = UserDocument(name="Jane", email="jane@example.com", age=25)
        await user.insert()

        post = PostDocument(title="Another Post", content="More content", user=user)
        await post.insert()

        comment = CommentDocument(text="Nice!", rating=4, post=post)
        await comment.insert()

        return user, post, comment

    async def test_update_by_filters_validation(self, controller, setup_data):
        """Test update_by_filters validates field types."""
        user, post, comment = setup_data

        # Valid update using a simple field filter
        result = await controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(
                    field="id",
                    value=str(comment.id),
                    operator=QueryOperator.EQUALS,
                ),
            ),
            attributes={"rating": 5},
        )

        assert isinstance(result, list)
        assert len(result) >= 1

    async def test_update_invalid_type_raises(self, controller, setup_data):
        """Test that updating with invalid type raises ValidationError."""
        user, post, comment = setup_data

        # Beanie/Pydantic validates at the document level, so this will raise
        # during the update call when Pydantic tries to validate
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            await controller.update_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="id",
                        value=str(comment.id),
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                attributes={"rating": "invalid"},
            )


class TestDeepNestedFieldAccess:
    """Test very deep nested field access (3+ levels) in Beanie."""

    def test_resolve_three_levels(self):
        """Test resolving three-level nested path."""
        # comment -> post -> user -> name
        field_type = resolve_nested_field_type(CommentDocument, "post.user.name")
        assert field_type is str

    def test_validate_deep_nested(self):
        """Test validation of deeply nested fields."""
        # Three levels: comment.post.user.age
        validate_nested_field(CommentDocument, "post.user.age", 30)

        with pytest.raises(ValueError, match="Wrong type"):
            validate_nested_field(CommentDocument, "post.user.age", "thirty")

    def test_resolve_nested_field_type_optional_link(self):
        """Test resolving nested field through Optional Link."""
        # PostDocument.user is Optional[Link[UserDocument]]
        field_type = resolve_nested_field_type(PostDocument, "user.email")
        assert field_type is str
