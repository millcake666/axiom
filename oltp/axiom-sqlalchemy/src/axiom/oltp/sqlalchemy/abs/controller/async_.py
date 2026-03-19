# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="type-arg,valid-type,name-defined,arg-type,attr-defined"
"""axiom.oltp.sqlalchemy.abs.controller.async_ — Abstract async controller."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any
from uuid import UUID

from axiom.core.exceptions import NotFoundError, UnprocessableError
from axiom.oltp.sqlalchemy.abs.repository.async_ import AsyncBaseRepository
from axiom.oltp.sqlalchemy.base.filter.schema import FilterParam, FilterRequest
from axiom.oltp.sqlalchemy.base.filter.type import QueryOperator, SortTypeEnum
from axiom.oltp.sqlalchemy.base.schema.response import CountResponse, PaginationResponse
from pydantic import BaseModel


class AsyncBaseController[ModelType](ABC):
    """Abstract base class for async data controllers."""

    def __init__(
        self,
        model: type[ModelType],
        repository: AsyncBaseRepository,
        exclude_fields: list[str],
    ) -> None:
        self.model_class = model
        self.repository = repository
        self.exclude_fields = exclude_fields

    @abstractmethod
    async def processing_transaction(
        self,
        function: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        raise NotImplementedError

    def transactional(function):  # type: ignore[no-untyped-def]
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            return await self.processing_transaction(function, *args, **kwargs)

        return wrapper

    async def get_by(
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
        db_obj = await self.repository.get_by(
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
        return await self.make_pagination_response(
            data=db_obj,
            skip=skip,
            limit=limit,
            filter_request=FilterRequest(
                chain=FilterParam(field=field, value=value, operator=operator),
            ),
        )

    async def get_by_filters(
        self,
        filter_request: FilterRequest | None = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
        unique: bool = False,
    ) -> ModelType | None | PaginationResponse:
        models = await self.repository.get_by_filters(
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
        return await self.make_pagination_response(
            data=models,
            skip=skip,
            limit=limit,
            filter_request=filter_request,
        )

    async def count(self, filter_request: FilterRequest | None = None) -> CountResponse:
        return CountResponse(
            count=await self.repository.count(filter_request=filter_request)
        )

    async def get_by_id(self, id_: int) -> ModelType:
        db_obj = await self.repository.get_by(field="id", value=id_, unique=True)
        if not db_obj:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return db_obj  # type: ignore[return-value]

    async def get_by_uuid(self, uuid: UUID) -> ModelType:
        db_obj = await self.repository.get_by(field="id", value=uuid, unique=True)
        if not db_obj:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found"
            )
        return db_obj  # type: ignore[return-value]

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> PaginationResponse:
        response = await self.repository.get_all(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_type=sort_type,
        )
        return await self.make_pagination_response(
            data=response, skip=skip, limit=limit
        )

    @transactional
    async def create(self, attributes: dict[str, Any]) -> ModelType:
        return await self.repository.create(attributes=attributes)

    @transactional
    async def create_many(
        self, attributes_list: list[dict[str, Any]]
    ) -> list[ModelType]:
        return await self.repository.create_many(attributes_list)

    @transactional
    async def delete(self, model: ModelType) -> ModelType:
        return await self.repository.delete(model=model)

    @transactional
    async def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        for field in attributes:
            if field in self.exclude_fields:
                raise UnprocessableError(f"Field {field} is prohibited for updating")
        return await self.repository.update(model=model, attributes=attributes)

    @transactional
    async def update_by_filters(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        for field in attributes:
            if field in self.exclude_fields:
                raise UnprocessableError(f"Field {field} is prohibited for updating")
        result = await self.repository.update_by_filters(
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
    async def delete_by_filters(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        result = await self.repository.delete_by_filters(
            filter_request=filter_request,
            unique=unique,
        )
        if unique and result is None:
            raise NotFoundError(
                f"Unique {self.model_class.__name__} with provided filters not exist",
            )
        return result

    @transactional
    async def update_by(
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
        result = await self.repository.update_by(
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
    async def delete_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        result = await self.repository.delete_by(
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
    async def update_by_id(self, id_: int, attributes: dict[str, Any]) -> ModelType:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = await self.repository.update_by(
            field="id", value=id_, attributes=attributes, unique=True
        )
        if result is None:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return result  # type: ignore[return-value]

    @transactional
    async def update_by_uuid(self, uuid: UUID, attributes: dict[str, Any]) -> ModelType:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = await self.repository.update_by(
            field="id", value=uuid, attributes=attributes, unique=True
        )
        if result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found"
            )
        return result  # type: ignore[return-value]

    @transactional
    async def delete_by_id(self, id_: int) -> ModelType:
        result = await self.repository.delete_by(field="id", value=id_, unique=True)
        if result is None:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return result  # type: ignore[return-value]

    @transactional
    async def delete_by_uuid(self, uuid: UUID) -> ModelType:
        result = await self.repository.delete_by(field="id", value=uuid, unique=True)
        if result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found"
            )
        return result  # type: ignore[return-value]

    @transactional
    async def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited")
        result = await self.repository.create_or_update_by(
            attributes=attributes,
            update_fields=update_fields,
        )
        if result is None:
            raise NotFoundError("Failed to insert or update")
        return result

    async def make_pagination_response(
        self,
        data: Sequence,
        skip: int = 0,
        limit: int = 100,
        filter_request: FilterRequest | None = None,
    ) -> PaginationResponse:
        total_count = (await self.count(filter_request=filter_request)).count
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
    async def extract_attributes_from_schema(
        schema: BaseModel,
        excludes: set[str | int] | None = None,
    ) -> dict[str, Any]:
        return schema.model_dump(exclude=excludes, exclude_unset=True)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
