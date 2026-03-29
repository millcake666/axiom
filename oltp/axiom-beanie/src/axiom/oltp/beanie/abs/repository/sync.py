# mypy: disable-error-code="name-defined,valid-type,assignment"
"""axiom.oltp.beanie.abs.repository.sync — Abstract sync repository for MongoDB."""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from axiom.core.filter import FilterParam, FilterRequest, QueryOperator, SortTypeEnum


class SyncBaseRepository[ModelType, SessionType, QueryType](ABC):
    """Abstract base class for sync MongoDB data repositories.

    Provides the full CRUD and query contract that concrete repositories must
    implement. Non-abstract methods compose the abstract primitives to deliver
    standard ``get_all``, ``get_by``, ``get_by_filters``, and ``count`` behaviour.
    """

    def __init__(
        self,
        model: type[ModelType],
        collection: Any,
        db_session: SessionType = None,
    ) -> None:
        """Initialise the repository.

        Args:
            model: The document model class managed by this repository.
            collection: The PyMongo collection object to operate on.
            db_session: Optional database session for transactional operations.
        """
        self.model_class = model
        self.collection = collection
        self.session = db_session

    @abstractmethod
    def create(self, attributes: dict[str, Any]) -> ModelType:
        """Persist a new document with the given field values.

        Args:
            attributes: Mapping of field names to values.

        Returns:
            The newly created document instance.
        """
        raise NotImplementedError

    @abstractmethod
    def create_many(self, attributes_list: list[dict[str, Any]]) -> list[ModelType]:
        """Persist multiple documents in a single operation.

        Args:
            attributes_list: List of attribute mappings, one per document.

        Returns:
            List of newly created document instances.
        """
        raise NotImplementedError

    @abstractmethod
    def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Apply attribute changes to an existing document.

        Args:
            model: The document instance to update.
            attributes: Field names and their new values.

        Returns:
            The updated document instance.
        """
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
        """
        raise NotImplementedError

    @abstractmethod
    def update_by_filters(
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
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, model: ModelType) -> ModelType:
        """Remove a document from the database.

        Args:
            model: The document instance to delete.

        Returns:
            The deleted document instance.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by(
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
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_filters(
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
        """
        raise NotImplementedError

    @abstractmethod
    def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Insert a new document or update an existing one.

        Args:
            attributes: Full set of field values for the document.
            update_fields: Fields to update on an existing document. If ``None``,
                all fields are used for both matching and updating.

        Returns:
            The created or updated document instance.
        """
        raise NotImplementedError

    @abstractmethod
    def _query(self) -> QueryType:
        """Return a base query object for the managed model.

        Returns:
            An initial, unfiltered query for ``ModelType``.
        """
        raise NotImplementedError

    @abstractmethod
    def _maybe_join(self, query: QueryType, field: str) -> QueryType:
        """Optionally extend the query to handle relational field access.

        Args:
            query: The current query object.
            field: The field path that may require special handling.

        Returns:
            The query, potentially extended.
        """
        raise NotImplementedError

    @abstractmethod
    def _filter(self, query: QueryType, filter_request: FilterRequest) -> QueryType:
        """Apply a ``FilterRequest`` to the query.

        Args:
            query: The current query object.
            filter_request: Composite filter to apply.

        Returns:
            The filtered query object.
        """
        raise NotImplementedError

    @abstractmethod
    def _paginate(self, query: QueryType, skip: int = 0, limit: int = 100) -> QueryType:
        """Apply skip and limit pagination to the query.

        Args:
            query: The current query object.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            The paginated query object.
        """
        raise NotImplementedError

    @abstractmethod
    def _sort_by(
        self,
        query: QueryType,
        sort_by: str | None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> QueryType:
        """Apply an ordering clause to the query.

        Args:
            query: The current query object.
            sort_by: Field name to sort by; ``None`` applies a default.
            sort_type: Sort direction; defaults to ascending.

        Returns:
            The sorted query object.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
    ) -> Any:
        """Build a filter expression for a single field condition.

        Args:
            field: Document field name.
            value: Value to compare against.
            operator: Comparison operator; defaults to ``EQUALS``.

        Returns:
            A backend-specific filter expression.
        """
        raise NotImplementedError

    @abstractmethod
    def _all(self, query: QueryType) -> list[ModelType]:
        """Execute the query and return all matching documents.

        Args:
            query: The finalised query object.

        Returns:
            List of matching document instances.
        """
        raise NotImplementedError

    @abstractmethod
    def _one_or_none(self, query: QueryType) -> ModelType | None:
        """Execute the query and return at most one document.

        Args:
            query: The finalised query object.

        Returns:
            A single document instance, or ``None`` if no match.
        """
        raise NotImplementedError

    @abstractmethod
    def _count(self, query: QueryType) -> int:
        """Count documents matching the query.

        Args:
            query: The finalised query object.

        Returns:
            The number of matching documents.
        """
        raise NotImplementedError

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> list[ModelType]:
        """Return all documents with optional sorting and pagination.

        Args:
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            sort_by: Field name to sort results by.
            sort_type: Sort direction; defaults to ascending.

        Returns:
            List of document instances for the requested page.
        """
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
        """Fetch documents matching a single field condition.

        Args:
            field: Document field name to filter on.
            value: Value to compare against.
            operator: Comparison operator; defaults to ``EQUALS``.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            sort_by: Field name to sort results by.
            sort_type: Sort direction; defaults to ascending.
            unique: If ``True``, return at most one document.

        Returns:
            A single document or ``None`` when ``unique=True``,
            otherwise a list of matching documents.
        """
        query = self._query()
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
        """Fetch documents using a structured filter request.

        Args:
            filter_request: Composite filter to apply; ``None`` matches all.
            skip: Number of documents to skip.
            limit: Maximum number of documents to return.
            sort_by: Field name to sort results by.
            sort_type: Sort direction; defaults to ascending.
            unique: If ``True``, return at most one document.

        Returns:
            A single document or ``None`` when ``unique=True``,
            otherwise a list of matching documents.
        """
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
        """Count documents matching an optional filter.

        Args:
            filter_request: Filter to apply; ``None`` counts all documents.

        Returns:
            The total number of matching documents.
        """
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
            return {key: self._get_deep_unique_from_dict(value) for key, value in columns.items()}
        if isinstance(columns, list):
            return self._aggregate_unique_list(columns)
        return columns  # type: ignore[unreachable]

    def _aggregate_unique_list(self, columns: list[Any]) -> list[Any]:
        if all(isinstance(item, dict) for item in columns):
            aggregated: dict[str, list[Any]] = defaultdict(list)
            for item in columns:
                for k, v in item.items():
                    processed_v = self._get_deep_unique_from_dict(v)
                    if processed_v not in aggregated[k]:
                        aggregated[k].append(processed_v)
            return self._get_deep_unique_from_dict(aggregated)  # type: ignore[return-value]
        processed_list: list[Any] = []
        for item in columns:
            processed_item = self._get_deep_unique_from_dict(item)
            if processed_item not in processed_list:
                processed_list.append(processed_item)
        return processed_list
