# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for SyncMongoController."""

import pytest
from pydantic import BaseModel

from axiom.core.exceptions.http import NotFoundError, UnprocessableError
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator
from axiom.core.schema.response import CountResponse, PaginationResponse
from axiom.oltp.beanie.base.controller.sync import SyncMongoController
from axiom.oltp.beanie.base.repository.sync import SyncMongoRepository
from tests.fixtures.sync_models import SyncUserModel


class UserSchema(BaseModel):
    name: str
    email: str
    age: int


@pytest.fixture
def sync_repo(sync_db):
    return SyncMongoRepository(
        model=SyncUserModel,
        collection=sync_db[SyncUserModel.Settings.name],
    )


@pytest.fixture
def sync_controller(sync_repo):
    return SyncMongoController(
        model=SyncUserModel,
        repository=sync_repo,
        exclude_fields=["email"],
    )


class TestSyncController:
    def test_create_and_get_by_id(self, sync_controller):
        user = sync_controller.create({"name": "Alice", "email": "a@x.com", "age": 20})
        assert user.id is not None
        found = sync_controller.get_by_id(user.id)
        assert found.name == "Alice"

    def test_get_all_pagination_response(self, sync_controller):
        sync_controller.create({"name": "B1", "email": "b1@x.com", "age": 21})
        sync_controller.create({"name": "B2", "email": "b2@x.com", "age": 22})
        response = sync_controller.get_all(skip=0, limit=10)
        assert isinstance(response, PaginationResponse)
        assert response.total_count >= 2
        assert isinstance(response.data, list)
        assert response.page == 1

    def test_update_by_id(self, sync_controller):
        user = sync_controller.create({"name": "C1", "email": "c1@x.com", "age": 30})
        updated = sync_controller.update_by_id(user.id, {"name": "C1_updated", "age": 31})
        assert updated.name == "C1_updated"

    def test_delete_by_id(self, sync_controller):
        user = sync_controller.create({"name": "D1", "email": "d1@x.com", "age": 40})
        deleted = sync_controller.delete_by_id(user.id)
        assert deleted.name == "D1"
        with pytest.raises(NotFoundError):
            sync_controller.get_by_id(user.id)

    def test_get_by_id_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.get_by_id("000000000000000000000000")

    def test_get_by_filters(self, sync_controller):
        sync_controller.create({"name": "E1", "email": "e1@x.com", "age": 50})
        sync_controller.create({"name": "E2", "email": "e2@x.com", "age": 51})
        response = sync_controller.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="E1", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(response, PaginationResponse)
        assert response.total_count == 1

    def test_count(self, sync_controller):
        sync_controller.create({"name": "F1", "email": "f1@x.com", "age": 60})
        response = sync_controller.count()
        assert isinstance(response, CountResponse)
        assert response.count >= 1

    def test_update_excluded_field(self, sync_controller):
        user = sync_controller.create({"name": "G1", "email": "g1@x.com", "age": 70})
        with pytest.raises(UnprocessableError):
            sync_controller.update(user, {"email": "new@x.com"})

    def test_extract_attributes_from_schema(self, sync_controller):
        schema = UserSchema(name="H1", email="h1@x.com", age=80)
        attrs = sync_controller.extract_attributes_from_schema(schema)
        assert attrs == {"name": "H1", "email": "h1@x.com", "age": 80}

    def test_repr(self, sync_controller):
        assert repr(sync_controller) == "<SyncMongoController>"

    def test_get_by_returns_pagination(self, sync_controller):
        sync_controller.create({"name": "I1", "email": "i1@x.com", "age": 11})
        response = sync_controller.get_by(field="name", value="I1")
        assert isinstance(response, PaginationResponse)
        assert response.total_count == 1

    def test_get_by_unique(self, sync_controller):
        sync_controller.create({"name": "J1", "email": "j1@x.com", "age": 13})
        result = sync_controller.get_by(field="name", value="J1", unique=True)
        assert result.name == "J1"

    def test_get_by_unique_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.get_by(field="name", value="no_such_name", unique=True)

    def test_get_by_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.get_by(field="name", value="no_such_abc")

    def test_update_by(self, sync_controller):
        sync_controller.create({"name": "K1upd", "email": "k1@x.com", "age": 19})
        result = sync_controller.update_by(field="name", value="K1upd", attributes={"age": 88})
        assert isinstance(result, list)
        assert result[0].age == 88

    def test_delete_by(self, sync_controller):
        sync_controller.create({"name": "L1del", "email": "l1@x.com", "age": 20})
        result = sync_controller.delete_by(field="name", value="L1del")
        assert isinstance(result, list)
        assert result[0].name == "L1del"

    def test_update_by_filters(self, sync_controller):
        sync_controller.create({"name": "M1filter", "email": "m1@x.com", "age": 17})
        result = sync_controller.update_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="M1filter", operator=QueryOperator.EQUALS),
            ),
            attributes={"age": 99},
        )
        assert isinstance(result, list)
        assert result[0].age == 99

    def test_update_by_filters_excluded_raises(self, sync_controller):
        with pytest.raises(UnprocessableError):
            sync_controller.update_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(field="name", value="any", operator=QueryOperator.EQUALS),
                ),
                attributes={"email": "bad@x.com"},
            )

    def test_delete_by_filters(self, sync_controller):
        sync_controller.create({"name": "N1filter", "email": "n1@x.com", "age": 18})
        result = sync_controller.delete_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="N1filter", operator=QueryOperator.EQUALS),
            ),
        )
        assert isinstance(result, list)
        assert result[0].name == "N1filter"

    def test_update_by_id_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.update_by_id("000000000000000000000000", {"age": 1})

    def test_delete_by_id_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.delete_by_id("000000000000000000000000")

    def test_update_by_id_excluded_field_raises(self, sync_controller):
        user = sync_controller.create({"name": "O1upd", "email": "o1@x.com", "age": 21})
        with pytest.raises(UnprocessableError):
            sync_controller.update_by_id(user.id, {"email": "new@x.com"})

    def test_create_or_update_by(self, sync_controller):
        ctrl = SyncMongoController(
            model=SyncUserModel,
            repository=sync_controller.repository,
            exclude_fields=[],
        )
        user = ctrl.create_or_update_by(
            attributes={"name": "P1ctrl", "email": "p1@x.com", "age": 15},
        )
        assert user.name == "P1ctrl"
        updated = ctrl.create_or_update_by(
            attributes={"name": "P1ctrl", "email": "p1@x.com", "age": 99},
            update_fields=["age"],
        )
        assert updated.age == 99

    def test_create_or_update_by_excluded_raises(self, sync_controller):
        with pytest.raises(UnprocessableError):
            sync_controller.create_or_update_by(
                attributes={"name": "Q1", "email": "excluded@x.com", "age": 16},
            )

    def test_update_by_excluded_field_raises(self, sync_controller):
        with pytest.raises(UnprocessableError):
            sync_controller.update_by(field="name", value="any", attributes={"email": "bad@x.com"})

    def test_delete_by_filters_unique_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.delete_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )

    def test_update_by_filters_unique_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.update_by_filters(
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

    def test_update_by_unique_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.update_by(
                field="name",
                value="no_such_xyz",
                attributes={"age": 1},
                unique=True,
            )

    def test_delete_by_unique_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.delete_by(field="name", value="no_such_xyz", unique=True)

    def test_create_many(self, sync_controller):
        users = sync_controller.create_many(
            [
                {"name": "R1", "email": "r1@x.com", "age": 50},
                {"name": "R2", "email": "r2@x.com", "age": 51},
            ],
        )
        assert len(users) == 2

    def test_get_by_filters_unique_found(self, sync_controller):
        sync_controller.create({"name": "S1unique", "email": "s1@x.com", "age": 14})
        result = sync_controller.get_by_filters(
            filter_request=FilterRequest(
                chain=FilterParam(field="name", value="S1unique", operator=QueryOperator.EQUALS),
            ),
            unique=True,
        )
        assert result.name == "S1unique"

    def test_get_by_filters_unique_not_found(self, sync_controller):
        with pytest.raises(NotFoundError):
            sync_controller.get_by_filters(
                filter_request=FilterRequest(
                    chain=FilterParam(
                        field="name",
                        value="no_such_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )
