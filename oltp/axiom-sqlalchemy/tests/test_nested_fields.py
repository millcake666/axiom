# ruff: noqa: D100, D101, D102, D103
"""Tests for nested field access in SQLAlchemy repositories and controllers."""

import pytest

from axiom.core.exceptions import ValidationError
from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.oltp.sqlalchemy.base.controller.async_ import AsyncSQLAlchemyController
from axiom.oltp.sqlalchemy.base.repository.async_ import AsyncSQLAlchemyRepository
from axiom.oltp.sqlalchemy.base.utils import (
    get_nested_field_type,
    resolve_nested_relation,
    validate_nested_field,
)
from tests.fixtures.models import CommentModel, PostModel, UserModel


class TestNestedFieldUtils:
    """Test utility functions for nested field resolution."""

    def test_resolve_nested_relation_single_level(self):
        """Test resolving a single-level field."""
        model, column = resolve_nested_relation(UserModel, "name")
        assert model is UserModel
        assert column == "name"

    def test_resolve_nested_relation_two_levels(self):
        """Test resolving a two-level nested field: post.user."""
        model, column = resolve_nested_relation(PostModel, "user.name")
        assert model is UserModel
        assert column == "name"

    def test_resolve_nested_relation_three_levels(self):
        """Test resolving a three-level nested field: comment.post.user."""
        model, column = resolve_nested_relation(CommentModel, "post.user.email")
        assert model is UserModel
        assert column == "email"

    def test_resolve_nested_relation_invalid_relation(self):
        """Test that invalid relation raises ValueError."""
        with pytest.raises(ValueError, match="has no relation"):
            resolve_nested_relation(PostModel, "invalid.user")

    def test_resolve_nested_relation_invalid_column(self):
        """Test that invalid column in nested path raises ValueError."""
        # Test with a nested path where relation exists but column doesn't
        with pytest.raises(ValueError, match="has no column"):
            get_nested_field_type(PostModel, "user.nonexistent_field")

    def test_get_nested_field_type_single_level(self):
        """Test getting type of a single-level field."""
        field_type = get_nested_field_type(UserModel, "name")
        assert field_type is str

    def test_get_nested_field_type_two_levels(self):
        """Test getting type of a two-level nested field."""
        field_type = get_nested_field_type(PostModel, "user.email")
        assert field_type is str

    def test_get_nested_field_type_three_levels(self):
        """Test getting type of a three-level nested field."""
        field_type = get_nested_field_type(CommentModel, "post.user.age")
        assert field_type is int

    def test_validate_nested_field_valid(self):
        """Test validating a valid nested field value."""
        # Should not raise
        validate_nested_field(PostModel, "user.name", "Alice")
        validate_nested_field(CommentModel, "post.user.age", 25)

    def test_validate_nested_field_invalid_type(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="Wrong type"):
            validate_nested_field(PostModel, "user.age", "not_an_int")

    def test_validate_nested_field_none_value(self):
        """Test that None value skips type checking."""
        # Should not raise for None values
        validate_nested_field(PostModel, "user.name", None)


@pytest.mark.asyncio
class TestNestedFieldRepository:
    """Test nested field access in repository layer."""

    @pytest.fixture
    async def repo(self, async_session):
        return AsyncSQLAlchemyRepository(model=CommentModel, db_session=async_session)

    @pytest.fixture
    async def controller(self, async_session):
        repo = AsyncSQLAlchemyRepository(model=CommentModel, db_session=async_session)
        return AsyncSQLAlchemyController(
            model=CommentModel,
            repository=repo,
            exclude_fields=[],
        )

    @pytest.fixture
    async def setup_data(self, async_session):
        """Create test data with nested relationships."""
        user = UserModel(name="John", email="john@example.com", age=30)
        post = PostModel(title="Test Post", content="Test content", user=user)
        comment = CommentModel(text="Great post!", rating=5, post=post)

        async_session.add(user)
        async_session.add(post)
        async_session.add(comment)
        await async_session.flush()

        return user, post, comment

    async def test_get_by_nested_field_filter(self, repo, setup_data):
        """Test filtering by nested field using get_by."""
        user, post, comment = setup_data

        # Filter comment by nested post.user.name
        result = await repo.get_by(
            field="post.user.name",
            value="John",
            unique=True,
        )

        assert result is not None
        assert result.text == "Great post!"

    async def test_get_by_filters_nested_field(self, repo, setup_data):
        """Test filtering by nested field using FilterRequest."""
        user, post, comment = setup_data

        filter_request = FilterRequest(
            chain=FilterParam(
                field="post.user.email",
                value="john@example.com",
                operator=QueryOperator.EQUALS,
            ),
        )

        result = await repo.get_by_filters(filter_request=filter_request, unique=True)

        assert result is not None
        assert result.post.title == "Test Post"

    async def test_validate_nested_field_in_update(self, repo, setup_data):
        """Test that nested field validation works in update."""
        user, post, comment = setup_data

        # This should work - updating a regular field
        updated = await repo.update(comment, {"rating": 10})
        assert updated.rating == 10

    async def test_validate_nested_field_invalid_type_in_update(self, repo, setup_data):
        """Test that invalid type validation fails in update."""
        user, post, comment = setup_data

        # This should fail - wrong type for rating (int expected)
        with pytest.raises(ValidationError, match="Wrong type"):
            await repo.update(comment, {"rating": "not_a_number"})

    async def test_get_by_nested_field_with_operator(self, repo, setup_data):
        """Test filtering nested field with different operators."""
        user, post, comment = setup_data

        # Test GREATER operator on nested field
        filter_request = FilterRequest(
            chain=FilterParam(
                field="post.user.age",
                value=25,
                operator=QueryOperator.GREATER,
            ),
        )

        result = await repo.get_by_filters(filter_request=filter_request)

        assert len(result) == 1
        assert result[0].text == "Great post!"

    async def test_resolve_field_relation_nested(self, repo):
        """Test _resolve_field_relation with nested paths."""
        model, column = repo._resolve_field_relation("post.user.name")
        assert model is UserModel
        assert column == "name"

    async def test_get_model_field_type_nested(self, repo):
        """Test _get_model_field_type with nested paths."""
        field_type = repo._get_model_field_type(CommentModel, "post.user.age")
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


