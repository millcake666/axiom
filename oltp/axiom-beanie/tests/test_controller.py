# ruff: noqa: D100, D101, D102, D103, E501
"""Integration tests for AsyncBeanieController."""

import pytest
from pydantic import BaseModel

from axiom.core.exceptions.http import NotFoundError, UnprocessableError
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator
from axiom.core.schema.response import CountResponse, PaginationResponse
from axiom.oltp.beanie.base.controller.async_ import AsyncBeanieController
from axiom.oltp.beanie.base.repository.async_ import AsyncBeanieRepository
from tests.fixtures.models import UserDocument


class UserSchema(BaseModel):
    name: str
    email: str
    age: int


@pytest.fixture
def repo(session):
    return AsyncBeanieRepository(model=UserDocument, db_session=session)


@pytest.fixture
def controller(repo):
    return AsyncBeanieController(
        model=UserDocument,
        repository=repo,
        exclude_fields=["email"],
    )


@pytest.mark.usefixtures("beanie_init")
class TestController:
    async def test_create_and_get_by_id(self, controller):
        user = await controller.create({"name": "Alice", "email": "a@x.com", "age": 20})
        assert user.id is not None
        found = await controller.get_by_id(str(user.id))
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
        updated = await controller.update_by_id(str(user.id), {"name": "C1_updated", "age": 31})
        assert updated.name == "C1_updated"

    async def test_delete_by_id(self, controller):
        user = await controller.create({"name": "D1", "email": "d1@x.com", "age": 40})
        deleted = await controller.delete_by_id(str(user.id))
        assert deleted.name == "D1"
        with pytest.raises(NotFoundError):
            await controller.get_by_id(str(user.id))

    async def test_get_by_id_not_found(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by_id("000000000000000000000000")

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

    async def test_count(self, controller):
        await controller.create({"name": "F1", "email": "f1@x.com", "age": 60})
        response = await controller.count()
        assert isinstance(response, CountResponse)
        assert response.count >= 1

    async def test_update_excluded_field(self, controller):
        user = await controller.create({"name": "G1", "email": "g1@x.com", "age": 70})
        with pytest.raises(UnprocessableError):
            await controller.update(user, {"email": "new@x.com"})

    async def test_extract_attributes_from_schema(self, controller):
        schema = UserSchema(name="H1", email="h1@x.com", age=80)
        attrs = await controller.extract_attributes_from_schema(schema)
        assert attrs == {"name": "H1", "email": "h1@x.com", "age": 80}

    async def test_repr(self, controller):
        assert repr(controller) == "<AsyncBeanieController>"

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
                        value="no_such_name_xyz",
                        operator=QueryOperator.EQUALS,
                    ),
                ),
                unique=True,
            )

    async def test_create_or_update_by(self, repo):
        from axiom.oltp.beanie.base.controller.async_ import AsyncBeanieController

        ctrl = AsyncBeanieController(model=UserDocument, repository=repo, exclude_fields=[])
        user = await ctrl.create_or_update_by(
            attributes={"name": "L1ctrl", "email": "l1ctrl@x.com", "age": 15},
        )
        assert user.name == "L1ctrl"
        updated = await ctrl.create_or_update_by(
            attributes={"name": "L1ctrl", "email": "l1ctrl@x.com", "age": 99},
            update_fields=["age"],
        )
        assert updated.age == 99

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
            await controller.update_by_id("000000000000000000000000", {"age": 1})

    async def test_update_by_id_excluded_field_raises(self, controller):
        user = await controller.create({"name": "Q1upd", "email": "q1@x.com", "age": 21})
        with pytest.raises(UnprocessableError):
            await controller.update_by_id(str(user.id), {"email": "new@x.com"})

    async def test_delete_by_id_not_found_raises(self, controller):
        with pytest.raises(NotFoundError):
            await controller.delete_by_id("000000000000000000000000")
