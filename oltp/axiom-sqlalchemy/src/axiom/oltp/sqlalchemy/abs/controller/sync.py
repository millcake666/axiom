# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="type-arg,valid-type,name-defined,arg-type,attr-defined"
"""axiom.oltp.sqlalchemy.abs.controller.sync — Abstract sync controller."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from axiom.core.exceptions.http import NotFoundError, UnprocessableError
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator, SortTypeEnum
from axiom.core.schema.response import CountResponse, PaginationResponse
from axiom.oltp.sqlalchemy.abs.repository.sync import SyncBaseRepository


class SyncBaseController[ModelType](ABC):
    """Abstract base class for sync data controllers."""

    def __init__(
        self,
        model: type[ModelType],
        repository: SyncBaseRepository,
        exclude_fields: list[str],
    ) -> None:
        self.model_class = model
        self.repository = repository
        self.exclude_fields = exclude_fields

    @abstractmethod
    def processing_transaction(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError

    def transactional(function):  # type: ignore[no-untyped-def]
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            return self.processing_transaction(function, *args, **kwargs)

        return wrapper

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
    ) -> ModelType | PaginationResponse:
        db_obj = self.repository.get_by(
            field=field,
            value=value,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_type=sort_type,
            operator=operator,
            unique=unique,
        )
        if not db_obj:
            raise NotFoundError(
                f"{self.model_class.__name__} {field} with value {value} not exist",
            )
        if unique:
            return db_obj  # type: ignore[return-value]
        return self.make_pagination_response(
            data=db_obj,
            skip=skip,
            limit=limit,
            filter_request=FilterRequest(
                chain=FilterParam(field=field, value=value, operator=operator),
            ),
        )

    def get_by_filters(
        self,
        filter_request: FilterRequest | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
        unique: bool = False,
    ) -> ModelType | None | PaginationResponse:
        models = self.repository.get_by_filters(
            filter_request=filter_request,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_type=sort_type,
            unique=unique,
        )
        if unique:
            if models:
                return models  # type: ignore[return-value]
            else:
                raise NotFoundError(
                    f"Unique {self.model_class.__name__} with provided filters not exist",
                )
        return self.make_pagination_response(
            data=models,
            skip=skip,
            limit=limit,
            filter_request=filter_request,
        )

    def count(self, filter_request: FilterRequest | None = None) -> CountResponse:
        return CountResponse(count=self.repository.count(filter_request=filter_request))

    def get_by_id(self, id_: int) -> ModelType:
        db_obj = self.repository.get_by(field="id", value=id_, unique=True)
        if not db_obj:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return db_obj  # type: ignore[return-value]

    def get_by_uuid(self, uuid: UUID) -> ModelType:
        db_obj = self.repository.get_by(field="id", value=uuid, unique=True)
        if not db_obj:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found",
            )
        return db_obj  # type: ignore[return-value]

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> PaginationResponse:
        response = self.repository.get_all(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_type=sort_type,
        )
        return self.make_pagination_response(data=response, skip=skip, limit=limit)

    @transactional
    def create(self, attributes: dict[str, Any]) -> ModelType:
        return self.repository.create(attributes=attributes)

    @transactional
    def create_many(self, attributes_list: list[dict[str, Any]]) -> list[ModelType]:
        return self.repository.create_many(attributes_list)

    @transactional
    def delete(self, model: ModelType) -> ModelType:
        return self.repository.delete(model=model)

    @transactional
    def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        for field in attributes:
            if field in self.exclude_fields:
                raise UnprocessableError(f"Field {field} is prohibited for updating")
        return self.repository.update(model=model, attributes=attributes)

    @transactional
    def update_by_filters(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        for field in attributes:
            if field in self.exclude_fields:
                raise UnprocessableError(f"Field {field} is prohibited for updating")
        result = self.repository.update_by_filters(
            filter_request=filter_request,
            attributes=attributes,
            unique=unique,
        )
        if unique and result is None:
            raise NotFoundError(
                f"Unique {self.model_class.__name__} with provided filters not exist",
            )
        return result

    @transactional
    def delete_by_filters(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        result = self.repository.delete_by_filters(
            filter_request=filter_request,
            unique=unique,
        )
        if unique and result is None:
            raise NotFoundError(
                f"Unique {self.model_class.__name__} with provided filters not exist",
            )
        return result

    @transactional
    def update_by(
        self,
        field: str,
        value: Any,
        attributes: dict[str, Any],
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = self.repository.update_by(
            field=field,
            value=value,
            attributes=attributes,
            operator=operator,
            unique=unique,
        )
        if unique and result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} {field} with value {value} not exist",
            )
        return result

    @transactional
    def delete_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        result = self.repository.delete_by(
            field=field,
            value=value,
            operator=operator,
            unique=unique,
        )
        if unique and result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} {field} with value {value} not exist",
            )
        return result

    @transactional
    def update_by_id(self, id_: int, attributes: dict[str, Any]) -> ModelType:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = self.repository.update_by(
            field="id",
            value=id_,
            attributes=attributes,
            unique=True,
        )
        if result is None:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return result  # type: ignore[return-value]

    @transactional
    def update_by_uuid(self, uuid: UUID, attributes: dict[str, Any]) -> ModelType:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = self.repository.update_by(
            field="id",
            value=uuid,
            attributes=attributes,
            unique=True,
        )
        if result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found",
            )
        return result  # type: ignore[return-value]

    @transactional
    def delete_by_id(self, id_: int) -> ModelType:
        result = self.repository.delete_by(field="id", value=id_, unique=True)
        if result is None:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return result  # type: ignore[return-value]

    @transactional
    def delete_by_uuid(self, uuid: UUID) -> ModelType:
        result = self.repository.delete_by(field="id", value=uuid, unique=True)
        if result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found",
            )
        return result  # type: ignore[return-value]

    @transactional
    def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited")
        result = self.repository.create_or_update_by(
            attributes=attributes,
            update_fields=update_fields,
        )
        if result is None:
            raise NotFoundError("Failed to insert or update")
        return result

    @transactional
    def create_or_update(self, model: ModelType) -> ModelType:
        return self.repository.create_or_update(model=model)

    @transactional
    def create_or_update_many(self, models: Sequence) -> list[ModelType]:
        return self.repository.create_or_update_many(models=models)

    @transactional
    def update_many(self, models: Sequence) -> list[ModelType]:
        return self.repository.update_many(models=models)

    @transactional
    def delete_many(self, models: Sequence) -> list[ModelType]:
        return self.repository.delete_many(models=models)

    def make_pagination_response(
        self,
        data: Sequence,
        skip: int = 0,
        limit: int = 100,
        filter_request: FilterRequest | None = None,
    ) -> PaginationResponse:
        total_count = self.count(filter_request=filter_request).count
        page = skip // limit + 1 if limit > 0 else 1
        page_size = len(data)
        total_pages = (total_count + limit - 1) // limit if limit > 0 else 1
        return PaginationResponse(
            data=list(data),
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_count=total_count,
        )

    @staticmethod
    def extract_attributes_from_schema(
        schema: BaseModel,
        excludes: set[str | int] | None = None,
    ) -> dict[str, Any]:
        return schema.model_dump(exclude=excludes, exclude_unset=True)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
