# ruff: noqa: D100, D101, D102, D103, E501
"""Unit tests for utilities: to_snake, AsDictMixin, filter schema, response schemas."""

from axiom.core.filter import (
    FilterGroup,
    FilterParam,
    FilterRequest,
    FilterType,
    QueryOperator,
    SortParams,
    SortTypeEnum,
)
from axiom.core.schema import CountResponse, PaginationResponse
from axiom.oltp.sqlalchemy.base.declarative import to_snake
from tests.fixtures.models import UserModel


class TestToSnake:
    def test_pascal_case(self):
        assert to_snake("UserModel") == "user_model"

    def test_camel_case(self):
        assert to_snake("userModel") == "user_model"

    def test_single_word(self):
        assert to_snake("User") == "user"

    def test_already_snake(self):
        assert to_snake("user_model") == "user_model"

    def test_kebab_case(self):
        assert to_snake("user-model") == "user_model"

    def test_consecutive_uppercase(self):
        assert to_snake("HTTPSConnector") == "https_connector"

    def test_number_transition(self):
        # "Model3D" -> "model_3_d"
        result = to_snake("Model3D")
        assert result == "model_3_d"


class TestAsDictMixin:
    def test_as_dict_basic(self, sync_session):
        from axiom.oltp.sqlalchemy.sqlite.repository.sync import SyncSQLiteRepository

        repo = SyncSQLiteRepository(model=UserModel, db_session=sync_session)
        user = repo.create({"name": "DictUser", "email": "dict@test.com", "age": 25})
        sync_session.flush()
        d = user.as_dict()
        assert d["name"] == "DictUser"
        assert d["age"] == 25
        assert "id" in d

    def test_as_dict_exclude_none(self, sync_session):
        from axiom.oltp.sqlalchemy.sqlite.repository.sync import SyncSQLiteRepository

        repo = SyncSQLiteRepository(model=UserModel, db_session=sync_session)
        user = repo.create({"name": "NoNone", "email": "none@test.com", "age": 30})
        sync_session.flush()
        d = user.as_dict(exclude_none=True)
        assert "name" in d
        assert all(v is not None for v in d.values())

    def test_as_dict_exclude_columns(self, sync_session):
        from axiom.oltp.sqlalchemy.sqlite.repository.sync import SyncSQLiteRepository

        repo = SyncSQLiteRepository(model=UserModel, db_session=sync_session)
        user = repo.create({"name": "ExcludeCol", "email": "excol@test.com", "age": 35})
        sync_session.flush()
        d = user.as_dict(exclude_columns=["email"])
        assert "email" not in d
        assert "name" in d


class TestFilterSchema:
    def test_filter_param_repr(self):
        fp = FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS)
        r = repr(fp)
        assert "FilterParam" in r
        assert "name" in r

    def test_filter_param_extract(self):
        fp = FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS)
        params = fp.extract_filter_params()
        assert len(params) == 1
        assert params[0] is fp

    def test_filter_group_and_operator(self):
        fp1 = FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS)
        fp2 = FilterParam(field="age", value=30, operator=QueryOperator.EQUALS)
        group = fp1 & fp2
        assert isinstance(group, FilterGroup)
        assert group.type == FilterType.AND
        assert len(group.items) == 2

    def test_filter_group_or_operator(self):
        fp1 = FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS)
        fp2 = FilterParam(field="name", value="Bob", operator=QueryOperator.EQUALS)
        group = fp1 | fp2
        assert isinstance(group, FilterGroup)
        assert group.type == FilterType.OR

    def test_filter_group_extract_params(self):
        fp1 = FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS)
        fp2 = FilterParam(field="age", value=30, operator=QueryOperator.EQUALS)
        group = FilterGroup(type=FilterType.AND, items=[fp1, fp2])
        params = group.extract_filter_params()
        assert len(params) == 2

    def test_filter_group_repr(self):
        fp1 = FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS)
        fp2 = FilterParam(field="age", value=30, operator=QueryOperator.EQUALS)
        group = FilterGroup(type=FilterType.AND, items=[fp1, fp2])
        r = repr(group)
        assert "FilterGroup" in r

    def test_filter_request_repr(self):
        fr = FilterRequest(
            chain=FilterParam(field="name", value="x", operator=QueryOperator.EQUALS),
        )
        r = repr(fr)
        assert "FilterRequest" in r

    def test_filter_request_extract_params(self):
        fr = FilterRequest(
            chain=FilterParam(field="name", value="x", operator=QueryOperator.EQUALS),
        )
        params = fr.extract_filter_params()
        assert len(params) == 1

    def test_nested_filter_group_extract(self):
        fp1 = FilterParam(field="name", value="A", operator=QueryOperator.EQUALS)
        fp2 = FilterParam(field="age", value=1, operator=QueryOperator.EQUALS)
        fp3 = FilterParam(field="name", value="B", operator=QueryOperator.EQUALS)
        inner = fp1 & fp2
        outer = FilterGroup(type=FilterType.OR, items=[inner, fp3])
        fr = FilterRequest(chain=outer)
        params = fr.extract_filter_params()
        assert len(params) == 3


class TestFilterTypes:
    def test_query_operators_exist(self):
        ops = [
            QueryOperator.EQUALS,
            QueryOperator.NOT_EQUAL,
            QueryOperator.IN,
            QueryOperator.NOT_IN,
            QueryOperator.GREATER,
            QueryOperator.EQUALS_OR_GREATER,
            QueryOperator.LESS,
            QueryOperator.EQUALS_OR_LESS,
            QueryOperator.STARTS_WITH,
            QueryOperator.NOT_START_WITH,
            QueryOperator.ENDS_WITH,
            QueryOperator.NOT_END_WITH,
            QueryOperator.CONTAINS,
            QueryOperator.NOT_CONTAIN,
        ]
        assert len(ops) == 14

    def test_sort_type_enum(self):
        assert SortTypeEnum.asc.value == "asc"
        assert SortTypeEnum.desc.value == "desc"

    def test_sort_params(self):
        sp = SortParams(sort_by="name", sort_type=SortTypeEnum.asc)
        assert sp.sort_by == "name"
        assert sp.sort_type == SortTypeEnum.asc

    def test_filter_type_enum(self):
        assert FilterType.AND
        assert FilterType.OR


class TestResponseSchemas:
    def test_pagination_response(self):
        resp = PaginationResponse(
            data=["a", "b"],
            page=1,
            page_size=2,
            total_pages=5,
            total_count=10,
        )
        assert resp.page == 1
        assert resp.total_count == 10
        assert len(resp.data) == 2

    def test_count_response(self):
        resp = CountResponse(count=42)
        assert resp.count == 42


class TestDeclarativeBase:
    def test_tablename_auto_generation(self):
        # UserModel -> user_model
        assert UserModel.__tablename__ == "user_model"

    def test_base_is_abstract(self):
        from axiom.oltp.sqlalchemy.base.declarative import Base

        assert Base.__abstract__ is True
