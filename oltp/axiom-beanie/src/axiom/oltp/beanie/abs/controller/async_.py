# mypy: disable-error-code="type-arg,valid-type,name-defined,arg-type,attr-defined"
"""axiom.oltp.beanie.abs.controller.async_ — Abstract async controller for Beanie."""

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from pydantic import BaseModel

from axiom.core.exceptions import NotFoundError, UnprocessableError
from axiom.core.filter import FilterParam, FilterRequest, QueryOperator, SortTypeEnum
from axiom.core.schema import CountResponse, PaginationResponse
from axiom.oltp.beanie.abs.repository.async_ import AsyncBaseRepository


class AsyncBaseController[ModelType](ABC):
    """Abstract base class for async Beanie data controllers.

    Provides standard CRUD, filter, and pagination operations delegating
    persistence to an ``AsyncBaseRepository``. Subclasses must implement
    ``processing_transaction`` to define transaction handling strategy.
    """

    def __init__(
        self,
        model: type[ModelType],
        repository: AsyncBaseRepository,
        exclude_fields: list[str],
    ) -> None:
        """Initialise the controller.

        Args:
            model: The document model class managed by this controller.
            repository: The async repository used for persistence.
            exclude_fields: Field names that are forbidden during update operations.
        """
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
        """Execute a function within a transaction context.

        Subclasses must implement session/transaction lifecycle management.

        Args:
            function: The callable to execute inside the transaction.
            *args: Positional arguments forwarded to ``function``.
            **kwargs: Keyword arguments forwarded to ``function``.

        Returns:
            The return value of ``function``.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError

    def transactional(function: Any) -> Any:
        """Decorator that wraps a method call in ``processing_transaction``.

        Args:
            function: The async method to wrap.

        Returns:
            An async wrapper that delegates to ``processing_transaction``.
        """

        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
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
        """Retrieve documents matching a single field condition.

        Args:
            field: Document field name to filter on.
            value: Value to compare against.
            operator: Comparison operator; defaults to ``EQUALS``.
            skip: Number of documents to skip (pagination offset).
            limit: Maximum number of documents to return.
            sort_by: Field name to sort results by.
            sort_type: Sort direction; defaults to ascending.
            unique: If ``True``, return a single document instead of a page.

        Returns:
            A single document when ``unique=True``, otherwise a ``PaginationResponse``.

        Raises:
            NotFoundError: If no matching document is found.
        """
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
            return db_obj
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
        """Retrieve documents using a structured filter request.

        Args:
            filter_request: Composite filter to apply; ``None`` matches all documents.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            sort_by: Field name to sort results by.
            sort_type: Sort direction; defaults to ascending.
            unique: If ``True``, return a single document instead of a page.

        Returns:
            A single document when ``unique=True``, otherwise a ``PaginationResponse``.

        Raises:
            NotFoundError: If ``unique=True`` and no matching document is found.
        """
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
                return models
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
        """Count documents matching an optional filter.

        Args:
            filter_request: Filter to apply; ``None`` counts all documents.

        Returns:
            A ``CountResponse`` containing the total document count.
        """
        return CountResponse(
            count=await self.repository.count(filter_request=filter_request),
        )

    async def get_by_id(self, id_: str) -> ModelType:
        """Retrieve a single document by its primary key.

        Args:
            id_: The document identifier.

        Returns:
            The matching document instance.

        Raises:
            NotFoundError: If no document with the given id exists.
        """
        db_obj = await self.repository.get_by(field="id", value=id_, unique=True)
        if not db_obj:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return db_obj

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> PaginationResponse:
        """Retrieve all documents with pagination and optional sorting.

        Args:
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            sort_by: Field name to sort results by.
            sort_type: Sort direction; defaults to ascending.

        Returns:
            A ``PaginationResponse`` containing the requested page of documents.
        """
        response = await self.repository.get_all(
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_type=sort_type,
        )
        return await self.make_pagination_response(
            data=response,
            skip=skip,
            limit=limit,
        )

    @transactional
    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """Create a new document from the given attributes.

        Args:
            attributes: Mapping of field names to values for the new document.

        Returns:
            The newly created document instance.
        """
        return await self.repository.create(attributes=attributes)

    @transactional
    async def create_many(
        self,
        attributes_list: list[dict[str, Any]],
    ) -> list[ModelType]:
        """Create multiple documents in a single operation.

        Args:
            attributes_list: List of attribute mappings, one per document.

        Returns:
            List of newly created document instances.
        """
        return await self.repository.create_many(attributes_list)

    @transactional
    async def delete(self, model: ModelType) -> ModelType:
        """Delete a document from the database.

        Args:
            model: The document instance to delete.

        Returns:
            The deleted document instance.
        """
        return await self.repository.delete(model=model)

    @transactional
    async def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Update a document with the given attributes.

        Args:
            model: The document instance to update.
            attributes: Field names and their new values.

        Returns:
            The updated document instance.

        Raises:
            UnprocessableError: If any attribute key is in ``exclude_fields``.
        """
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
        """Update documents matched by a filter request.

        Args:
            filter_request: Filter identifying documents to update.
            attributes: Field names and their new values.
            unique: If ``True``, update only the first matched document.

        Returns:
            Updated document when ``unique=True``, list of updated documents otherwise,
            or ``None`` if ``unique=True`` and no match was found.

        Raises:
            UnprocessableError: If any attribute key is in ``exclude_fields``.
            NotFoundError: If ``unique=True`` and no matching document is found.
        """
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
        """Delete documents matched by a filter request.

        Args:
            filter_request: Filter identifying documents to delete.
            unique: If ``True``, delete only the first matched document.

        Returns:
            Deleted document when ``unique=True``, list of deleted documents otherwise,
            or ``None`` if ``unique=True`` and no match was found.

        Raises:
            NotFoundError: If ``unique=True`` and no matching document is found.
        """
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
        """Update documents matching a single field condition.

        Args:
            field: Document field name to filter on.
            value: Value to compare against.
            attributes: Field names and their new values.
            operator: Comparison operator; defaults to ``EQUALS``.
            unique: If ``True``, update only the first matched document.

        Returns:
            Updated document when ``unique=True``, list of updated documents otherwise,
            or ``None`` if ``unique=True`` and no match was found.

        Raises:
            UnprocessableError: If any attribute key is in ``exclude_fields``.
            NotFoundError: If ``unique=True`` and no matching document is found.
        """
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
        """Delete documents matching a single field condition.

        Args:
            field: Document field name to filter on.
            value: Value to compare against.
            operator: Comparison operator; defaults to ``EQUALS``.
            unique: If ``True``, delete only the first matched document.

        Returns:
            Deleted document when ``unique=True``, list of deleted documents otherwise,
            or ``None`` if ``unique=True`` and no match was found.

        Raises:
            NotFoundError: If ``unique=True`` and no matching document is found.
        """
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
    async def update_by_id(self, id_: str, attributes: dict[str, Any]) -> ModelType:
        """Update a document by its primary key.

        Args:
            id_: The document identifier.
            attributes: Field names and their new values.

        Returns:
            The updated document instance.

        Raises:
            UnprocessableError: If any attribute key is in ``exclude_fields``.
            NotFoundError: If no document with the given id exists.
        """
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = await self.repository.update_by(
            field="id",
            value=id_,
            attributes=attributes,
            unique=True,
        )
        if result is None:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return result

    @transactional
    async def update_by_uuid(self, uuid: str, attributes: dict[str, Any]) -> ModelType:
        """Update a document by its UUID field.

        Args:
            uuid: The document UUID.
            attributes: Field names and their new values.

        Returns:
            The updated document instance.

        Raises:
            UnprocessableError: If any attribute key is in ``exclude_fields``.
            NotFoundError: If no document with the given UUID exists.
        """
        for f in attributes:
            if f in self.exclude_fields:
                raise UnprocessableError(f"Field {f} is prohibited for updating")
        result = await self.repository.update_by(
            field="id",
            value=uuid,
            attributes=attributes,
            unique=True,
        )
        if result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found",
            )
        return result

    @transactional
    async def delete_by_id(self, id_: str) -> ModelType:
        """Delete a document by its primary key.

        Args:
            id_: The document identifier.

        Returns:
            The deleted document instance.

        Raises:
            NotFoundError: If no document with the given id exists.
        """
        result = await self.repository.delete_by(field="id", value=id_, unique=True)
        if result is None:
            raise NotFoundError(f"{self.model_class.__name__} with id: {id_} not found")
        return result

    @transactional
    async def delete_by_uuid(self, uuid: str) -> ModelType:
        """Delete a document by its UUID field.

        Args:
            uuid: The document UUID.

        Returns:
            The deleted document instance.

        Raises:
            NotFoundError: If no document with the given UUID exists.
        """
        result = await self.repository.delete_by(field="id", value=uuid, unique=True)
        if result is None:
            raise NotFoundError(
                f"{self.model_class.__name__} with uuid: {uuid} not found",
            )
        return result

    @transactional
    async def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Insert a new document or update an existing one.

        Looks up a document using the non-update fields; creates if absent,
        updates ``update_fields`` if found.

        Args:
            attributes: Full set of field values for the document.
            update_fields: Fields to update on an existing document. If ``None``,
                all fields are considered for matching and updating.

        Returns:
            The created or updated document instance.

        Raises:
            UnprocessableError: If any attribute key is in ``exclude_fields``.
            NotFoundError: If the upsert operation returns no result.
        """
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
        """Build a ``PaginationResponse`` from a data page.

        Args:
            data: The current page of document instances.
            skip: Number of documents skipped (used to compute page number).
            limit: Page size limit (used to compute total pages).
            filter_request: Filter applied to count total matching documents.

        Returns:
            A populated ``PaginationResponse``.
        """
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
        """Dump a Pydantic schema to a dict, omitting unset and excluded fields.

        Args:
            schema: The Pydantic model instance to dump.
            excludes: Field names or indices to exclude from the output.

        Returns:
            Dictionary of set field values, with excluded fields removed.
        """
        return schema.model_dump(exclude=excludes, exclude_unset=True)

    def __repr__(self) -> str:  # noqa: D105
        return f"<{self.__class__.__name__}>"
