# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for AsyncBeanieRepository."""

import pytest

from axiom.core.filter import (
    FilterGroup,
    FilterParam,
    FilterRequest,
    FilterType,
    QueryOperator,
    SortTypeEnum,
)
from axiom.oltp.beanie.base.repository.async_ import AsyncBeanieRepository
from tests.fixtures.models import UserDocument


@pytest.fixture
def repo(session):
    return AsyncBeanieRepository(model=UserDocument, db_session=session)


@pytest.mark.usefixtures("beanie_init")
class TestRepository:
    async def test_create(self, repo):
        user = await repo.create({"name": "Alice", "email": "alice@example.com", "age": 30})
        assert user.name == "Alice"
        assert user.id is not None

    async def test_create_many(self, repo):
        users = await repo.create_many(
            [
                {"name": "Bob", "email": "bob@example.com", "age": 25},
                {"name": "Charlie", "email": "charlie@example.com", "age": 35},
            ],
        )
        assert len(users) == 2

    async def test_get_all(self, repo):
        await repo.create({"name": "Dave", "email": "dave@example.com", "age": 40})
        await repo.create({"name": "Eve", "email": "eve@example.com", "age": 28})
        results = await repo.get_all(skip=0, limit=10)
        assert len(results) >= 2

    async def test_get_by_field(self, repo):
        await repo.create({"name": "Frank", "email": "frank@example.com", "age": 22})
        results = await repo.get_by(field="name", value="Frank")
        assert isinstance(results, list)
        assert any(u.name == "Frank" for u in results)

    async def test_get_by_field_operators(self, repo):
        await repo.create_many(
            [
                {"name": "G1", "email": "g1@example.com", "age": 10},
                {"name": "G2", "email": "g2@example.com", "age": 20},
                {"name": "G3", "email": "g3@example.com", "age": 30},
            ],
        )
        # IN
        results = await repo.get_by(field="name", value=["G1", "G2"], operator=QueryOperator.IN)
        assert len(results) == 2
        # NOT_IN
        results = await repo.get_by(field="name", value=["G1"], operator=QueryOperator.NOT_IN)
        names = [u.name for u in results]
        assert "G1" not in names
        # NOT_EQUAL
        results = await repo.get_by(field="name", value="G1", operator=QueryOperator.NOT_EQUAL)
        assert all(u.name != "G1" for u in results)
        # GREATER
        results = await repo.get_by(field="age", value=15, operator=QueryOperator.GREATER)
        assert all(u.age > 15 for u in results)
        # LESS
        results = await repo.get_by(field="age", value=25, operator=QueryOperator.LESS)
        assert all(u.age < 25 for u in results)

    async def test_get_by_filters_and(self, repo):
        await repo.create({"name": "H1", "email": "h1@example.com", "age": 50})
        await repo.create({"name": "H2", "email": "h2@example.com", "age": 51})
        filter_request = FilterRequest(
            chain=FilterGroup(
                type=FilterType.AND,
                items=[
                    FilterParam(field="name", value="H1", operator=QueryOperator.EQUALS),
                    FilterParam(field="age", value=50, operator=QueryOperator.EQUALS),
                ],
            ),
        )
        results = await repo.get_by_filters(filter_request=filter_request)
        assert isinstance(results, list)
        assert all(u.name == "H1" for u in results)

    async def test_get_by_filters_or(self, repo):
        await repo.create({"name": "I1", "email": "i1@example.com", "age": 60})
        await repo.create({"name": "I2", "email": "i2@example.com", "age": 61})
        filter_request = FilterRequest(
            chain=FilterGroup(
                type=FilterType.OR,
                items=[
                    FilterParam(field="name", value="I1", operator=QueryOperator.EQUALS),
                    FilterParam(field="name", value="I2", operator=QueryOperator.EQUALS),
                ],
            ),
        )
        results = await repo.get_by_filters(filter_request=filter_request)
        assert len(results) == 2

    async def test_update(self, repo):
        user = await repo.create({"name": "J1", "email": "j1@example.com", "age": 70})
        updated = await repo.update(user, {"name": "J1_updated"})
        assert updated.name == "J1_updated"

    async def test_update_by(self, repo):
        await repo.create({"name": "K1", "email": "k1@example.com", "age": 80})
        result = await repo.update_by(field="name", value="K1", attributes={"age": 81})
        assert isinstance(result, list)
        assert result[0].age == 81

    async def test_delete(self, repo):
        user = await repo.create({"name": "L1", "email": "l1@example.com", "age": 90})
        deleted = await repo.delete(user)
        assert deleted.name == "L1"
        found = await repo.get_by(field="name", value="L1")
        assert found == []

    async def test_delete_by(self, repo):
        await repo.create({"name": "M1", "email": "m1@example.com", "age": 91})
        result = await repo.delete_by(field="name", value="M1")
        assert isinstance(result, list)
        found = await repo.get_by(field="name", value="M1")
        assert found == []

    async def test_count(self, repo):
        await repo.create({"name": "N1", "email": "n1@example.com", "age": 100})
        await repo.create({"name": "N2", "email": "n2@example.com", "age": 101})
        total = await repo.count()
        assert total >= 2
        filtered = await repo.count(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="N1", operator=QueryOperator.EQUALS),
            ),
        )
        assert filtered == 1

    async def test_sort_by(self, repo):
        await repo.create({"name": "O1", "email": "o1@example.com", "age": 5})
        await repo.create({"name": "O2", "email": "o2@example.com", "age": 3})
        asc = await repo.get_all(sort_by="age", sort_type=SortTypeEnum.asc)
        ages = [u.age for u in asc]
        assert ages == sorted(ages)
        desc = await repo.get_all(sort_by="age", sort_type=SortTypeEnum.desc)
        ages_desc = [u.age for u in desc]
        assert ages_desc == sorted(ages_desc, reverse=True)

    async def test_paginate(self, repo):
        for i in range(5):
            await repo.create({"name": f"P{i}", "email": f"p{i}@example.com", "age": i})
        page1 = await repo.get_all(skip=0, limit=2)
        page2 = await repo.get_all(skip=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2

    async def test_create_or_update_by(self, repo):
        user = await repo.create_or_update_by(
            attributes={"name": "Q1", "email": "q1@example.com", "age": 110},
        )
        assert user.name == "Q1"
        # Update existing
        updated = await repo.create_or_update_by(
            attributes={"name": "Q1", "email": "q1@example.com", "age": 111},
            update_fields=["age"],
        )
        assert updated.age == 111

    async def test_get_by_filters_none_filter_request(self, repo):
        await repo.create({"name": "R1", "email": "r1@example.com", "age": 200})
        results = await repo.get_by_filters(filter_request=None)
        assert isinstance(results, list)
        assert any(u.name == "R1" for u in results)

    async def test_get_by_filters_unique_found(self, repo):
        await repo.create({"name": "S1unique", "email": "s1@example.com", "age": 201})
        result = await repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="S1unique", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result is not None
        assert result.name == "S1unique"

    async def test_get_by_filters_unique_not_found(self, repo):
        result = await repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(
                    field="name",
                    value="no_such_name_xyz",
                    operator=QueryOperator.EQUALS,
                ),
            ),
            unique=True,
        )
        assert result is None

    async def test_count_with_no_filter(self, repo):
        await repo.create({"name": "T1", "email": "t1@example.com", "age": 202})
        total = await repo.count(filter_request=None)
        assert total >= 1

    async def test_validate_params_is_noop(self, repo):
        # _validate_params is a no-op pass; calling it should not raise
        repo._validate_params("name", "Alice")
        repo._validate_params("age")

    async def test_get_deep_unique_from_dict_with_dict(self, repo):
        result = repo._get_deep_unique_from_dict({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    async def test_get_deep_unique_from_dict_with_list_of_dicts(self, repo):
        # Aggregates dict lists, deduplicating values
        data = [{"key": "val1"}, {"key": "val1"}, {"key": "val2"}]
        result = repo._get_deep_unique_from_dict(data)
        assert isinstance(result, dict)
        assert "key" in result
        assert "val1" in result["key"]
        assert "val2" in result["key"]
        assert result["key"].count("val1") == 1

    async def test_get_deep_unique_from_dict_with_scalar_list(self, repo):
        result = repo._get_deep_unique_from_dict([1, 2, 2, 3])
        assert result == [1, 2, 3]

    async def test_get_deep_unique_from_dict_with_scalar(self, repo):
        assert repo._get_deep_unique_from_dict(42) == 42
        assert repo._get_deep_unique_from_dict("hello") == "hello"

    async def test_get_by_filters_none_unique_true(self, repo):
        # No filter_request, unique=True returns first or none
        result = await repo.get_by_filters(filter_request=None, unique=True)
        # May be None or a model depending on prior inserts — just verify no exception
        assert result is None or hasattr(result, "name")

    async def test_create_many_empty(self, repo):
        # Line 48: empty list returns []
        result = await repo.create_many([])
        assert result == []

    async def test_update_by_filters(self, repo):
        # Line 82: update_by_filters
        await repo.create({"name": "UBF1", "email": "ubf1@example.com", "age": 300})
        filter_request = FilterRequest(
            chain=FilterParam(field="name", value="UBF1", operator=QueryOperator.EQUALS),
        )
        result = await repo.update_by_filters(
            filter_request=filter_request,
            attributes={"age": 301},
        )
        assert isinstance(result, list)
        assert result[0].age == 301

    async def test_update_by_filters_unique(self, repo):
        # unique=True branch in _update_models (lines 251-254)
        await repo.create({"name": "UBF2", "email": "ubf2@example.com", "age": 302})
        filter_request = FilterRequest(
            chain=FilterParam(field="name", value="UBF2", operator=QueryOperator.EQUALS),
        )
        result = await repo.update_by_filters(
            filter_request=filter_request,
            attributes={"age": 303},
            unique=True,
        )
        assert result is not None
        assert result.age == 303

    async def test_update_by_filters_unique_not_found(self, repo):
        # unique=True, model is None branch
        filter_request = FilterRequest(
            chain=FilterParam(field="name", value="no_such_xyz_abc", operator=QueryOperator.EQUALS),
        )
        result = await repo.update_by_filters(
            filter_request=filter_request,
            attributes={"age": 999},
            unique=True,
        )
        assert result is None

    async def test_delete_by_filters(self, repo):
        # Line 112: delete_by_filters
        await repo.create({"name": "DBF1", "email": "dbf1@example.com", "age": 310})
        filter_request = FilterRequest(
            chain=FilterParam(field="name", value="DBF1", operator=QueryOperator.EQUALS),
        )
        result = await repo.delete_by_filters(filter_request=filter_request)
        assert isinstance(result, list)

    async def test_delete_by_filters_unique(self, repo):
        # unique=True branch in _delete_models (lines 270-273)
        await repo.create({"name": "DBF2", "email": "dbf2@example.com", "age": 311})
        filter_request = FilterRequest(
            chain=FilterParam(field="name", value="DBF2", operator=QueryOperator.EQUALS),
        )
        result = await repo.delete_by_filters(filter_request=filter_request, unique=True)
        assert result is not None
        assert result.name == "DBF2"

    async def test_delete_by_filters_unique_not_found(self, repo):
        # unique=True, model is None branch in _delete_models
        filter_request = FilterRequest(
            chain=FilterParam(
                field="name",
                value="no_such_xyz_abc2",
                operator=QueryOperator.EQUALS,
            ),
        )
        result = await repo.delete_by_filters(filter_request=filter_request, unique=True)
        assert result is None

    async def test_get_by_id_field(self, repo):
        # Lines 161-168: ObjectId conversion when field == "id"
        user = await repo.create({"name": "OID1", "email": "oid1@example.com", "age": 320})
        user_id = str(user.id)
        results = await repo.get_by(field="id", value=user_id)
        assert len(results) == 1
        assert results[0].name == "OID1"

    async def test_operators_equals_or_greater(self, repo):
        # Line 182: EQUALS_OR_GREATER
        await repo.create({"name": "OP1", "email": "op1@example.com", "age": 50})
        await repo.create({"name": "OP2", "email": "op2@example.com", "age": 60})
        results = await repo.get_by(field="age", value=50, operator=QueryOperator.EQUALS_OR_GREATER)
        assert all(u.age >= 50 for u in results)

    async def test_operators_equals_or_less(self, repo):
        # Line 185-186: EQUALS_OR_LESS
        await repo.create({"name": "OP3", "email": "op3@example.com", "age": 40})
        results = await repo.get_by(field="age", value=50, operator=QueryOperator.EQUALS_OR_LESS)
        assert all(u.age <= 50 for u in results)

    async def test_operators_starts_with(self, repo):
        # Lines 187-188: STARTS_WITH
        await repo.create({"name": "StartMe", "email": "sw@example.com", "age": 1})
        results = await repo.get_by(field="name", value="Start", operator=QueryOperator.STARTS_WITH)
        assert any(u.name.startswith("Start") for u in results)

    async def test_operators_ends_with(self, repo):
        # Lines 191-192: ENDS_WITH
        await repo.create({"name": "EndMe", "email": "ew@example.com", "age": 2})
        results = await repo.get_by(field="name", value="Me", operator=QueryOperator.ENDS_WITH)
        assert any(u.name.endswith("Me") for u in results)

    async def test_operators_contains(self, repo):
        # Lines 195-196: CONTAINS
        await repo.create({"name": "ContainMe", "email": "cm@example.com", "age": 3})
        results = await repo.get_by(field="name", value="ntain", operator=QueryOperator.CONTAINS)
        assert any("ntain" in u.name for u in results)

    async def test_operators_not_start_with(self, repo):
        # Lines 189-190: NOT_START_WITH
        await repo.create({"name": "AlphaX", "email": "ax@example.com", "age": 4})
        results = await repo.get_by(
            field="name",
            value="Beta",
            operator=QueryOperator.NOT_START_WITH,
        )
        names = [u.name for u in results]
        assert all(not n.startswith("Beta") for n in names)

    async def test_operators_not_end_with(self, repo):
        # Lines 193-194: NOT_END_WITH
        await repo.create({"name": "GammaZ", "email": "gz@example.com", "age": 5})
        results = await repo.get_by(field="name", value="X", operator=QueryOperator.NOT_END_WITH)
        names = [u.name for u in results]
        assert all(not n.endswith("X") for n in names)

    async def test_operators_not_contain(self, repo):
        # Lines 197-198: NOT_CONTAIN
        await repo.create({"name": "DeltaQ", "email": "dq@example.com", "age": 6})
        results = await repo.get_by(field="name", value="ZZZ", operator=QueryOperator.NOT_CONTAIN)
        names = [u.name for u in results]
        assert all("ZZZ" not in n for n in names)

    async def test_create_or_update_by_empty_search_fields(self, repo):
        # Line 135: search_fields empty → existing = None → create
        user = await repo.create_or_update_by(
            attributes={"name": "EmptySF", "email": "esf@example.com", "age": 400},
            update_fields=[
                "name",
                "email",
                "age",
            ],  # all fields in update_fields → search_fields empty
        )
        assert user.name == "EmptySF"

    async def test_maybe_join_with_dot_field(self, repo):
        # Line 151: _maybe_join with dot notation
        from axiom.oltp.beanie.base.repository.async_ import AsyncBeanieRepository
        from tests.fixtures.models import PostDocument

        post_repo = AsyncBeanieRepository(model=PostDocument, db_session=None)
        query = post_repo._query()
        result = post_repo._maybe_join(query, "user.name")
        assert result is not None
