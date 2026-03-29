# ruff: noqa: W505, D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="name-defined,valid-type"
"""axiom.oltp.sqlalchemy.abs.repository.sync_ — Abstract sync repository."""

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any

from axiom.core.exceptions import ValidationError
from axiom.oltp.sqlalchemy.base.filter.schema import FilterParam, FilterRequest
from axiom.oltp.sqlalchemy.base.filter.type import QueryOperator, SortTypeEnum
from sqlalchemy import inspect
from sqlalchemy.orm import selectinload


class SyncBaseRepository[ModelType, SessionType, QueryType](ABC):
    """Abstract base class for sync data repositories."""

    def __init__(self, model: type[ModelType], db_session: SessionType) -> None:
        self.session = db_session
        self.model_class = model

    @abstractmethod
    def create(self, attributes: dict[str, Any]) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def create_many(self, attributes_list: list[dict[str, Any]]) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def update_by(
        self,
        field: str,
        value: Any,
        attributes: dict[str, Any],
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def update_by_filters(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def delete(self, model: ModelType) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def delete_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_filters(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    def _query(self) -> QueryType:
        raise NotImplementedError

    @abstractmethod
    def _maybe_join(self, query: QueryType, field: str) -> QueryType:
        raise NotImplementedError

    @abstractmethod
    def _filter(self, query: QueryType, filter_request: FilterRequest) -> QueryType:
        raise NotImplementedError

    @abstractmethod
    def _paginate(self, query: QueryType, skip: int = 0, limit: int = 100) -> QueryType:
        raise NotImplementedError

    @abstractmethod
    def _sort_by(
        self,
        query: QueryType,
        sort_by: str | None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> QueryType:
        raise NotImplementedError

    @abstractmethod
    def _get_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def _all(self, query: QueryType) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    def _one_or_none(self, query: QueryType) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    def _count(self, query: QueryType) -> int:
        raise NotImplementedError

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> list[ModelType]:
        query = self._query()
        query = self._sort_by(query=query, sort_by=sort_by, sort_type=sort_type)
        query = self._paginate(query=query, skip=skip, limit=limit)
        return self._all(query)

    def get_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        query = self._query()
        mapper = inspect(self.model_class)
        for rel in mapper.relationships:  # type: ignore[union-attr]
            if rel.lazy and rel.lazy == "selectin":
                query = query.options(selectinload(getattr(self.model_class, rel.key)))  # type: ignore[attr-defined]
        query = self._maybe_join(query=query, field=field)
        query = self._filter(
            query=query,
            filter_request=FilterRequest(
                chain=FilterParam(field=field, value=value, operator=operator),
            ),
        )
        if unique:
            return self._one_or_none(query)
        query = self._sort_by(query=query, sort_by=sort_by, sort_type=sort_type)
        query = self._paginate(query=query, skip=skip, limit=limit)
        return self._all(query)

    def get_by_filters(
        self,
        filter_request: FilterRequest | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        query = self._query()
        if filter_request is not None:
            for param in filter_request.extract_filter_params():
                query = self._maybe_join(query=query, field=param.field)
            query = self._filter(query=query, filter_request=filter_request)
        if unique:
            return self._one_or_none(query)
        query = self._sort_by(query=query, sort_by=sort_by, sort_type=sort_type)
        query = self._paginate(query=query, skip=skip, limit=limit)
        return self._all(query)

    def count(self, filter_request: FilterRequest | None = None) -> int:
        query = self._query()
        if filter_request is not None:
            for param in filter_request.extract_filter_params():
                query = self._maybe_join(query=query, field=param.field)
            query = self._filter(query, filter_request)
        return self._count(query)

    def _get_deep_unique_from_dict(
        self,
        columns: dict[str, Any] | list[dict[str, Any]],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if isinstance(columns, dict):
            result = {}
            for key, value in columns.items():
                result[key] = self._get_deep_unique_from_dict(value)
            return result
        elif isinstance(columns, list):
            if all(isinstance(item, dict) for item in columns):
                aggregated: dict[str, list[Any]] = defaultdict(list)
                for item in columns:
                    for k, v in item.items():
                        processed_v = self._get_deep_unique_from_dict(v)
                        if processed_v not in aggregated[k]:
                            aggregated[k].append(processed_v)
                return self._get_deep_unique_from_dict(aggregated)
            else:
                processed_list = []
                for item in columns:
                    processed_item = self._get_deep_unique_from_dict(item)
                    if processed_item not in processed_list:
                        processed_list.append(processed_item)
                return processed_list  # type: ignore[return-value]
        else:
            return columns  # type: ignore[unreachable]

    def _get_model_field_type(self, _model: type[ModelType], _field: str) -> type:
        raise NotImplementedError

    def _resolve_field_relation(self, field: str) -> tuple[type[ModelType], str]:
        raise NotImplementedError

    def _validate_params(self, field: str, value: Any | None = None) -> None:
        model, column_name = self._resolve_field_relation(field)
        model_field_type = self._get_model_field_type(model, column_name)
        if issubclass(model_field_type, dict):
            return None
        if issubclass(model_field_type, Enum):
            if all(value != item for item in model_field_type):
                raise ValidationError(
                    f"Value {value} is not permissible for the field {field}. "
                    f"Available values: {[e for e in model_field_type]}",
                )
            enum_member = next(iter(model_field_type)).value
            model_field_type = type(enum_member)
        if value is not None and not isinstance(value, model_field_type):
            raise ValidationError(
                f"Wrong type for field {field}: "
                f"expected {model_field_type.__name__}, "
                f"received {type(value).__name__}",
            )
        return None
