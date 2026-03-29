# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for SyncSQLAlchemyController with SyncSQLiteRepository."""

import pytest
from pydantic import BaseModel

from axiom.core.exceptions import NotFoundError, UnprocessableError
from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.core.schema import CountResponse, PaginationResponse
from axiom.oltp.sqlalchemy.base.controller.sync import SyncSQLAlchemyController
from axiom.oltp.sqlalchemy.sqlite.repository.sync import SyncSQLiteRepository
from tests.fixtures.models import UserModel


class UserSchema(BaseModel):
    name: str
    email: str
    age: int


@pytest.fixture
def repo(sync_session):
    return SyncSQLiteRepository(model=UserModel, db_session=sync_session)


@pytest.fixture
def controller(repo):
    return SyncSQLAlchemyController(
        model=UserModel,
        repository=repo,
        exclude_fields=["email"],
    )


class TestSyncController:
    def test_create_and_get_by_id(self, controller):
        user = controller.create({"name": "Alice", "email": "a@x.com", "age": 20})
        assert user.id is not None
        found = controller.get_by_id(user.id)
        assert found.name == "Alice"

    def test_get_all_pagination_response(self, controller):
        controller.create({"name": "B1", "email": "b1@x.com", "age": 21})
        controller.create({"name": "B2", "email": "b2@x.com", "age": 22})
        response = controller.get_all(skip=0, limit=10)
        assert isinstance(response, PaginationResponse)
        assert response.total_count >= 2
        assert isinstance(response.data, list)
        assert response.page == 1

    def test_update_by_id(self, controller):
        user = controller.create({"name": "C1", "email": "c1@x.com", "age": 30})
        controller.update_by_id(user.id, {"name": "C1_updated", "age": 31})
        # expire identity map so get_by_id fetches fresh data from DB
        controller.repository.session.expire_all()
        found = controller.get_by_id(user.id)
        assert found.name == "C1_updated"

    def test_delete_by_id(self, controller):
        user = controller.create({"name": "D1", "email": "d1@x.com", "age": 40})
        deleted = controller.delete_by_id(user.id)
        assert deleted.name == "D1"
        with pytest.raises(NotFoundError):
            controller.get_by_id(user.id)

    def test_get_by_id_not_found(self, controller):
        with pytest.raises(NotFoundError):
            controller.get_by_id(999999)

    def test_get_by_filters(self, controller):
        controller.create({"name": "E1", "email": "e1@x.com", "age": 50})
        controller.create({"name": "E2", "email": "e2@x.com", "age": 51})
        response = controller.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="E1", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(response, PaginationResponse)
        assert response.total_count == 1

    def test_get_by_filters_no_filter(self, controller):
        controller.create({"name": "E3", "email": "e3@x.com", "age": 52})
        response = controller.get_by_filters()
        assert isinstance(response, PaginationResponse)
        assert response.total_count >= 1

    def test_count(self, controller):
        controller.create({"name": "F1", "email": "f1@x.com", "age": 60})
        response = controller.count()
        assert isinstance(response, CountResponse)
        assert response.count >= 1

    def test_update_allowed_field(self, controller):
        user = controller.create({"name": "G0", "email": "g0@x.com", "age": 69})
        updated = controller.update(user, {"age": 100})
        assert updated.age == 100

    def test_update_excluded_field_raises(self, controller):
        user = controller.create({"name": "G1", "email": "g1@x.com", "age": 70})
        with pytest.raises(UnprocessableError):
            controller.update(user, {"email": "new@x.com"})

    def test_extract_attributes_from_schema(self, controller):
        schema = UserSchema(name="H1", email="h1@x.com", age=80)
        attrs = controller.extract_attributes_from_schema(schema)
        assert attrs == {"name": "H1", "email": "h1@x.com", "age": 80}

    def test_repr(self, controller):
        assert "SyncSQLAlchemyController" in repr(controller)

    def test_get_by_returns_pagination(self, controller):
        controller.create({"name": "I1", "email": "i1@x.com", "age": 11})
        response = controller.get_by(field="name", value="I1")
        assert isinstance(response, PaginationResponse)
        assert response.total_count == 1

    def test_get_by_unique_returns_model(self, controller):
        controller.create({"name": "J1", "email": "j1@x.com", "age": 13})
        result = controller.get_by(field="name", value="J1", unique=True)
        assert result.name == "J1"

    def test_get_by_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.get_by(field="name", value="nonexistent_xyz", unique=True)

    def test_get_by_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.get_by(field="name", value="no_such_name_abc")

    def test_get_by_filters_unique_found(self, controller):
        controller.create({"name": "K1unique", "email": "k1@x.com", "age": 14})
        result = controller.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="K1unique", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result.name == "K1unique"

    def test_get_by_filters_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.get_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )

    def test_create_or_update_by(self, repo):
        ctrl = SyncSQLAlchemyController(model=UserModel, repository=repo, exclude_fields=[])
        user = ctrl.create_or_update_by(
            attributes={"name": "L1ctrl", "email": "l1ctrl@x.com", "age": 15},
        )
        assert user.name == "L1ctrl"
        ctrl.create_or_update_by(
            attributes={"name": "L1ctrl Updated", "email": "l1ctrl@x.com", "age": 99},
            update_fields=["name", "age"],
        )
        # expire identity map so get_by fetches fresh data from DB
        repo.session.expire_all()
        found = repo.get_by(field="email", value="l1ctrl@x.com", unique=True)
        assert found.age == 99

    def test_create_or_update_by_excluded_field_raises(self, controller):
        with pytest.raises(UnprocessableError):
            controller.create_or_update_by(
                attributes={"name": "L2", "email": "excluded@x.com", "age": 16},
            )

    def test_update_by_filters(self, controller):
        controller.create({"name": "M1filter", "email": "m1@x.com", "age": 17})
        result = controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="M1filter", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 99},
        )
        assert isinstance(result, list)
        assert result[0].age == 99

    def test_update_by_filters_excluded_field_raises(self, controller):
        with pytest.raises(UnprocessableError):
            controller.update_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(field="name", value="any", operator=QueryOperator.EQUALS),
                ),
                attributes={"email": "bad@x.com"},
            )

    def test_update_by_filters_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.update_by_filters(
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

    def test_delete_by_filters(self, controller):
        controller.create({"name": "N1filter", "email": "n1@x.com", "age": 18})
        result = controller.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="N1filter", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(result, list)
        assert result[0].name == "N1filter"

    def test_delete_by_filters_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.delete_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )

    def test_update_by(self, controller):
        controller.create({"name": "O1upd", "email": "o1@x.com", "age": 19})
        result = controller.update_by(field="name", value="O1upd", attributes={"age": 88})
        assert isinstance(result, list)
        assert result[0].age == 88

    def test_update_by_excluded_field_raises(self, controller):
        with pytest.raises(UnprocessableError):
            controller.update_by(field="name", value="any", attributes={"email": "bad@x.com"})

    def test_update_by_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.update_by(
                field="name",
                value="no_such_xyz",
                attributes={"age": 1},
                unique=True,
            )

    def test_delete_by(self, controller):
        controller.create({"name": "P1del", "email": "p1@x.com", "age": 20})
        result = controller.delete_by(field="name", value="P1del")
        assert isinstance(result, list)
        assert result[0].name == "P1del"

    def test_delete_by_unique_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.delete_by(field="name", value="no_such_xyz", unique=True)

    def test_update_by_id_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.update_by_id(999999, {"age": 1})

    def test_update_by_id_excluded_field_raises(self, controller):
        user = controller.create({"name": "Q1upd", "email": "q1@x.com", "age": 21})
        with pytest.raises(UnprocessableError):
            controller.update_by_id(user.id, {"email": "new@x.com"})

    def test_delete_by_id_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.delete_by_id(999999)

    def test_create_many(self, controller):
        users = controller.create_many(
            [
                {"name": "CM1", "email": "cm1@x.com", "age": 31},
                {"name": "CM2", "email": "cm2@x.com", "age": 32},
            ],
        )
        assert len(users) == 2

    def test_delete(self, controller):
        user = controller.create({"name": "Del1ctrl", "email": "del1ctrl@x.com", "age": 42})
        deleted = controller.delete(user)
        assert deleted.name == "Del1ctrl"

    def test_pagination_response_pages(self, controller):
        for i in range(5):
            controller.create({"name": f"Pg{i}", "email": f"pg{i}@x.com", "age": i})
        response = controller.get_all(skip=0, limit=2)
        assert isinstance(response, PaginationResponse)
        assert response.total_pages >= 3

    def test_get_by_uuid_found(self, controller):
        user = controller.create({"name": "UUID1", "email": "uuid1@x.com", "age": 10})
        found = controller.get_by_uuid(user.id)
        assert found.name == "UUID1"

    def test_get_by_uuid_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.get_by_uuid(999999)

    def test_update_by_uuid_found(self, controller):
        user = controller.create({"name": "UUIDU1", "email": "uuidu1@x.com", "age": 10})
        user_id = user.id
        controller.update_by_uuid(user_id, {"age": 55})
        controller.repository.session.expire_all()
        found = controller.get_by_id(user_id)
        assert found.age == 55

    def test_update_by_uuid_excluded_field_raises(self, controller):
        user = controller.create({"name": "UUIDEX1", "email": "uuidex1@x.com", "age": 10})
        with pytest.raises(UnprocessableError):
            controller.update_by_uuid(user.id, {"email": "bad@x.com"})

    def test_update_by_uuid_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.update_by_uuid(999999, {"age": 1})

    def test_delete_by_uuid_found(self, controller):
        user = controller.create({"name": "UUIDDEL1", "email": "uuiddel1@x.com", "age": 11})
        result = controller.delete_by_uuid(user.id)
        assert result.name == "UUIDDEL1"

    def test_delete_by_uuid_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            controller.delete_by_uuid(999999)

    def test_delete_by_filters_unique_found(self, controller):
        controller.create({"name": "DBFuniq", "email": "dbfuniq@x.com", "age": 55})
        result = controller.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="DBFuniq", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result.name == "DBFuniq"

    def test_delete_by_unique_found(self, controller):
        controller.create({"name": "DBuniq", "email": "dbuniq@x.com", "age": 56})
        result = controller.delete_by(field="name", value="DBuniq", unique=True)
        assert result.name == "DBuniq"

    def test_update_by_unique_found(self, controller):
        controller.create({"name": "UBuniq", "email": "ubuniq@x.com", "age": 57})
        result = controller.update_by(
            field="name",
            value="UBuniq",
            attributes={"age": 99},
            unique=True,
        )
        assert result.age == 99

    def test_update_by_filters_unique_found(self, controller):
        controller.create({"name": "UBFuniq", "email": "ubfuniq@x.com", "age": 58})
        result = controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="UBFuniq", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 100},
            unique=True,
        )
        assert result.age == 100
