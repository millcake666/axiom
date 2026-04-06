# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for SyncSQLiteRepository (and SyncSQLAlchemyRepository base)."""

import pytest

from axiom.core.exceptions.http import BadRequestError, ValidationError
from axiom.core.filter.expr import FilterGroup, FilterParam, FilterRequest
from axiom.core.filter.type import FilterType, QueryOperator, SortTypeEnum
from axiom.oltp.sqlalchemy.sqlite.repository.sync import SyncSQLiteRepository
from tests.fixtures.models import PostModel, TagModel, UserModel


@pytest.fixture
def repo(sync_session):
    return SyncSQLiteRepository(model=UserModel, db_session=sync_session)


@pytest.fixture
def post_repo(sync_session):
    return SyncSQLiteRepository(model=PostModel, db_session=sync_session)


class TestSyncRepository:
    def test_create(self, repo):
        user = repo.create({"name": "Alice", "email": "alice@test.com", "age": 30})
        repo.session.flush()
        assert user.name == "Alice"
        assert user.id is not None

    def test_create_many(self, repo):
        users = repo.create_many(
            [
                {"name": "Bob", "email": "bob@test.com", "age": 25},
                {"name": "Charlie", "email": "charlie@test.com", "age": 35},
            ],
        )
        repo.session.flush()
        assert len(users) == 2
        assert all(u.id is not None for u in users)

    def test_create_many_empty(self, repo):
        result = repo.create_many([])
        assert result == []

    def test_get_all(self, repo):
        repo.create({"name": "D1", "email": "d1@test.com", "age": 40})
        repo.create({"name": "D2", "email": "d2@test.com", "age": 28})
        repo.session.flush()
        results = repo.get_all(skip=0, limit=10)
        assert len(results) >= 2

    def test_get_all_default_sort(self, repo):
        repo.create({"name": "Sort1", "email": "srt1@test.com", "age": 1})
        repo.session.commit()
        results = repo.get_all()
        assert len(results) >= 1

    def test_get_by_field_equals(self, repo):
        repo.create({"name": "Frank", "email": "frank@test.com", "age": 22})
        repo.session.flush()
        results = repo.get_by(field="name", value="Frank")
        assert isinstance(results, list)
        assert any(u.name == "Frank" for u in results)

    def test_get_by_operator_in(self, repo):
        repo.create_many(
            [
                {"name": "G1", "email": "g1@test.com", "age": 10},
                {"name": "G2", "email": "g2@test.com", "age": 20},
                {"name": "G3", "email": "g3@test.com", "age": 30},
            ],
        )
        repo.session.flush()
        results = repo.get_by(field="name", value=["G1", "G2"], operator=QueryOperator.IN)
        assert len(results) == 2

    def test_get_by_operator_not_in(self, repo):
        repo.create_many(
            [
                {"name": "H1", "email": "h1@test.com", "age": 11},
                {"name": "H2", "email": "h2@test.com", "age": 12},
            ],
        )
        repo.session.flush()
        results = repo.get_by(field="name", value=["H1"], operator=QueryOperator.NOT_IN)
        assert all(u.name != "H1" for u in results)

    def test_get_by_operator_not_equal(self, repo):
        repo.create_many(
            [
                {"name": "I1", "email": "i1@test.com", "age": 13},
                {"name": "I2", "email": "i2@test.com", "age": 14},
            ],
        )
        repo.session.flush()
        results = repo.get_by(field="name", value="I1", operator=QueryOperator.NOT_EQUAL)
        assert all(u.name != "I1" for u in results)

    def test_get_by_operator_greater(self, repo):
        repo.create_many(
            [
                {"name": "J1", "email": "j1@test.com", "age": 5},
                {"name": "J2", "email": "j2@test.com", "age": 50},
            ],
        )
        repo.session.flush()
        results = repo.get_by(field="age", value=10, operator=QueryOperator.GREATER)
        assert all(u.age > 10 for u in results)

    def test_get_by_operator_less(self, repo):
        repo.create_many(
            [
                {"name": "K1", "email": "k1@test.com", "age": 5},
                {"name": "K2", "email": "k2@test.com", "age": 50},
            ],
        )
        repo.session.flush()
        results = repo.get_by(field="age", value=10, operator=QueryOperator.LESS)
        assert all(u.age < 10 for u in results)

    def test_get_by_operator_gte_lte(self, repo):
        repo.create_many(
            [
                {"name": "L1", "email": "l1@test.com", "age": 10},
                {"name": "L2", "email": "l2@test.com", "age": 20},
            ],
        )
        repo.session.flush()
        gte = repo.get_by(field="age", value=10, operator=QueryOperator.EQUALS_OR_GREATER)
        assert all(u.age >= 10 for u in gte)
        lte = repo.get_by(field="age", value=20, operator=QueryOperator.EQUALS_OR_LESS)
        assert all(u.age <= 20 for u in lte)

    def test_get_by_operator_regex(self, repo):
        repo.create({"name": "STARTS_test", "email": "st@test.com", "age": 1})
        repo.session.flush()
        starts = repo.get_by(field="name", value="STARTS", operator=QueryOperator.STARTS_WITH)
        assert any(u.name.startswith("STARTS") for u in starts)
        ends = repo.get_by(field="name", value="test", operator=QueryOperator.ENDS_WITH)
        assert any(u.name.endswith("test") for u in ends)
        contains = repo.get_by(field="name", value="ARTS_t", operator=QueryOperator.CONTAINS)
        assert any("ARTS_t" in u.name for u in contains)

    def test_get_by_operator_not_regex(self, repo):
        repo.create({"name": "PREFIX_only", "email": "pre@test.com", "age": 2})
        repo.create({"name": "other_SUFFIX", "email": "suf@test.com", "age": 3})
        repo.session.flush()
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

    def test_get_by_unique_found(self, repo):
        repo.create({"name": "Unique1", "email": "u1@test.com", "age": 99})
        repo.session.flush()
        result = repo.get_by(field="name", value="Unique1", unique=True)
        assert result is not None
        assert result.name == "Unique1"

    def test_get_by_unique_not_found(self, repo):
        result = repo.get_by(field="name", value="no_such_xyz", unique=True)
        assert result is None

    def test_get_by_filters_and(self, repo):
        repo.create({"name": "M1", "email": "m1@test.com", "age": 25})
        repo.create({"name": "M2", "email": "m2@test.com", "age": 35})
        repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="M1", operator=QueryOperator.EQUALS)
            & FilterParam(field="age", value=25, operator=QueryOperator.EQUALS),
        )
        results = repo.get_by_filters(filter_request=fr)
        assert len(results) == 1
        assert results[0].name == "M1"

    def test_get_by_filters_or(self, repo):
        repo.create({"name": "N1", "email": "n1@test.com", "age": 1})
        repo.create({"name": "N2", "email": "n2@test.com", "age": 2})
        repo.session.flush()
        fr = FilterRequest(
            chain=FilterParam(field="name", value="N1", operator=QueryOperator.EQUALS)
            | FilterParam(field="name", value="N2", operator=QueryOperator.EQUALS),
        )
        results = repo.get_by_filters(filter_request=fr)
        assert len(results) == 2

    def test_get_by_filters_group(self, repo):
        repo.create({"name": "AA1", "email": "aa1@test.com", "age": 100})
        repo.create({"name": "AA2", "email": "aa2@test.com", "age": 200})
        repo.session.flush()
        fr = FilterRequest(
            chain=FilterGroup(
                type=FilterType.AND,
                items=[
                    FilterParam(field="age", value=50, operator=QueryOperator.GREATER),
                    FilterParam(field="age", value=150, operator=QueryOperator.LESS),
                ],
            ),
        )
        results = repo.get_by_filters(filter_request=fr)
        assert all(50 < u.age < 150 for u in results)

    def test_get_by_filters_none(self, repo):
        repo.create({"name": "R1", "email": "r1@test.com", "age": 200})
        repo.session.flush()
        results = repo.get_by_filters(filter_request=None)
        assert isinstance(results, list)
        assert any(u.name == "R1" for u in results)

    def test_get_by_filters_unique_found(self, repo):
        repo.create({"name": "SU1", "email": "su1@test.com", "age": 201})
        repo.session.flush()
        result = repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="SU1", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result is not None
        assert result.name == "SU1"

    def test_get_by_filters_unique_not_found(self, repo):
        result = repo.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="no_such", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result is None

    def test_update(self, repo):
        user = repo.create({"name": "O1", "email": "o1@test.com", "age": 20})
        repo.session.flush()
        updated = repo.update(user, {"age": 99})
        assert updated.age == 99
        assert updated.name == "O1"

    def test_update_wrong_type(self, repo):
        user = repo.create({"name": "WT1", "email": "wt1@test.com", "age": 20})
        repo.session.flush()
        with pytest.raises(ValidationError):
            repo.update(user, {"name": 123})

    def test_update_by(self, repo):
        repo.create({"name": "P1", "email": "p1@test.com", "age": 21})
        repo.session.flush()
        result = repo.update_by(field="name", value="P1", attributes={"age": 88})
        assert isinstance(result, list)
        assert result[0].age == 88

    def test_update_by_unique(self, repo):
        repo.create({"name": "PU1", "email": "pu1@test.com", "age": 32})
        repo.session.flush()
        result = repo.update_by(field="name", value="PU1", attributes={"age": 77}, unique=True)
        assert result is not None
        assert result.age == 77

    def test_update_by_unique_not_found(self, repo):
        result = repo.update_by(field="name", value="no_such", attributes={"age": 1}, unique=True)
        assert result is None

    def test_update_by_filters(self, repo):
        repo.create({"name": "Q1filter", "email": "q1f@test.com", "age": 22})
        repo.session.flush()
        result = repo.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="Q1filter", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 77},
        )
        assert isinstance(result, list)
        assert result[0].age == 77

    def test_update_by_filters_unique(self, repo):
        repo.create({"name": "Q2filter", "email": "q2f@test.com", "age": 302})
        repo.session.flush()
        result = repo.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="Q2filter", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 303},
            unique=True,
        )
        assert result is not None
        assert result.age == 303

    def test_update_by_filters_unique_not_found(self, repo):
        result = repo.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="no_such", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 1},
            unique=True,
        )
        assert result is None

    def test_delete(self, repo):
        user = repo.create({"name": "R1", "email": "r1@test.com", "age": 22})
        repo.session.flush()
        deleted = repo.delete(user)
        assert deleted.name == "R1"

    def test_delete_by(self, repo):
        repo.create({"name": "S1", "email": "s1@test.com", "age": 23})
        repo.session.flush()
        result = repo.delete_by(field="name", value="S1")
        assert isinstance(result, list)
        assert result[0].name == "S1"

    def test_delete_by_unique(self, repo):
        repo.create({"name": "SU1del", "email": "sud@test.com", "age": 33})
        repo.session.flush()
        result = repo.delete_by(field="name", value="SU1del", unique=True)
        assert result is not None
        assert result.name == "SU1del"

    def test_delete_by_unique_not_found(self, repo):
        result = repo.delete_by(field="name", value="no_such_xyz", unique=True)
        assert result is None

    def test_delete_by_filters(self, repo):
        repo.create({"name": "T1filter", "email": "t1f@test.com", "age": 24})
        repo.session.flush()
        result = repo.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="T1filter", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(result, list)
        assert result[0].name == "T1filter"

    def test_delete_by_filters_unique(self, repo):
        repo.create({"name": "T2filter", "email": "t2f@test.com", "age": 311})
        repo.session.flush()
        result = repo.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="T2filter", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result is not None
        assert result.name == "T2filter"

    def test_delete_by_filters_unique_not_found(self, repo):
        result = repo.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(
                    field="name",
                    value="no_such_xyz2",
                    operator=QueryOperator.EQUALS,
                ),
            ),
            unique=True,
        )
        assert result is None

    def test_count(self, repo):
        repo.create({"name": "U1", "email": "u1@test.com", "age": 25})
        repo.create({"name": "U2", "email": "u2@test.com", "age": 26})
        repo.session.flush()
        total = repo.count()
        assert total >= 2

    def test_count_with_filter(self, repo):
        repo.create({"name": "V1unique", "email": "v1@test.com", "age": 27})
        repo.session.flush()
        cnt = repo.count(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="V1unique", operator=QueryOperator.EQUALS),
            ),
        )
        assert cnt == 1

    def test_sort_asc(self, repo):
        repo.create_many(
            [
                {"name": "W1", "email": "w1@test.com", "age": 30},
                {"name": "W2", "email": "w2@test.com", "age": 10},
                {"name": "W3", "email": "w3@test.com", "age": 20},
            ],
        )
        repo.session.flush()
        results = repo.get_all(sort_by="age", sort_type=SortTypeEnum.asc)
        ages = [u.age for u in results]
        assert ages == sorted(ages)

    def test_sort_desc(self, repo):
        repo.create_many(
            [
                {"name": "X1", "email": "x1@test.com", "age": 10},
                {"name": "X2", "email": "x2@test.com", "age": 30},
            ],
        )
        repo.session.flush()
        results = repo.get_all(sort_by="age", sort_type=SortTypeEnum.desc)
        ages = [u.age for u in results]
        assert ages == sorted(ages, reverse=True)

    def test_paginate(self, repo):
        repo.create_many([{"name": f"Y{i}", "email": f"y{i}@test.com", "age": i} for i in range(5)])
        repo.session.flush()
        page1 = repo.get_all(skip=0, limit=2, sort_by="age", sort_type=SortTypeEnum.asc)
        page2 = repo.get_all(skip=2, limit=2, sort_by="age", sort_type=SortTypeEnum.asc)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].age != page2[0].age

    def test_create_or_update_by_create(self, repo):
        user = repo.create_or_update_by(
            attributes={"name": "Z1upsert", "email": "z1@test.com", "age": 28},
        )
        repo.session.flush()
        assert user is not None
        assert user.name == "Z1upsert"

    def test_create_or_update_by_update(self, repo):
        repo.create_or_update_by(attributes={"name": "Z2upsert", "email": "z2@test.com", "age": 29})
        repo.session.commit()
        updated = repo.create_or_update_by(
            attributes={"name": "Z2 Updated", "email": "z2@test.com", "age": 99},
            update_fields=["name", "age"],
        )
        assert updated is not None
        assert updated.age == 99

    def test_get_by_bad_field_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="nonexistent_field", value="x")

    def test_get_by_in_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="name", value="not_a_list", operator=QueryOperator.IN)

    def test_get_by_not_in_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="name", value="not_a_list", operator=QueryOperator.NOT_IN)

    def test_get_by_starts_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="age", value=123, operator=QueryOperator.STARTS_WITH)

    def test_get_by_not_starts_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="age", value=123, operator=QueryOperator.NOT_START_WITH)

    def test_get_by_ends_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="age", value=123, operator=QueryOperator.ENDS_WITH)

    def test_get_by_not_ends_with_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="age", value=123, operator=QueryOperator.NOT_END_WITH)

    def test_get_by_contains_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="age", value=123, operator=QueryOperator.CONTAINS)

    def test_get_by_not_contains_bad_type_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_by(field="age", value=123, operator=QueryOperator.NOT_CONTAIN)

    def test_sort_bad_field_raises(self, repo):
        with pytest.raises(BadRequestError):
            repo.get_all(sort_by="nonexistent_field")

    def test_get_deep_unique_from_dict_with_scalar_list(self, repo):
        result = repo._get_deep_unique_from_dict([1, 2, 2, 3])
        assert result == [1, 2, 3]

    def test_get_deep_unique_from_dict_with_dict(self, repo):
        result = repo._get_deep_unique_from_dict({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_get_deep_unique_from_dict_with_list_of_dicts(self, repo):
        data = [{"key": "val1"}, {"key": "val1"}, {"key": "val2"}]
        result = repo._get_deep_unique_from_dict(data)
        assert isinstance(result, dict)
        assert "key" in result
        assert "val1" in result["key"]
        assert "val2" in result["key"]
        assert result["key"].count("val1") == 1

    def test_get_deep_unique_from_dict_with_scalar(self, repo):
        assert repo._get_deep_unique_from_dict(42) == 42
        assert repo._get_deep_unique_from_dict("hello") == "hello"

    def test_get_conflict_fields(self, repo):
        assert "email" in repo._get_conflict_fields()

    def test_get_model_field_type(self, repo):
        field_type = repo._get_model_field_type(UserModel, "name")
        assert field_type is str

    def test_validate_params_valid(self, repo):
        user = repo.create({"name": "VP1", "email": "vp1sync@test.com", "age": 40})
        repo.session.flush()
        repo.update(user, {"name": "VP1 Updated"})
        assert user.name == "VP1 Updated"

    def test_validate_params_wrong_relation_raises(self, repo):
        user = repo.create({"name": "VR1", "email": "vr1sync@test.com", "age": 41})
        repo.session.flush()
        with pytest.raises(ValidationError):
            repo.update(user, {"nonexistent": "value"})

    def test_resolve_field_relation_dot_notation(self, post_repo):
        model, col = post_repo._resolve_field_relation("user.name")
        assert col == "name"

    def test_resolve_field_relation_bad_raises(self, repo):
        with pytest.raises(ValidationError):
            repo._resolve_field_relation("bad_relation.name")

    def test_maybe_join_no_dot(self, repo):
        query = repo._query()
        result = repo._maybe_join(query, "name")
        assert result is not None

    def test_maybe_join_with_dot(self, post_repo):
        query = post_repo._query()
        result = post_repo._maybe_join(query, "user.name")
        assert result is not None

    def test_get_by_dot_notation(self, sync_session):
        user_repo = SyncSQLiteRepository(model=UserModel, db_session=sync_session)
        p_repo = SyncSQLiteRepository(model=PostModel, db_session=sync_session)

        user = user_repo.create({"name": "DotSync", "email": "dots@test.com", "age": 50})
        sync_session.flush()
        p_repo.create({"title": "SyncPost", "user_id": user.id})
        sync_session.flush()

        results = p_repo.get_by(field="user.name", value="DotSync")
        assert isinstance(results, list)
        assert any(p.title == "SyncPost" for p in results)

    def test_paginate_no_limit(self, repo):
        for i in range(3):
            repo.create({"name": f"NL{i}", "email": f"nl{i}@test.com", "age": i})
        repo.session.flush()
        results = repo.get_all(limit=-1)
        assert len(results) >= 3

    def test_create_or_update_by_no_conflict_cols(self, sync_session):
        # TagModel has no unique constraints — exercises the fallback create path
        tag_repo = SyncSQLiteRepository(model=TagModel, db_session=sync_session)
        tag = tag_repo.create_or_update_by(attributes={"label": "python"})
        sync_session.flush()
        assert tag is not None
        assert tag.label == "python"

    def test_create_or_update_creates_new(self, repo):
        model = UserModel(name="SYNC_COU_New", email="sync_cou_new@test.com", age=11)
        result = repo.create_or_update(model)
        repo.session.flush()
        assert result is not None
        assert result.name == "SYNC_COU_New"

    def test_create_or_update_updates_existing(self, repo):
        repo.create_or_update_by(
            attributes={"name": "SYNC_COU_E", "email": "sync_cou_e@test.com", "age": 22},
        )
        repo.session.commit()
        model = UserModel(name="SYNC_COU_E_upd", email="sync_cou_e@test.com", age=99)
        result = repo.create_or_update(model)
        repo.session.flush()
        assert result is not None
        assert result.age == 99

    def test_create_or_update_many_empty(self, repo):
        result = repo.create_or_update_many([])
        assert result == []

    def test_create_or_update_many_all_new(self, repo):
        models = [
            UserModel(name="SYNC_COUM_N1", email="sync_coum_n1@test.com", age=1),
            UserModel(name="SYNC_COUM_N2", email="sync_coum_n2@test.com", age=2),
        ]
        results = repo.create_or_update_many(models)
        repo.session.flush()
        assert len(results) == 2
        assert all(r.id is not None for r in results)

    def test_create_or_update_many_all_existing(self, repo):
        repo.create_or_update_by(
            attributes={"name": "SYNC_COUM_E1", "email": "sync_coum_e1@test.com", "age": 10},
        )
        repo.create_or_update_by(
            attributes={"name": "SYNC_COUM_E2", "email": "sync_coum_e2@test.com", "age": 20},
        )
        repo.session.commit()
        models = [
            UserModel(name="SYNC_COUM_E1_upd", email="sync_coum_e1@test.com", age=11),
            UserModel(name="SYNC_COUM_E2_upd", email="sync_coum_e2@test.com", age=21),
        ]
        results = repo.create_or_update_many(models)
        repo.session.flush()
        assert len(results) == 2
        ages = {r.age for r in results}
        assert ages == {11, 21}

    def test_create_or_update_many_mixed(self, repo):
        repo.create_or_update_by(
            attributes={
                "name": "SYNC_COUM_M_exist",
                "email": "sync_coum_m_exist@test.com",
                "age": 50,
            },
        )
        repo.session.commit()
        models = [
            UserModel(name="SYNC_COUM_M_exist_upd", email="sync_coum_m_exist@test.com", age=51),
            UserModel(name="SYNC_COUM_M_new", email="sync_coum_m_new@test.com", age=52),
        ]
        results = repo.create_or_update_many(models)
        repo.session.flush()
        assert len(results) == 2

    def test_update_many_empty(self, repo):
        result = repo.update_many([])
        assert result == []

    def test_update_many_single(self, repo):
        user = repo.create({"name": "SYNC_UM_S1", "email": "sync_um_s1@test.com", "age": 10})
        repo.session.flush()
        user.age = 99
        results = repo.update_many([user])
        repo.session.flush()
        assert len(results) == 1
        assert results[0].age == 99

    def test_update_many_multiple(self, repo):
        user1 = repo.create({"name": "SYNC_UM_M1", "email": "sync_um_m1@test.com", "age": 10})
        user2 = repo.create({"name": "SYNC_UM_M2", "email": "sync_um_m2@test.com", "age": 20})
        repo.session.flush()
        user1.age = 88
        user2.age = 77
        results = repo.update_many([user1, user2])
        repo.session.flush()
        assert len(results) == 2
        ages = {r.age for r in results}
        assert ages == {88, 77}

    def test_delete_many_empty(self, repo):
        result = repo.delete_many([])
        assert result == []

    def test_delete_many_single(self, repo):
        user = repo.create({"name": "SYNC_DM_S1", "email": "sync_dm_s1@test.com", "age": 10})
        repo.session.flush()
        results = repo.delete_many([user])
        assert len(results) == 1
        assert results[0].name == "SYNC_DM_S1"
        found = repo.get_by(field="email", value="sync_dm_s1@test.com", unique=True)
        assert found is None

    def test_delete_many_multiple(self, repo):
        user1 = repo.create({"name": "SYNC_DM_M1", "email": "sync_dm_m1@test.com", "age": 10})
        user2 = repo.create({"name": "SYNC_DM_M2", "email": "sync_dm_m2@test.com", "age": 20})
        repo.session.flush()
        results = repo.delete_many([user1, user2])
        assert len(results) == 2
        found1 = repo.get_by(field="email", value="sync_dm_m1@test.com", unique=True)
        found2 = repo.get_by(field="email", value="sync_dm_m2@test.com", unique=True)
        assert found1 is None
        assert found2 is None
