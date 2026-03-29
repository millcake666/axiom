# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107, S110
# mypy: disable-error-code="name-defined,valid-type,type-arg,attr-defined,assignment,arg-type,misc,call-overload,call-arg,return-value,unreachable"
"""axiom.oltp.beanie.base.repository.async_ — Async Beanie repository."""

import re
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClientSession as ClientSession
from pymongo import ASCENDING, DESCENDING

from axiom.core.filter import (
    FilterNode,
    FilterParam,
    FilterRequest,
    FilterType,
    QueryOperator,
    SortTypeEnum,
)
from axiom.core.logger import get_logger
from axiom.oltp.beanie.abs.repository.async_ import AsyncBaseRepository
from beanie import Document

logger = get_logger(__name__)


class AsyncBeanieRepository[
    ModelType: Document,
    SessionType: (ClientSession, None),
    QueryType,
](AsyncBaseRepository):
    """Async Beanie repository for MongoDB documents.

    Implements ``AsyncBaseRepository`` using the Beanie ODM. All write
    operations use the ``session`` attribute for optional transaction support.
    """

    model_class: type[ModelType]
    session: SessionType

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """Persist a new document with the given field values.

        Args:
            attributes: Mapping of field names to values.

        Returns:
            The newly inserted document instance.
        """
        instance = self.model_class(**attributes)
        await instance.insert(session=self.session)
        return instance

    async def create_many(
        self,
        attributes_list: list[dict[str, Any]],
    ) -> list[ModelType]:
        """Persist multiple documents in a single bulk insert.

        Args:
            attributes_list: List of attribute mappings, one per document.

        Returns:
            List of newly inserted document instances; empty if input is empty.
        """
        if not attributes_list:
            return []
        instances = [self.model_class(**attrs) for attrs in attributes_list]
        await self.model_class.insert_many(instances, session=self.session)
        return instances

    async def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Apply attribute changes to an existing document and save it.

        Args:
            model: The document instance to update.
            attributes: Field names and their new values.

        Returns:
            The updated document instance.
        """
        for field, value in attributes.items():
            setattr(model, field, value)
        await model.save(session=self.session)
        return model

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
        """
        filter_request = FilterRequest(
            chain=FilterParam(field=field, value=value, operator=operator),
        )
        return await self._update_models(
            filter_request=filter_request,
            attributes=attributes,
            unique=unique,
        )

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
        """
        return await self._update_models(
            filter_request=filter_request,
            attributes=attributes,
            unique=unique,
        )

    async def delete(self, model: ModelType) -> ModelType:
        """Remove a document from the database.

        Args:
            model: The document instance to delete.

        Returns:
            The deleted document instance.
        """
        await model.delete(session=self.session)
        return model

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
        """
        filter_request = FilterRequest(
            chain=FilterParam(field=field, value=value, operator=operator),
        )
        return await self._delete_models(
            filter_request=filter_request,
            unique=unique,
        )

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
        """
        return await self._delete_models(
            filter_request=filter_request,
            unique=unique,
        )

    async def create_or_update_by(
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
            The created or updated document instance.
        """
        if update_fields:
            search_fields = {k: v for k, v in attributes.items() if k not in update_fields}
        else:
            search_fields = attributes

        if search_fields:
            filter_dict = self._build_filter_dict_from_attrs(search_fields)
            existing = await self.model_class.find_one(filter_dict, session=self.session)
        else:
            existing = None

        if existing is not None:
            update_attrs = {
                k: v for k, v in attributes.items() if update_fields is None or k in update_fields
            }
            return await self.update(existing, update_attrs)
        return await self.create(attributes)

    def _query(self) -> Any:
        """Return a base Beanie find query for the managed model.

        Returns:
            An unfiltered ``FindMany`` query with the current session.
        """
        return self.model_class.find(session=self.session)

    def _maybe_join(self, query: Any, field: str) -> Any:
        """Enable link fetching when the field path contains a dot.

        Args:
            query: The current Beanie find query.
            field: The field path; dot notation indicates a linked document.

        Returns:
            The query with ``fetch_links=True`` if the path is nested,
            otherwise the unchanged query.
        """
        if "." in field:
            return query.find(fetch_links=True)
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
            from bson import ObjectId

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

    def _filter(self, query: Any, filter_request: FilterRequest) -> Any:
        """Append a filter condition derived from ``filter_request`` to the query.

        Args:
            query: The current Beanie find query.
            filter_request: Composite filter to translate and apply.

        Returns:
            The query extended with the compiled filter condition.
        """
        condition = self._build_filter_node(filter_request.chain)
        return query.find(condition)

    def _paginate(self, query: Any, skip: int = 0, limit: int = 100) -> Any:
        """Apply skip/limit pagination to a Beanie find query.

        Args:
            query: The current Beanie find query.
            skip: Number of documents to skip.
            limit: Maximum documents to return; non-positive values disable limiting.

        Returns:
            The paginated query object.
        """
        if limit > 0:
            query = query.skip(skip).limit(limit)
        return query

    def _sort_by(
        self,
        query: Any,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> Any:
        """Apply an ordering clause to a Beanie find query.

        Falls back to ``updated_at`` when ``sort_by`` is ``None`` and the
        model exposes that field.

        Args:
            query: The current Beanie find query.
            sort_by: Field name to sort by.
            sort_type: Sort direction; defaults to ascending.

        Returns:
            The sorted query object, or the unchanged query if no sort field.
        """
        if sort_by is None:
            if hasattr(self.model_class, "updated_at"):
                sort_by = "updated_at"
            else:
                return query
        direction = ASCENDING if sort_type == SortTypeEnum.asc else DESCENDING
        return query.sort([(sort_by, direction)])

    async def _all(self, query: Any) -> list[ModelType]:
        """Execute the query and return all matching documents.

        Args:
            query: The finalised Beanie find query.

        Returns:
            List of matching document instances.
        """
        return await query.to_list()

    async def _one_or_none(self, query: Any) -> ModelType | None:
        """Execute the query and return at most one document.

        Args:
            query: The finalised Beanie find query.

        Returns:
            The first matching document, or ``None`` if no match.
        """
        return await query.first_or_none()

    async def _count(self, query: Any) -> int:
        """Count documents matching the query.

        Args:
            query: The finalised Beanie find query.

        Returns:
            The number of matching documents.
        """
        return await query.count()

    async def _update_models(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        query = self._query()
        query = self._filter(query, filter_request)
        if unique:
            model = await self._one_or_none(query)
            if model is None:
                return None
            return await self.update(model, attributes)
        models = await self._all(query)
        result = []
        for model in models:
            updated = await self.update(model, attributes)
            result.append(updated)
        return result

    async def _delete_models(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        query = self._query()
        query = self._filter(query, filter_request)
        if unique:
            model = await self._one_or_none(query)
            if model is None:
                return None
            return await self.delete(model)
        models = await self._all(query)
        result = []
        for model in models:
            deleted = await self.delete(model)
            result.append(deleted)
        return result

    def _build_filter_dict_from_attrs(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Convert an attribute dict to a MongoDB filter dict.

        Args:
            attrs: Field-to-value mapping used as equality filter conditions.

        Returns:
            A MongoDB filter dict (currently the input dict unchanged).
        """
        return attrs

    def _get_model_field_type(self, _model: type[ModelType], _field: str) -> type:
        """Get the Python type of a field, supporting nested paths.

        Args:
            _model: The model class (unused, uses self.model_class).
            _field: Dot-notation field path (e.g., "user.profile.name").

        Returns:
            The Python type of the field.
        """
        from axiom.oltp.beanie.base.utils import resolve_nested_field_type

        return resolve_nested_field_type(self.model_class, _field)

    def _resolve_field_relation(self, field: str) -> tuple[type[ModelType], str]:
        """Resolve model and field name from field path — unlimited depth.

        Args:
            field: Dot-notation field path (e.g., "user.profile.name").

        Returns:
            Tuple of (final_model_class, field_name).

        Raises:
            ValidationError: If the field path is invalid.
        """
        from axiom.core.exceptions import ValidationError
        from axiom.oltp.beanie.base.utils import get_field_type, get_linked_document_type

        if "." not in field:
            return self.model_class, field

        parts = field.split(".")
        current_model: type[ModelType] = self.model_class

        for rel_name in parts[:-1]:
            try:
                field_type = get_field_type(current_model, rel_name)
            except ValueError as exc:
                raise ValidationError(str(exc)) from exc

            # Handle Link fields - get the linked document type
            linked_doc = get_linked_document_type(field_type)
            if linked_doc is not None:
                current_model = linked_doc
            elif isinstance(field_type, type) and issubclass(field_type, Document):
                current_model = field_type
            else:
                raise ValidationError(
                    f"Cannot traverse into field '{rel_name}' of {current_model.__name__}",
                )

        return current_model, parts[-1]
