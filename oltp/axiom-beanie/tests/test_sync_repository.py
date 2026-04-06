# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for SyncMongoRepository."""

import pytest

from axiom.core.filter.expr import FilterGroup, FilterParam, FilterRequest
from axiom.core.filter.type import FilterType, QueryOperator, SortTypeEnum
from axiom.oltp.beanie.base.repository.sync import SyncMongoRepository
from tests.fixtures.sync_models import SyncUserModel


@pytest.fixture
def repo(sync_db):
    return SyncMongoRepository(
        model=SyncUserModel,
        collection=sync_db[SyncUserModel.Settings.name],
    )


class TestSyncRepository:
    def test_create(self, repo):
        user = repo.create({"name": "Alice", "email": "alice@example.com", "age": 30})
        assert user.name == "Alice"
        assert user.id is not None

    def test_create_many(self, repo):
        users = repo.create_many(
            [
                {"name": "Bob", "email": "bob@example.com", "age": 25},
                {"name": "Charlie", "email": "charlie@example.com", "age": 35},
            ],
        )
        assert len(users) == 2
        assert all(u.id is not None for u in users)

    def test_create_many_empty(self, repo):
        result = repo.create_many([])
        assert result == []

    def test_get_all(self, repo):
        repo.create({"name": "Dave", "email": "dave@example.com", "age": 40})
        repo.create({"name": "Eve", "email": "eve@example.com", "age": 28})
        results = repo.get_all(skip=0, limit=10)
        assert len(results) >= 2

    def test_get_by_field(self, repo):
        repo.create({"name": "Frank", "email": "frank@example.com", "age": 22})
        results = repo.get_by(field="name", value="Frank")
        assert isinstance(results, list)
        assert any(u.name == "Frank" for u in results)

    def test_get_by_operator_in(self, repo):
        repo.create_many(
            [
                {"name": "G1", "email": "g1@example.com", "age": 10},
                {"name": "G2", "email": "g2@example.com", "age": 20},
                {"name": "G3", "email": "g3@example.com", "age": 30},
            ],
        )
        results = repo.get_by(field="name", value=["G1", "G2"], operator=QueryOperator.IN)
        assert len(results) == 2

    def test_get_by_operator_not_in(self, repo):
        repo.create_many(
            [
                {"name": "H1", "email": "h1@example.com", "age": 11},
                {"name": "H2", "email": "h2@example.com", "age": 12},
            ],
        )
        results = repo.get_by(field="name", value=["H1"], operator=QueryOperator.NOT_IN)
        assert all(u.name != "H1" for u in results)

    def test_get_by_operator_not_equal(self, repo):
        repo.create_many(
            [
                {"name": "I1", "email": "i1@example.com", "age": 13},
                {"name": "I2", "email": "i2@example.com", "age": 14},
            ],
        )
        results = repo.get_by(field="name", value="I1", operator=QueryOperator.NOT_EQUAL)
        assert all(u.name != "I1" for u in results)

    def test_get_by_operator_greater(self, repo):
        repo.create_many(
            [
                {"name": "J1", "email": "j1@example.com", "age": 5},
                {"name": "J2", "email": "j2@example.com", "age": 50},
            ],
        )
        results = repo.get_by(field="age", value=10, operator=QueryOperator.GREATER)
        assert all(u.age > 10 for u in results)

    def test_get_by_operator_less(self, repo):
        repo.create_many(
            [
                {"name": "K1", "email": "k1@example.com", "age": 5},
                {"name": "K2", "email": "k2@example.com", "age": 50},
            ],
        )
        results = repo.get_by(field="age", value=10, operator=QueryOperator.LESS)
        assert all(u.age < 10 for u in results)

    def test_get_by_operator_gte_lte(self, repo):
        repo.create_many(
            [
                {"name": "L1", "email": "l1@example.com", "age": 10},
                {"name": "L2", "email": "l2@example.com", "age": 20},
            ],
        )
        gte = repo.get_by(field="age", value=10, operator=QueryOperator.EQUALS_OR_GREATER)
        assert all(u.age >= 10 for u in gte)
        lte = repo.get_by(field="age", value=20, operator=QueryOperator.EQUALS_OR_LESS)
        assert all(u.age <= 20 for u in lte)

    def test_get_by_operator_regex(self, repo):
        repo.create({"name": "STARTS_test", "email": "s@example.com", "age": 1})
        starts = repo.get_by(field="name", value="STARTS", operator=QueryOperator.STARTS_WITH)
        assert any(u.name.startswith("STARTS") for u in starts)
        ends = repo.get_by(field="name", value="test", operator=QueryOperator.ENDS_WITH)
        assert any(u.name.endswith("test") for u in ends)
        contains = repo.get_by(field="name", value="ARTS_t", operator=QueryOperator.CONTAINS)
        assert any("ARTS_t" in u.name for u in contains)

    def test_get_by_operator_not_regex(self, repo):
        repo.create({"name": "PREFIX_only", "email": "p@example.com", "age": 2})
        repo.create({"name": "other_SUFFIX", "email": "o@example.com", "age": 3})
        not_starts = repo.get_by(
            field="name",
            value="PREFIX",
            operator=QueryOperator.NOT_START_WITH,
        )
        assert all(not u.name.startswith("PREFIX") for u in not_starts)
        not_ends = repo.get_by(field="name", value="SUFFIX", operator=QueryOperator.NOT_END_WITH)
        assert all(not u.name.endswith("SUFFIX") for u in not_ends)
        not_contains = repo.get_by(
            field="name",
            value="PREFIX_only",
            operator=QueryOperator.NOT_CONTAIN,
        )
        assert all("PREFIX_only" not in u.name for u in not_contains)

    def test_get_by_filters_and(self, repo):
        repo.create({"name": "M1", "email": "m1@example.com", "age": 25})
        repo.create({"name": "M2", "email": "m2@example.com", "age": 35})
        results = repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="M1", operator=QueryOperator.EQUALS)
                & FilterParam(field="age", value=25, operator=QueryOperator.EQUALS),
            ),
        )
        assert len(results) == 1
        assert results[0].name == "M1"

    def test_get_by_filters_or(self, repo):
        repo.create({"name": "N1", "email": "n1@example.com", "age": 1})
        repo.create({"name": "N2", "email": "n2@example.com", "age": 2})
        results = repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="N1", operator=QueryOperator.EQUALS)
                | FilterParam(field="name", value="N2", operator=QueryOperator.EQUALS),
            ),
        )
        assert len(results) == 2

    def test_get_by_filters_group(self, repo):
        repo.create({"name": "AA1", "email": "aa1@example.com", "age": 100})
        repo.create({"name": "AA2", "email": "aa2@example.com", "age": 200})
        results = repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterGroup(
                    type=FilterType.AND,
                    items=[
                        FilterParam(field="age", value=50, operator=QueryOperator.GREATER),
                        FilterParam(field="age", value=150, operator=QueryOperator.LESS),
                    ],
                ),
            ),
        )
        assert all(50 < u.age < 150 for u in results)

    def test_update(self, repo):
        user = repo.create({"name": "O1", "email": "o1@example.com", "age": 20})
        updated = repo.update(user, {"age": 99})
        assert updated.age == 99
        assert updated.name == "O1"

    def test_update_by(self, repo):
        repo.create({"name": "P1", "email": "p1@example.com", "age": 21})
        result = repo.update_by(field="name", value="P1", attributes={"age": 88})
        assert isinstance(result, list)
        assert result[0].age == 88

    def test_update_by_filters(self, repo):
        repo.create({"name": "Q1filter", "email": "q1@example.com", "age": 22})
        result = repo.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="Q1filter", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 77},
        )
        assert isinstance(result, list)
        assert result[0].age == 77

    def test_delete(self, repo):
        user = repo.create({"name": "R1", "email": "r1@example.com", "age": 22})
        deleted = repo.delete(user)
        assert deleted.name == "R1"
        remaining = repo.get_by(field="name", value="R1")
        assert remaining == []

    def test_delete_by(self, repo):
        repo.create({"name": "S1", "email": "s1@example.com", "age": 23})
        result = repo.delete_by(field="name", value="S1")
        assert isinstance(result, list)
        assert result[0].name == "S1"

    def test_delete_by_filters(self, repo):
        repo.create({"name": "T1filter", "email": "t1@example.com", "age": 24})
        result = repo.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="T1filter", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(result, list)
        assert result[0].name == "T1filter"

    def test_count(self, repo):
        repo.create({"name": "U1", "email": "u1@example.com", "age": 25})
        repo.create({"name": "U2", "email": "u2@example.com", "age": 26})
        total = repo.count()
        assert total >= 2

    def test_count_with_filter(self, repo):
        repo.create({"name": "V1unique", "email": "v1@example.com", "age": 27})
        cnt = repo.count(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="V1unique", operator=QueryOperator.EQUALS),
            ),
        )
        assert cnt == 1

    def test_sort_asc(self, repo):
        repo.create_many(
            [
                {"name": "W1", "email": "w1@example.com", "age": 30},
                {"name": "W2", "email": "w2@example.com", "age": 10},
            ],
        )
        results = repo.get_all(sort_by="age", sort_type=SortTypeEnum.asc)
        ages = [u.age for u in results]
        assert ages == sorted(ages)

    def test_sort_desc(self, repo):
        repo.create_many(
            [
                {"name": "X1", "email": "x1@example.com", "age": 10},
                {"name": "X2", "email": "x2@example.com", "age": 30},
            ],
        )
        results = repo.get_all(sort_by="age", sort_type=SortTypeEnum.desc)
        ages = [u.age for u in results]
        assert ages == sorted(ages, reverse=True)

    def test_paginate(self, repo):
        repo.create_many(
            [{"name": f"Y{i}", "email": f"y{i}@example.com", "age": i} for i in range(5)],
        )
        page1 = repo.get_all(skip=0, limit=2)
        page2 = repo.get_all(skip=2, limit=2)
        assert len(page1) == 2
        assert len(page2) == 2

    def test_create_or_update_by_create(self, repo):
        user = repo.create_or_update_by(
            attributes={"name": "Z1upsert", "email": "z1@example.com", "age": 28},
        )
        assert user.name == "Z1upsert"
        assert user.id is not None

    def test_create_or_update_by_update(self, repo):
        repo.create_or_update_by(
            attributes={"name": "Z2upsert", "email": "z2@example.com", "age": 29},
        )
        updated = repo.create_or_update_by(
            attributes={"name": "Z2upsert", "email": "z2@example.com", "age": 99},
            update_fields=["age"],
        )
        assert updated.age == 99

    def test_get_by_unique_found(self, repo):
        repo.create({"name": "AB1unique", "email": "ab1@example.com", "age": 31})
        result = repo.get_by(field="name", value="AB1unique", unique=True)
        assert result is not None
        assert result.name == "AB1unique"

    def test_get_by_unique_not_found(self, repo):
        result = repo.get_by(field="name", value="no_such_name_xyz", unique=True)
        assert result is None

    def test_update_by_unique(self, repo):
        repo.create({"name": "AC1upd", "email": "ac1@example.com", "age": 32})
        result = repo.update_by(field="name", value="AC1upd", attributes={"age": 77}, unique=True)
        assert result is not None
        assert result.age == 77

    def test_update_by_unique_not_found(self, repo):
        result = repo.update_by(
            field="name",
            value="no_such_xyz",
            attributes={"age": 1},
            unique=True,
        )
        assert result is None

    def test_delete_by_unique(self, repo):
        repo.create({"name": "AD1del", "email": "ad1@example.com", "age": 33})
        result = repo.delete_by(field="name", value="AD1del", unique=True)
        assert result is not None
        assert result.name == "AD1del"

    def test_delete_by_unique_not_found(self, repo):
        result = repo.delete_by(field="name", value="no_such_xyz", unique=True)
        assert result is None

    def test_create_or_update_creates_new(self, repo):
        from tests.fixtures.sync_models import SyncUserModel

        model = SyncUserModel(name="COU_New", email="cou_new@test.com", age=11)
        result = repo.create_or_update(model)
        assert result is not None
        assert result.name == "COU_New"
        assert result.id is not None

    def test_create_or_update_updates_existing(self, repo):
        from tests.fixtures.sync_models import SyncUserModel

        user = repo.create({"name": "COU_Exist", "email": "cou_exist@test.com", "age": 22})
        model = SyncUserModel(
            id=user.id,
            name="COU_Exist_Updated",
            email="cou_exist@test.com",
            age=99,
        )
        result = repo.create_or_update(model)
        assert result is not None
        assert result.age == 99

    def test_create_or_update_many_empty(self, repo):
        result = repo.create_or_update_many([])
        assert result == []

    def test_create_or_update_many_all_new(self, repo):
        from tests.fixtures.sync_models import SyncUserModel

        models = [
            SyncUserModel(name="COUM_N1", email="coum_n1@test.com", age=1),
            SyncUserModel(name="COUM_N2", email="coum_n2@test.com", age=2),
        ]
        results = repo.create_or_update_many(models)
        assert len(results) == 2
        assert all(r.id is not None for r in results)

    def test_create_or_update_many_all_existing(self, repo):
        from tests.fixtures.sync_models import SyncUserModel

        u1 = repo.create({"name": "COUM_E1", "email": "coum_e1@test.com", "age": 10})
        u2 = repo.create({"name": "COUM_E2", "email": "coum_e2@test.com", "age": 20})
        models = [
            SyncUserModel(id=u1.id, name="COUM_E1_upd", email="coum_e1@test.com", age=11),
            SyncUserModel(id=u2.id, name="COUM_E2_upd", email="coum_e2@test.com", age=21),
        ]
        results = repo.create_or_update_many(models)
        assert len(results) == 2
        ages = {r.age for r in results}
        assert ages == {11, 21}

    def test_create_or_update_many_mixed(self, repo):
        from tests.fixtures.sync_models import SyncUserModel

        existing = repo.create(
            {"name": "COUM_M_exist", "email": "coum_m_exist@test.com", "age": 50},
        )
        models = [
            SyncUserModel(
                id=existing.id,
                name="COUM_M_exist_upd",
                email="coum_m_exist@test.com",
                age=51,
            ),
            SyncUserModel(name="COUM_M_new", email="coum_m_new@test.com", age=52),
        ]
        results = repo.create_or_update_many(models)
        assert len(results) == 2

    def test_update_many_empty(self, repo):
        result = repo.update_many([])
        assert result == []

    def test_update_many_single(self, repo):
        user = repo.create({"name": "UM_S1", "email": "um_s1@test.com", "age": 10})
        user.age = 99
        results = repo.update_many([user])
        assert len(results) == 1
        assert results[0].age == 99

    def test_update_many_multiple(self, repo):
        user1 = repo.create({"name": "UM_M1", "email": "um_m1@test.com", "age": 10})
        user2 = repo.create({"name": "UM_M2", "email": "um_m2@test.com", "age": 20})
        user1.age = 88
        user2.age = 77
        results = repo.update_many([user1, user2])
        assert len(results) == 2
        ages = {r.age for r in results}
        assert ages == {88, 77}

    def test_delete_many_empty(self, repo):
        result = repo.delete_many([])
        assert result == []

    def test_delete_many_single(self, repo):
        user = repo.create({"name": "DM_S1", "email": "dm_s1@test.com", "age": 10})
        results = repo.delete_many([user])
        assert len(results) == 1
        assert results[0].name == "DM_S1"
        found = repo.get_by(field="email", value="dm_s1@test.com", unique=True)
        assert found is None

    def test_delete_many_multiple(self, repo):
        user1 = repo.create({"name": "DM_M1", "email": "dm_m1@test.com", "age": 10})
        user2 = repo.create({"name": "DM_M2", "email": "dm_m2@test.com", "age": 20})
        results = repo.delete_many([user1, user2])
        assert len(results) == 2
        found1 = repo.get_by(field="email", value="dm_m1@test.com", unique=True)
        found2 = repo.get_by(field="email", value="dm_m2@test.com", unique=True)
        assert found1 is None
        assert found2 is None
