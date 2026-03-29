# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for AsyncSQLiteRepository (and AsyncSQLAlchemyRepository base)."""

import pytest

from axiom.core.exceptions import BadRequestError, ValidationError
from axiom.core.filter import (
    FilterGroup,
    FilterParam,
    FilterRequest,
    FilterType,
    QueryOperator,
    SortTypeEnum,
)
from axiom.oltp.sqlalchemy.sqlite.repository.async_ import AsyncSQLiteRepository
from tests.fixtures.models import PostModel, TagModel, UserModel


@pytest.fixture
def repo(async_session):
    return AsyncSQLiteRepository(model=UserModel, db_session=async_session)


@pytest.fixture
def post_repo(async_session):
    return AsyncSQLiteRepository(model=PostModel, db_session=async_session)


class TestAsyncRepository:
    async def test_create(self, repo):
        user = await repo.create({"name": "Alice", "email": "alice@test.com", "age": 30})
        await repo.session.flush()
        assert user.name == "Alice"
        assert user.id is not None

    async def test_create_many(self, repo):
        users = await repo.create_many(
            [
                {"name": "Bob", "email": "bob@test.com", "age": 25},
                {"name": "Charlie", "email": "charlie@test.com", "age": 35},
            ],
        )
        await repo.session.flush()
        assert len(users) == 2
        assert all(u.id is not None for u in users)

    async def test_create_many_empty(self, repo):
        result = await repo.create_many([])
        assert result == []

    async def test_get_all(self, repo):
        await repo.create({"name": "D1", "email": "d1@test.com", "age": 40})
        await repo.create({"name": "D2", "email": "d2@test.com", "age": 28})
        await repo.session.flush()
        results = await repo.get_all(skip=0, limit=10)
        assert len(results) >= 2

    async def test_get_all_default_sort_by_updated_at(self, repo):
        # UserModel has updated_at so _sort_by defaults to it
        await repo.create({"name": "Sort1", "email": "s1@test.com", "age": 1})
        await repo.create({"name": "Sort2", "email": "s2@test.com", "age": 2})
        await repo.session.commit()
        results = await repo.get_all()
        assert len(results) >= 2

    async def test_get_by_field_equals(self, repo):
        await repo.create({"name": "Frank", "email": "frank@test.com", "age": 22})
        await repo.session.flush()
        results = await repo.get_by(field="name", value="Frank")
        assert isinstance(results, list)
        assert any(u.name == "Frank" for u in results)

    async def test_get_by_field_in(self, repo):
        await repo.create_many(
            [
                {"name": "G1", "email": "g1@test.com", "age": 10},
                {"name": "G2", "email": "g2@test.com", "age": 20},
                {"name": "G3", "email": "g3@test.com", "age": 30},
            ],
        )
        await repo.session.flush()
        results = await repo.get_by(field="name", value=["G1", "G2"], operator=QueryOperator.IN)
        assert len(results) == 2

    async def test_get_by_field_not_in(self, repo):
        await repo.create_many(
            [
                {"name": "H1", "email": "h1@test.com", "age": 11},
                {"name": "H2", "email": "h2@test.com", "age": 12},
            ],
        )
        await repo.session.flush()
        results = await repo.get_by(field="name", value=["H1"], operator=QueryOperator.NOT_IN)
        assert all(u.name != "H1" for u in results)

    async def test_get_by_field_not_equal(self, repo):
        await repo.create_many(
            [
                {"name": "I1", "email": "i1@test.com", "age": 13},
                {"name": "I2", "email": "i2@test.com", "age": 14},
            ],
        )
        await repo.session.flush()
        results = await repo.get_by(field="name", value="I1", operator=QueryOperator.NOT_EQUAL)
        assert all(u.name != "I1" for u in results)

    async def test_get_by_field_greater(self, repo):
        await repo.create_many(
            [
                {"name": "J1", "email": "j1@test.com", "age": 5},
                {"name": "J2", "email": "j2@test.com", "age": 50},
            ],
        )
        await repo.session.flush()
        results = await repo.get_by(field="age", value=10, operator=QueryOperator.GREATER)
        assert all(u.age > 10 for u in results)

    async def test_get_by_field_less(self, repo):
        await repo.create_many(
            [
                {"name": "K1", "email": "k1@test.com", "age": 5},
                {"name": "K2", "email": "k2@test.com", "age": 50},
            ],
        )
        await repo.session.flush()
        results = await repo.get_by(field="age", value=10, operator=QueryOperator.LESS)
        assert all(u.age < 10 for u in results)

    async def test_get_by_field_gte(self, repo):
        await repo.create({"name": "L1", "email": "l1@test.com", "age": 10})
        await repo.session.flush()
        results = await repo.get_by(field="age", value=10, operator=QueryOperator.EQUALS_OR_GREATER)
        assert all(u.age >= 10 for u in results)

    async def test_get_by_field_lte(self, repo):
        await repo.create({"name": "L2", "email": "l2@test.com", "age": 20})
        await repo.session.flush()
        results = await repo.get_by(field="age", value=20, operator=QueryOperator.EQUALS_OR_LESS)
        assert all(u.age <= 20 for u in results)

    async def test_get_by_field_starts_with(self, repo):
        await repo.create({"name": "StartMe", "email": "sw@test.com", "age": 1})
        await repo.session.flush()
        results = await repo.get_by(field="name", value="Start", operator=QueryOperator.STARTS_WITH)
        assert any(u.name.startswith("Start") for u in results)

    async def test_get_by_field_not_starts_with(self, repo):
        await repo.create({"name": "AlphaX", "email": "ax@test.com", "age": 4})
        await repo.session.flush()
        results = await repo.get_by(
            field="name",
            value="Beta",
            operator=QueryOperator.NOT_START_WITH,
        )
        assert all(not u.name.startswith("Beta") for u in results)

    async def test_get_by_field_ends_with(self, repo):
        await repo.create({"name": "EndMe", "email": "ew@test.com", "age": 2})
        await repo.session.flush()
        results = await repo.get_by(field="name", value="Me", operator=QueryOperator.ENDS_WITH)
        assert any(u.name.endswith("Me") for u in results)

    async def test_get_by_field_not_ends_with(self, repo):
        await repo.create({"name": "GammaZ", "email": "gz@test.com", "age": 5})
        await repo.session.flush()
        results = await repo.get_by(field="name", value="Q", operator=QueryOperator.NOT_END_WITH)
        assert all(not u.name.endswith("Q") for u in results)

    async def test_get_by_field_contains(self, repo):
        await repo.create({"name": "ContainMe", "email": "cm@test.com", "age": 3})
        await repo.session.flush()
        results = await repo.get_by(field="name", value="ntain", operator=QueryOperator.CONTAINS)
        assert any("ntain" in u.name for u in results)

    async def test_get_by_field_not_contains(self, repo):
        await repo.create({"name": "DeltaQ", "email": "dq@test.com", "age": 6})
        await repo.session.flush()
        results = await repo.get_by(field="name", value="ZZZ", operator=QueryOperator.NOT_CONTAIN)
        assert all("ZZZ" not in u.name for u in results)

    async def test_get_by_unique_found(self, repo):
        await repo.create({"name": "Unique1", "email": "uniq1@test.com", "age": 99})
        await repo.session.flush()
        result = await repo.get_by(field="name", value="Unique1", unique=True)
        assert result is not None
        assert result.name == "Unique1"

    async def test_get_by_unique_not_found(self, repo):
        result = await repo.get_by(field="name", value="no_such_xyz", unique=True)
        assert result is None

    async def test_get_by_filters_and(self, repo):
        await repo.create({"name": "M1", "email": "m1@test.com", "age": 25})
        await repo.create({"name": "M2", "email": "m2@test.com", "age": 35})
        await repo.session.flush()
        fr = FilterRequest(
            chain=FilterGroup(
                type=FilterType.AND,
                items=[
                    FilterParam(field="name", value="M1", operator=QueryOperator.EQUALS),
                    FilterParam(field="age", value=25, operator=QueryOperator.EQUALS),
                ],
            ),
        )
        results = await repo.get_by_filters(filter_request=fr)
        assert len(results) == 1
        assert results[0].name == "M1"

    async def test_get_by_filters_or(self, repo):
        await repo.create({"name": "N1", "email": "n1@test.com", "age": 1})
        await repo.create({"name": "N2", "email": "n2@test.com", "age": 2})
        await repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="N1", operator=QueryOperator.EQUALS)
            | FilterParam(field="name", value="N2", operator=QueryOperator.EQUALS),
        )
        results = await repo.get_by_filters(filter_request=fr)
        assert len(results) == 2

    async def test_get_by_filters_none(self, repo):
        await repo.create({"name": "R1", "email": "r1@test.com", "age": 200})
        await repo.session.flush()
        results = await repo.get_by_filters(filter_request=None)
        assert isinstance(results, list)
        assert any(u.name == "R1" for u in results)

    async def test_get_by_filters_unique_found(self, repo):
        await repo.create({"name": "S1uniq", "email": "s1u@test.com", "age": 201})
        await repo.session.flush()
        result = await repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="S1uniq", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result is not None
        assert result.name == "S1uniq"

    async def test_get_by_filters_unique_not_found(self, repo):
        result = await repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="no_such_xyz", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result is None

    async def test_count(self, repo):
        await repo.create({"name": "C1", "email": "c1@test.com", "age": 100})
        await repo.create({"name": "C2", "email": "c2@test.com", "age": 101})
        await repo.session.flush()
        total = await repo.count()
        assert total >= 2

    async def test_count_with_filter(self, repo):
        await repo.create({"name": "CV1unique", "email": "cv1@test.com", "age": 27})
        await repo.session.flush()
        cnt = await repo.count(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="CV1unique", operator=QueryOperator.EQUALS),
            ),
        )
        assert cnt == 1

    async def test_sort_asc(self, repo):
        await repo.create_many(
            [
                {"name": "W1", "email": "w1@test.com", "age": 30},
                {"name": "W2", "email": "w2@test.com", "age": 10},
                {"name": "W3", "email": "w3@test.com", "age": 20},
            ],
        )
        await repo.session.flush()
        results = await repo.get_all(sort_by="age", sort_type=SortTypeEnum.asc)
        ages = [u.age for u in results]
        assert ages == sorted(ages)

    async def test_sort_desc(self, repo):
        await repo.create_many(
            [
                {"name": "X1", "email": "x1@test.com", "age": 10},
                {"name": "X2", "email": "x2@test.com", "age": 30},
            ],
        )
        await repo.session.flush()
        results = await repo.get_all(sort_by="age", sort_type=SortTypeEnum.desc)
        ages = [u.age for u in results]
        assert ages == sorted(ages, reverse=True)

    async def test_paginate(self, repo):
        for i in range(5):
            await repo.create({"name": f"P{i}", "email": f"p{i}@test.com", "age": i})
        await repo.session.flush()
        page1 = await repo.get_all(skip=0, limit=2, sort_by="age", sort_type=SortTypeEnum.asc)
        page2 = await repo.get_all(skip=2, limit=2, sort_by="age", sort_type=SortTypeEnum.asc)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].age != page2[0].age

    async def test_update(self, repo):
        user = await repo.create({"name": "O1", "email": "o1@test.com", "age": 20})
        await repo.session.flush()
        updated = await repo.update(user, {"age": 99})
        assert updated.age == 99
        assert updated.name == "O1"

    async def test_update_wrong_type(self, repo):
        user = await repo.create({"name": "OWT", "email": "owt@test.com", "age": 20})
        await repo.session.flush()
        with pytest.raises(ValidationError):
            await repo.update(user, {"name": 123})

    async def test_update_by(self, repo):
        await repo.create({"name": "UB1", "email": "ub1@test.com", "age": 21})
        await repo.session.flush()
        result = await repo.update_by(field="name", value="UB1", attributes={"age": 88})
        assert isinstance(result, list)
        assert result[0].age == 88

    async def test_update_by_unique(self, repo):
        await repo.create({"name": "UBU1", "email": "ubu1@test.com", "age": 32})
        await repo.session.flush()
        result = await repo.update_by(
            field="name",
            value="UBU1",
            attributes={"age": 77},
            unique=True,
        )
        assert result is not None
        assert result.age == 77

    async def test_update_by_unique_not_found(self, repo):
        result = await repo.update_by(
            field="name",
            value="no_such",
            attributes={"age": 1},
            unique=True,
        )
        assert result is None

    async def test_update_by_filters(self, repo):
        await repo.create({"name": "UBF1", "email": "ubf1@test.com", "age": 300})
        await repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="UBF1", operator=QueryOperator.EQUALS),
        )
        result = await repo.update_by_filters(filter_request=fr, attributes={"age": 301})
        assert isinstance(result, list)
        assert result[0].age == 301

    async def test_update_by_filters_unique(self, repo):
        await repo.create({"name": "UBF2", "email": "ubf2@test.com", "age": 302})
        await repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="UBF2", operator=QueryOperator.EQUALS),
        )
        result = await repo.update_by_filters(
            filter_request=fr,
            attributes={"age": 303},
            unique=True,
        )
        assert result is not None
        assert result.age == 303

    async def test_update_by_filters_unique_not_found(self, repo):
        fr = FilterRequest(
            chain=FilterParam(field="name", value="no_such_xyz", operator=QueryOperator.EQUALS),
        )
        result = await repo.update_by_filters(
            filter_request=fr,
            attributes={"age": 999},
            unique=True,
        )
        assert result is None

    async def test_delete(self, repo):
        user = await repo.create({"name": "Del1", "email": "del1@test.com", "age": 90})
        await repo.session.flush()
        deleted = await repo.delete(user)
        assert deleted.name == "Del1"

    async def test_delete_by(self, repo):
        await repo.create({"name": "DB1", "email": "db1@test.com", "age": 91})
        await repo.session.flush()
        result = await repo.delete_by(field="name", value="DB1")
        assert isinstance(result, list)
        assert result[0].name == "DB1"

    async def test_delete_by_unique(self, repo):
        await repo.create({"name": "DBU1", "email": "dbu1@test.com", "age": 33})
        await repo.session.flush()
        result = await repo.delete_by(field="name", value="DBU1", unique=True)
        assert result is not None
        assert result.name == "DBU1"

    async def test_delete_by_unique_not_found(self, repo):
        result = await repo.delete_by(field="name", value="no_such_xyz", unique=True)
        assert result is None

    async def test_delete_by_filters(self, repo):
        await repo.create({"name": "DBF1", "email": "dbf1@test.com", "age": 310})
        await repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="DBF1", operator=QueryOperator.EQUALS),
        )
        result = await repo.delete_by_filters(filter_request=fr)
        assert isinstance(result, list)
        assert result[0].name == "DBF1"

    async def test_delete_by_filters_unique(self, repo):
        await repo.create({"name": "DBF2", "email": "dbf2@test.com", "age": 311})
        await repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="DBF2", operator=QueryOperator.EQUALS),
        )
        result = await repo.delete_by_filters(filter_request=fr, unique=True)
        assert result is not None
        assert result.name == "DBF2"

    async def test_delete_by_filters_unique_not_found(self, repo):
        fr = FilterRequest(
            chain=FilterParam(field="name", value="no_such_xyz2", operator=QueryOperator.EQUALS),
        )
        result = await repo.delete_by_filters(filter_request=fr, unique=True)
        assert result is None

    async def test_create_or_update_by_create(self, repo):
        user = await repo.create_or_update_by(
            attributes={"name": "Ups1", "email": "ups1@test.com", "age": 28},
        )
        await repo.session.flush()
        assert user is not None
        assert user.name == "Ups1"

    async def test_create_or_update_by_update(self, repo):
        await repo.create_or_update_by(
            attributes={"name": "Ups2", "email": "ups2@test.com", "age": 29},
        )
        await repo.session.commit()
        updated = await repo.create_or_update_by(
            attributes={"name": "Ups2 Updated", "email": "ups2@test.com", "age": 99},
            update_fields=["name", "age"],
        )
        assert updated is not None
        assert updated.age == 99

    async def test_get_by_bad_field_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="nonexistent_field", value="x")

    async def test_get_by_in_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="name", value="not_a_list", operator=QueryOperator.IN)

    async def test_get_by_not_in_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="name", value="not_a_list", operator=QueryOperator.NOT_IN)

    async def test_get_by_starts_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="age", value=123, operator=QueryOperator.STARTS_WITH)

    async def test_get_by_not_starts_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="age", value=123, operator=QueryOperator.NOT_START_WITH)

    async def test_get_by_ends_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="age", value=123, operator=QueryOperator.ENDS_WITH)

    async def test_get_by_not_ends_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="age", value=123, operator=QueryOperator.NOT_END_WITH)

    async def test_get_by_contains_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="age", value=123, operator=QueryOperator.CONTAINS)

    async def test_get_by_not_contains_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_by(field="age", value=123, operator=QueryOperator.NOT_CONTAIN)

    async def test_sort_bad_field_raises(self, repo):
        with pytest.raises(BadRequestError):
            await repo.get_all(sort_by="nonexistent_field")

    async def test_get_deep_unique_from_dict_with_dict(self, repo):
        result = repo._get_deep_unique_from_dict({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    async def test_get_deep_unique_from_dict_with_scalar_list(self, repo):
        result = repo._get_deep_unique_from_dict([1, 2, 2, 3])
        assert result == [1, 2, 3]

    async def test_get_deep_unique_from_dict_with_list_of_dicts(self, repo):
        data = [{"key": "val1"}, {"key": "val1"}, {"key": "val2"}]
        result = repo._get_deep_unique_from_dict(data)
        assert isinstance(result, dict)
        assert "key" in result
        assert "val1" in result["key"]
        assert "val2" in result["key"]
        assert result["key"].count("val1") == 1

    async def test_get_deep_unique_from_dict_with_scalar(self, repo):
        assert repo._get_deep_unique_from_dict(42) == 42
        assert repo._get_deep_unique_from_dict("hello") == "hello"

    async def test_validate_params_valid(self, repo):
        user = await repo.create({"name": "VP1", "email": "vp1@test.com", "age": 40})
        await repo.session.flush()
        # Should not raise
        await repo.update(user, {"name": "VP1 Updated"})
        assert user.name == "VP1 Updated"

    async def test_validate_params_wrong_relation_raises(self, repo):
        user = await repo.create({"name": "VR1", "email": "vr1@test.com", "age": 41})
        await repo.session.flush()
        with pytest.raises(ValidationError):
            await repo.update(user, {"nonexistent": "value"})

    async def test_resolve_field_relation_dot_notation(self, post_repo):
        # PostModel.user.name — resolves relation, then column
        model, col = post_repo._resolve_field_relation("user.name")
        assert col == "name"

    async def test_resolve_field_relation_bad_relation_raises(self, repo):
        with pytest.raises(ValidationError):
            repo._resolve_field_relation("bad_relation.name")

    async def test_maybe_join_no_dot(self, repo):
        query = repo._query()
        result = repo._maybe_join(query, "name")
        assert result is not None

    async def test_maybe_join_with_dot(self, post_repo):
        query = post_repo._query()
        result = post_repo._maybe_join(query, "user.name")
        assert result is not None

    async def test_get_by_dot_notation(self, async_session):
        # Test filtering PostModel by user.name via join
        user_repo = AsyncSQLiteRepository(model=UserModel, db_session=async_session)
        p_repo = AsyncSQLiteRepository(model=PostModel, db_session=async_session)

        user = await user_repo.create({"name": "Dot1", "email": "dot1@test.com", "age": 50})
        await async_session.flush()
        await p_repo.create({"title": "Post1", "user_id": user.id})
        await async_session.flush()

        results = await p_repo.get_by(field="user.name", value="Dot1")
        assert isinstance(results, list)
        assert any(p.title == "Post1" for p in results)

    async def test_get_conflict_fields(self, repo):
        conflict_fields = repo._get_conflict_fields()
        assert "email" in conflict_fields

    async def test_get_model_field_type(self, repo):
        field_type = repo._get_model_field_type(UserModel, "name")
        assert field_type is str

    async def test_paginate_no_limit(self, repo):
        # limit = -1 means no limit
        for i in range(3):
            await repo.create({"name": f"NL{i}", "email": f"nl{i}@test.com", "age": i})
        await repo.session.flush()
        results = await repo.get_all(limit=-1)
        assert len(results) >= 3

    async def test_create_or_update_by_no_conflict_cols(self, async_session):
        # TagModel has no unique constraints — exercises the fallback create path
        tag_repo = AsyncSQLiteRepository(model=TagModel, db_session=async_session)
        tag = await tag_repo.create_or_update_by(attributes={"label": "python"})
        await async_session.flush()
        assert tag is not None
        assert tag.label == "python"
