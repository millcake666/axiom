# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107, S110
# mypy: disable-error-code="name-defined,valid-type,type-arg,attr-defined,assignment,arg-type,misc,call-overload,call-arg,return-value,unreachable"
"""axiom.oltp.beanie.base.repository.sync — Sync MongoDB repository using PyMongo."""

import re
from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Any

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from axiom.core.filter.expr import FilterNode, FilterParam, FilterRequest
from axiom.core.filter.type import FilterType, QueryOperator, SortTypeEnum
from axiom.core.logger.core import get_logger
from axiom.oltp.beanie.abs.repository.sync import SyncBaseRepository
from axiom.oltp.beanie.base.document import SyncDocument

logger = get_logger(__name__)


@dataclass
class _SyncQuery:
    """Internal query state accumulating filter, sort, and pagination for PyMongo.

    Instances are built incrementally by the ``SyncMongoRepository`` helper
    methods and then executed against the collection in ``_all``, ``_one_or_none``,
    and ``_count``.
    """

    condition: dict[str, Any] = dc_field(default_factory=dict)
    offset: int = 0
    size: int = 0
    ordering: list[tuple[str, int]] = dc_field(default_factory=list)


class SyncMongoRepository[
    ModelType: SyncDocument,
    SessionType,
    QueryType,
](SyncBaseRepository):
    """Sync MongoDB repository using a PyMongo collection.

    Implements ``SyncBaseRepository`` for ``SyncDocument`` models. All
    operations target the ``collection`` attribute injected at construction.
    """

    def _query(self) -> _SyncQuery:
        """Return a fresh, empty ``_SyncQuery`` for the current operation.

        Returns:
            A ``_SyncQuery`` with no filter, sort, or pagination applied.
        """
        return _SyncQuery()

    def _maybe_join(self, query: _SyncQuery, field: str) -> _SyncQuery:
        """No-op join hook — PyMongo does not support ODM-level link fetching.

        Args:
            query: The current query state.
            field: The field path (unused).

        Returns:
            The query state unchanged.
        """
        return query

    def _get_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
    ) -> dict[str, Any]:
        """Build a MongoDB filter expression for a single field condition.

        Translates ``id`` to ``_id`` and converts string values to
        ``ObjectId`` when possible. All ``QueryOperator`` variants are
        mapped to their MongoDB ``$``-operator equivalents.

        Args:
            field: Document field name; ``"id"`` is remapped to ``"_id"``.
            value: Value to compare against.
            operator: Comparison operator; defaults to ``EQUALS``.

        Returns:
            A MongoDB filter dict, e.g. ``{"status": {"$ne": "active"}}``.
        """
        if field == "id":
            if isinstance(value, str):
                try:
                    value = ObjectId(value)
                except (ValueError, TypeError):
                    pass
            field = "_id"
        _MONGO_EXPR = {
            QueryOperator.NOT_EQUAL: lambda v: {"$ne": v},
            QueryOperator.IN: lambda v: {"$in": list(v)},
            QueryOperator.NOT_IN: lambda v: {"$nin": list(v)},
            QueryOperator.GREATER: lambda v: {"$gt": v},
            QueryOperator.EQUALS_OR_GREATER: lambda v: {"$gte": v},
            QueryOperator.LESS: lambda v: {"$lt": v},
            QueryOperator.EQUALS_OR_LESS: lambda v: {"$lte": v},
            QueryOperator.STARTS_WITH: lambda v: {"$regex": f"^{re.escape(str(v))}"},
            QueryOperator.NOT_START_WITH: lambda v: {"$not": {"$regex": f"^{re.escape(str(v))}"}},
            QueryOperator.ENDS_WITH: lambda v: {"$regex": f"{re.escape(str(v))}$"},
            QueryOperator.NOT_END_WITH: lambda v: {"$not": {"$regex": f"{re.escape(str(v))}$"}},
            QueryOperator.CONTAINS: lambda v: {"$regex": re.escape(str(v))},
            QueryOperator.NOT_CONTAIN: lambda v: {"$not": {"$regex": re.escape(str(v))}},
        }
        expr_fn = _MONGO_EXPR.get(operator)
        return {field: expr_fn(value) if expr_fn is not None else value}  # type: ignore[no-untyped-call]

    def _build_filter_node(self, node: FilterNode) -> dict[str, Any]:
        """Recursively translate a ``FilterNode`` to a MongoDB condition dict.

        Args:
            node: A ``FilterParam`` leaf or a ``FilterGroup`` composite.

        Returns:
            A MongoDB filter dict using ``$and`` / ``$or`` for groups.
        """
        if isinstance(node, FilterParam):
            return self._get_by(node.field, node.value, node.operator)
        conditions = [self._build_filter_node(item) for item in node.items]
        if node.type == FilterType.AND:
            return {"$and": conditions}
        return {"$or": conditions}

    def _filter(self, query: _SyncQuery, filter_request: FilterRequest) -> _SyncQuery:
        """Merge a compiled filter condition into the query state.

        Multiple calls are combined with ``$and``.

        Args:
            query: The current query state.
            filter_request: Composite filter to translate and apply.

        Returns:
            The updated query state.
        """
        condition = self._build_filter_node(filter_request.chain)
        if query.condition:
            query.condition = {"$and": [query.condition, condition]}
        else:
            query.condition = condition
        return query

    def _paginate(self, query: _SyncQuery, skip: int = 0, limit: int = 100) -> _SyncQuery:
        """Set skip and limit on the query state.

        Args:
            query: The current query state.
            skip: Number of documents to skip.
            limit: Maximum documents to return.

        Returns:
            The updated query state.
        """
        query.offset = skip
        query.size = limit
        return query

    def _sort_by(
        self,
        query: _SyncQuery,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> _SyncQuery:
        """Set an ordering clause on the query state.

        Falls back to ``updated_at`` when ``sort_by`` is ``None`` and the
        model exposes that field.

        Args:
            query: The current query state.
            sort_by: Field name to sort by.
            sort_type: Sort direction; defaults to ascending.

        Returns:
            The updated query state, or unchanged if no sort field is available.
        """
        if sort_by is None:
            fields = getattr(self.model_class, "model_fields", {})
            if "updated_at" in fields:
                sort_by = "updated_at"
            else:
                return query
        direction = ASCENDING if sort_type == SortTypeEnum.asc else DESCENDING
        query.ordering = [(sort_by, direction)]
        return query

    def _all(self, query: _SyncQuery) -> list[ModelType]:
        """Execute the query against the collection and return all matches.

        Args:
            query: The finalised query state.

        Returns:
            List of model instances built from the matching documents.
        """
        cursor = self.collection.find(query.condition)
        if query.ordering:
            cursor = cursor.sort(query.ordering)
        if query.offset:
            cursor = cursor.skip(query.offset)
        if query.size > 0:
            cursor = cursor.limit(query.size)
        return [self._doc_to_model(doc) for doc in cursor]

    def _one_or_none(self, query: _SyncQuery) -> ModelType | None:
        """Fetch at most one document matching the query state.

        Args:
            query: The finalised query state.

        Returns:
            A model instance, or ``None`` if no document matches.
        """
        doc = self.collection.find_one(query.condition)
        if doc is None:
            return None
        return self._doc_to_model(doc)

    def _count(self, query: _SyncQuery) -> int:
        """Count documents matching the query state.

        Args:
            query: The finalised query state.

        Returns:
            The number of matching documents.
        """
        return self.collection.count_documents(query.condition)

    def _doc_to_model(self, doc: dict[str, Any]) -> ModelType:
        """Convert a raw MongoDB document dict to a model instance.

        Renames ``_id`` to ``id`` (as a string) before constructing the model.

        Args:
            doc: Raw document dict returned by PyMongo.

        Returns:
            A ``ModelType`` instance populated from the document.
        """
        doc = dict(doc)
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return self.model_class(**doc)

    def create(self, attributes: dict[str, Any]) -> ModelType:
        """Persist a new document and return the inserted model.

        Args:
            attributes: Mapping of field names to values.

        Returns:
            The newly inserted model instance with ``id`` populated.
        """
        doc = dict(attributes)
        result = self.collection.insert_one(doc)
        return self.model_class(**{**attributes, "id": str(result.inserted_id)})

    def create_many(self, attributes_list: list[dict[str, Any]]) -> list[ModelType]:
        """Persist multiple documents in a single bulk insert.

        Args:
            attributes_list: List of attribute mappings, one per document.

        Returns:
            List of newly inserted model instances; empty if input is empty.
        """
        if not attributes_list:
            return []
        docs = [dict(attrs) for attrs in attributes_list]
        result = self.collection.insert_many(docs)
        return [
            self.model_class(**{**attrs, "id": str(oid)})
            for attrs, oid in zip(attributes_list, result.inserted_ids, strict=False)
        ]

    def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Apply attribute changes to an existing document.

        Uses ``$set`` to update only the provided fields in MongoDB.

        Args:
            model: The model instance whose document will be updated.
            attributes: Field names and their new values.

        Returns:
            A new model instance reflecting the applied changes.
        """
        if model.id:
            self.collection.update_one(
                {"_id": ObjectId(model.id)},
                {"$set": attributes},
            )
        updated = model.model_dump()
        updated.update(attributes)
        return self.model_class(**updated)

    def delete(self, model: ModelType) -> ModelType:
        """Remove a document from the collection.

        Args:
            model: The model instance whose document will be deleted.

        Returns:
            The deleted model instance.
        """
        if model.id:
            self.collection.delete_one({"_id": ObjectId(model.id)})
        return model

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
        filter_request = FilterRequest(
            chain=FilterParam(field=field, value=value, operator=operator),
        )
        return self._update_models(
            filter_request=filter_request,
            attributes=attributes,
            unique=unique,
        )

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
        return self._update_models(
            filter_request=filter_request,
            attributes=attributes,
            unique=unique,
        )

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
        filter_request = FilterRequest(
            chain=FilterParam(field=field, value=value, operator=operator),
        )
        return self._delete_models(filter_request=filter_request, unique=unique)

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
        return self._delete_models(filter_request=filter_request, unique=unique)

    def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Insert a new document or update an existing one.

        Searches for an existing document using the non-update fields; creates
        it if absent, or applies ``update_fields`` changes if found.

        Args:
            attributes: Full set of field values for the document.
            update_fields: Fields to update on an existing document. If ``None``,
                all fields are used for both matching and updating.

        Returns:
            The created or updated model instance.
        """
        if update_fields:
            search_fields = {k: v for k, v in attributes.items() if k not in update_fields}
        else:
            search_fields = dict(attributes)
        existing_doc = self.collection.find_one(search_fields) if search_fields else None
        existing = self._doc_to_model(existing_doc) if existing_doc is not None else None
        if existing is not None:
            update_attrs = {
                k: v for k, v in attributes.items() if update_fields is None or k in update_fields
            }
            return self.update(existing, update_attrs)
        return self.create(attributes)

    def _update_models(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        query = self._query()
        query = self._filter(query, filter_request)
        if unique:
            model = self._one_or_none(query)
            if model is None:
                return None
            return self.update(model, attributes)
        models = self._all(query)
        return [self.update(m, attributes) for m in models]

    def _delete_models(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        query = self._query()
        query = self._filter(query, filter_request)
        if unique:
            model = self._one_or_none(query)
            if model is None:
                return None
            return self.delete(model)
        models = self._all(query)
        return [self.delete(m) for m in models]
