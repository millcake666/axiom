# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for AsyncSQLAlchemyController with AsyncSQLiteRepository."""

import pytest
from pydantic import BaseModel

from axiom.core.exceptions.http import NotFoundError, UnprocessableError
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator
from axiom.core.schema.response import CountResponse, PaginationResponse
from axiom.oltp.sqlalchemy.sqlite.controller.async_ import AsyncSQLiteController
from axiom.oltp.sqlalchemy.sqlite.repository.async_ import AsyncSQLiteRepository
from tests.fixtures.models import UserModel


class UserSchema(BaseModel):
    name: str
    email: str
    age: int


@pytest.fixture
def repo(async_session):
    return AsyncSQLiteRepository(model=UserModel, db_session=async_session)


@pytest.fixture
def controller(repo):
    return AsyncSQLiteController(
        model=UserModel,
        repository=repo,
        exclude_fields=["email"],
    )


class TestAsyncController:
    async def test_create_and_get_by_id(self, controller):
        user = await controller.create({"name": "Alice", "email": "a@x.com", "age": 20})
        assert user.id is not None
        found = await controller.get_by_id(user.id)
        assert found.name == "Alice"

    async def test_get_all_pagination_response(self, controller):
        await controller.create({"name": "B1", "email": "b1@x.com", "age": 21})
        await controller.create({"name": "B2", "email": "b2@x.com", "age": 22})
        response = await controller.get_all(skip=0, limit=10)
        assert isinstance(response, PaginationResponse)
        assert response.total_count >= 2
        assert isinstance(response.data, list)
        assert response.page == 1

    async def test_update_by_id(self, controller):
        user = await controller.create({"name": "C1", "email": "c1@x.com", "age": 30})
        user_id = user.id
        await controller.update_by_id(user_id, {"name": "C1_updated", "age": 31})
        # expire identity map so get_by_id fetches fresh data from DB
        controller.repository.session.expire_all()
        found = await controller.get_by_id(user_id)
        assert found.name == "C1_updated"

    async def test_delete_by_id(self, controller):
        user = await controller.create({"name": "D1", "email": "d1@x.com", "age": 40})
        deleted = await controller.delete_by_id(user.id)
        assert deleted.name == "D1"
        with pytest.raises(NotFoundError):
            await controller.get_by_id(user.id)

    async def test_get_by_id_not_found(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by_id(999999)

    async def test_get_by_filters(self, controller):
        await controller.create({"name": "E1", "email": "e1@x.com", "age": 50})
        await controller.create({"name": "E2", "email": "e2@x.com", "age": 51})
        response = await controller.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="E1", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(response, PaginationResponse)
        assert response.total_count == 1

    async def test_get_by_filters_no_filter(self, controller):
        await controller.create({"name": "E3", "email": "e3@x.com", "age": 52})
        response = await controller.get_by_filters()
        assert isinstance(response, PaginationResponse)
        assert response.total_count >= 1

    async def test_count(self, controller):
        await controller.create({"name": "F1", "email": "f1@x.com", "age": 60})
        response = await controller.count()
        assert isinstance(response, CountResponse)
        assert response.count >= 1

    async def test_update_allowed_field(self, controller):
        user = await controller.create({"name": "G0", "email": "g0@x.com", "age": 69})
        updated = await controller.update(user, {"age": 100})
        assert updated.age == 100

    async def test_update_excluded_field_raises(self, controller):
        user = await controller.create({"name": "G1", "email": "g1@x.com", "age": 70})
        with pytest.raises(UnprocessableError):
            await controller.update(user, {"email": "new@x.com"})

    async def test_extract_attributes_from_schema(self, controller):
        schema = UserSchema(name="H1", email="h1@x.com", age=80)
        attrs = await controller.extract_attributes_from_schema(schema)
        assert attrs == {"name": "H1", "email": "h1@x.com", "age": 80}

    async def test_repr(self, controller):
        assert "AsyncSQLiteController" in repr(controller)

    async def test_get_by_returns_pagination(self, controller):
        await controller.create({"name": "I1", "email": "i1@x.com", "age": 11})
        await controller.create({"name": "I2", "email": "i2@x.com", "age": 12})
        response = await controller.get_by(field="name", value="I1")
        assert isinstance(response, PaginationResponse)
        assert response.total_count == 1

    async def test_get_by_unique_returns_model(self, controller):
        await controller.create({"name": "J1", "email": "j1@x.com", "age": 13})
        result = await controller.get_by(field="name", value="J1", unique=True)
        assert result.name == "J1"

    async def test_get_by_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by(field="name", value="nonexistent_xyz", unique=True)

    async def test_get_by_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by(field="name", value="no_such_name_abc")

    async def test_get_by_filters_unique_found(self, controller):
        await controller.create({"name": "K1unique", "email": "k1@x.com", "age": 14})
        result = await controller.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="K1unique", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result.name == "K1unique"

    async def test_get_by_filters_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )

    async def test_create_or_update_by(self, repo):
        ctrl = AsyncSQLiteController(model=UserModel, repository=repo, exclude_fields=[])
        user = await ctrl.create_or_update_by(
            attributes={"name": "L1ctrl", "email": "l1ctrl@x.com", "age": 15},
        )
        assert user.name == "L1ctrl"
        await ctrl.create_or_update_by(
            attributes={"name": "L1ctrl Updated", "email": "l1ctrl@x.com", "age": 99},
            update_fields=["name", "age"],
        )
        # expire identity map so get_by fetches fresh data from DB
        repo.session.expire_all()
        found = await repo.get_by(field="email", value="l1ctrl@x.com", unique=True)
        assert found.age == 99

    async def test_create_or_update_by_excluded_field_raises(self, controller):
        with pytest.raises(UnprocessableError):
            await controller.create_or_update_by(
                attributes={"name": "L2", "email": "excluded@x.com", "age": 16},
            )

    async def test_update_by_filters(self, controller):
        await controller.create({"name": "M1filter", "email": "m1@x.com", "age": 17})
        result = await controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="M1filter", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 99},
        )
        assert isinstance(result, list)
        assert result[0].age == 99

    async def test_update_by_filters_excluded_field_raises(self, controller):
        with pytest.raises(UnprocessableError):
            await controller.update_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(field="name", value="any", operator=QueryOperator.EQUALS),
                ),
                attributes={"email": "bad@x.com"},
            )

    async def test_update_by_filters_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.update_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                attributes={"age": 1},
                unique=True,
            )

    async def test_delete_by_filters(self, controller):
        await controller.create({"name": "N1filter", "email": "n1@x.com", "age": 18})
        result = await controller.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="N1filter", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].name == "N1filter"

    async def test_delete_by_filters_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.delete_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )

    async def test_update_by(self, controller):
        await controller.create({"name": "O1upd", "email": "o1@x.com", "age": 19})
        result = await controller.update_by(field="name", value="O1upd", attributes={"age": 88})
        assert isinstance(result, list)
        assert result[0].age == 88

    async def test_update_by_excluded_field_raises(self, controller):
        with pytest.raises(UnprocessableError):
            await controller.update_by(field="name", value="any", attributes={"email": "bad@x.com"})

    async def test_update_by_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.update_by(
                field="name",
                value="no_such_xyz",
                attributes={"age": 1},
                unique=True,
            )

    async def test_delete_by(self, controller):
        await controller.create({"name": "P1del", "email": "p1@x.com", "age": 20})
        result = await controller.delete_by(field="name", value="P1del")
        assert isinstance(result, list)
        assert result[0].name == "P1del"

    async def test_delete_by_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.delete_by(field="name", value="no_such_xyz", unique=True)

    async def test_update_by_id_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.update_by_id(999999, {"age": 1})

    async def test_update_by_id_excluded_field_raises(self, controller):
        user = await controller.create({"name": "Q1upd", "email": "q1@x.com", "age": 21})
        with pytest.raises(UnprocessableError):
            await controller.update_by_id(user.id, {"email": "new@x.com"})

    async def test_delete_by_id_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.delete_by_id(999999)

    async def test_create_many(self, controller):
        users = await controller.create_many(
            [
                {"name": "CM1", "email": "cm1@x.com", "age": 31},
                {"name": "CM2", "email": "cm2@x.com", "age": 32},
            ],
        )
        assert len(users) == 2

    async def test_delete(self, controller):
        user = await controller.create({"name": "Del1ctrl", "email": "del1ctrl@x.com", "age": 42})
        deleted = await controller.delete(user)
        assert deleted.name == "Del1ctrl"

    async def test_pagination_response_pages(self, controller):
        for i in range(5):
            await controller.create({"name": f"Pg{i}", "email": f"pg{i}@x.com", "age": i})
        response = await controller.get_all(skip=0, limit=2)
        assert isinstance(response, PaginationResponse)
        assert response.page == 1
        assert response.total_pages >= 3

    async def test_get_by_uuid_found(self, controller):
        # UserModel uses integer PK; passing the integer ID through get_by_uuid exercises
        # the success return path (line 130 in abs/controller/async_.py)
        user = await controller.create({"name": "UUID1", "email": "uuid1@x.com", "age": 10})
        found = await controller.get_by_uuid(user.id)
        assert found.name == "UUID1"

    async def test_get_by_uuid_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by_uuid(999999)

    async def test_update_by_uuid_found(self, controller):
        user = await controller.create({"name": "UUIDU1", "email": "uuidu1@x.com", "age": 10})
        user_id = user.id
        await controller.update_by_uuid(user_id, {"age": 55})
        controller.repository.session.expire_all()
        found = await controller.get_by_id(user_id)
        assert found.age == 55

    async def test_update_by_uuid_excluded_field_raises(self, controller):
        user = await controller.create({"name": "UUIDEX1", "email": "uuidex1@x.com", "age": 10})
        with pytest.raises(UnprocessableError):
            await controller.update_by_uuid(user.id, {"email": "bad@x.com"})

    async def test_update_by_uuid_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.update_by_uuid(999999, {"age": 1})

    async def test_delete_by_uuid_found(self, controller):
        user = await controller.create({"name": "UUIDDEL1", "email": "uuiddel1@x.com", "age": 11})
        user_id = user.id
        result = await controller.delete_by_uuid(user_id)
        assert result.name == "UUIDDEL1"

    async def test_delete_by_uuid_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.delete_by_uuid(999999)

    async def test_delete_by_filters_unique_found(self, controller):
        await controller.create({"name": "DBFuniq", "email": "dbfuniq@x.com", "age": 55})
        result = await controller.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="DBFuniq", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result.name == "DBFuniq"

    async def test_delete_by_unique_found(self, controller):
        await controller.create({"name": "DBuniq", "email": "dbuniq@x.com", "age": 56})
        result = await controller.delete_by(field="name", value="DBuniq", unique=True)
        assert result.name == "DBuniq"

    async def test_update_by_unique_found(self, controller):
        await controller.create({"name": "UBuniq", "email": "ubuniq@x.com", "age": 57})
        result = await controller.update_by(
            field="name",
            value="UBuniq",
            attributes={"age": 99},
            unique=True,
        )
        assert result.age == 99

    async def test_update_by_filters_unique_found(self, controller):
        await controller.create({"name": "UBFuniq", "email": "ubfuniq@x.com", "age": 58})
        result = await controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="UBFuniq", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 100},
            unique=True,
        )
        assert result.age == 100

    async def test_create_or_update_creates_new(self, repo):
        ctrl = AsyncSQLiteController(model=UserModel, repository=repo, exclude_fields=[])
        model = UserModel(name="CTRL_COU_New", email="ctrl_cou_new@x.com", age=11)
        result = await ctrl.create_or_update(model)
        assert result is not None
        assert result.name == "CTRL_COU_New"

    async def test_create_or_update_updates_existing(self, repo):
        ctrl = AsyncSQLiteController(model=UserModel, repository=repo, exclude_fields=[])
        await ctrl.create_or_update_by(
            attributes={"name": "CTRL_COU_E", "email": "ctrl_cou_e@x.com", "age": 22},
        )
        repo.session.expire_all()
        model = UserModel(name="CTRL_COU_E_upd", email="ctrl_cou_e@x.com", age=99)
        result = await ctrl.create_or_update(model)
        assert result is not None
        assert result.age == 99

    async def test_create_or_update_many_empty(self, controller):
        result = await controller.create_or_update_many([])
        assert result == []

    async def test_create_or_update_many_all_new(self, repo):
        ctrl = AsyncSQLiteController(model=UserModel, repository=repo, exclude_fields=[])
        models = [
            UserModel(name="CTRL_COUM_N1", email="ctrl_coum_n1@x.com", age=1),
            UserModel(name="CTRL_COUM_N2", email="ctrl_coum_n2@x.com", age=2),
        ]
        results = await ctrl.create_or_update_many(models)
        assert len(results) == 2
        assert all(r.id is not None for r in results)

    async def test_update_many_empty(self, controller):
        result = await controller.update_many([])
        assert result == []

    async def test_update_many_multiple(self, repo):
        ctrl = AsyncSQLiteController(model=UserModel, repository=repo, exclude_fields=[])
        user1 = await ctrl.create({"name": "CTRL_UM1", "email": "ctrl_um1@x.com", "age": 10})
        user2 = await ctrl.create({"name": "CTRL_UM2", "email": "ctrl_um2@x.com", "age": 20})
        user1.age = 88
        user2.age = 77
        results = await ctrl.update_many([user1, user2])
        assert len(results) == 2
        ages = {r.age for r in results}
        assert ages == {88, 77}

    async def test_delete_many_empty(self, controller):
        result = await controller.delete_many([])
        assert result == []

    async def test_delete_many_multiple(self, repo):
        ctrl = AsyncSQLiteController(model=UserModel, repository=repo, exclude_fields=[])
        user1 = await ctrl.create({"name": "CTRL_DM1", "email": "ctrl_dm1@x.com", "age": 10})
        user2 = await ctrl.create({"name": "CTRL_DM2", "email": "ctrl_dm2@x.com", "age": 20})
        results = await ctrl.delete_many([user1, user2])
        assert len(results) == 2
        found = await repo.get_by(field="email", value="ctrl_dm1@x.com", unique=True)
        assert found is None