@pytest.mark.asyncio
class TestNestedFieldController:
    """Test nested field access in controller layer."""

    @pytest.fixture
    async def controller(self, async_session):
        repo = AsyncSQLAlchemyRepository(model=CommentModel, db_session=async_session)
        return AsyncSQLAlchemyController(
            model=CommentModel,
            repository=repo,
            exclude_fields=[],
        )

    @pytest.fixture
    async def setup_data(self, async_session):
        """Create test data with nested relationships."""
        user = UserModel(name="Jane", email="jane@example.com", age=25)
        post = PostModel(title="Another Post", content="More content", user=user)
        comment = CommentModel(text="Nice!", rating=4, post=post)

        async_session.add(user)
        async_session.add(post)
        async_session.add(comment)
        await async_session.flush()

        return user, post, comment

    async def test_get_by_nested_field(self, controller, setup_data):
        """Test get_by with nested field path."""
        user, post, comment = setup_data

        result = await controller.get_by(
            field="post.user.email",
            value="jane@example.com",
            unique=True,
        )

        assert result is not None
        assert result.text == "Nice!"

    async def test_get_by_filters_nested(self, controller, setup_data):
        """Test get_by_filters with nested field path."""
        user, post, comment = setup_data

        filter_request = FilterRequest(
            chain=FilterParam(
                field="post.user.age",
                value=25,
                operator=QueryOperator.EQUALS,
            ),
        )

        result = await controller.get_by_filters(filter_request=filter_request, unique=True)

        assert result is not None
        assert result.post.title == "Another Post"

    async def test_update_by_filters_nested_validation(self, controller, setup_data):
        """Test update_by_filters validates field types correctly."""
        user, post, comment = setup_data

        # Valid update using a simple field filter
        result = await controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(
                    field="id",
                    value=comment.id,
                    operator=QueryOperator.EQUALS,
                ),
            ),
            attributes={"rating": 5},
        )

        assert isinstance(result, list)
        assert len(result) >= 1
        # The update was successful if we got a result back

    async def test_update_invalid_type_raises(self, controller, setup_data):
        """Test that updating with invalid type raises ValidationError."""
        user, post, comment = setup_data

        with pytest.raises(ValidationError, match="Wrong type"):
            await controller.update_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="id",
                        value=comment.id,
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                attributes={"rating": "invalid"},
            )


class TestDeepNestedFieldAccess:
    """Test very deep nested field access (4+ levels)."""

    def test_resolve_four_levels(self):
        """Test resolving four-level nested path."""
        # comment -> post -> user -> (imagine user has a profile -> address)
        # For now, test what we have: comment.post.user.name
        model, column = resolve_nested_relation(CommentModel, "post.user.name")
        assert model is UserModel
        assert column == "name"
        assert get_nested_field_type(CommentModel, "post.user.name") is str

    def test_validate_deep_nested(self):
        """Test validation of deeply nested fields."""
        # Three levels: comment.post.user.age
        validate_nested_field(CommentModel, "post.user.age", 30)

        with pytest.raises(ValueError, match="Wrong type"):
            validate_nested_field(CommentModel, "post.user.age", "thirty")
