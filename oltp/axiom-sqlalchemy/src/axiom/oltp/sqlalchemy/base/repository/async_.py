# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="name-defined,valid-type,type-arg,attr-defined,assignment,arg-type,misc,call-overload,call-arg"
"""axiom.oltp.sqlalchemy.base.repository.async_ — Async SQLAlchemy repository."""

from typing import Any, Literal

from axiom.core.exceptions.http import BadRequestError, NotFoundError, ValidationError
from axiom.core.filter.expr import FilterNode, FilterParam, FilterRequest
from axiom.core.filter.type import FilterType, QueryOperator, SortTypeEnum
from axiom.oltp.sqlalchemy.abs.repository.async_ import AsyncBaseRepository
from axiom.oltp.sqlalchemy.base.declarative import Base
from sqlalchemy import Select, UniqueConstraint, and_, delete, func, inspect, not_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import select


class AsyncSQLAlchemyRepository[
    ModelType: Base,
    SessionType: AsyncSession,
    QueryType: Select,
](AsyncBaseRepository):
    """Async SQLAlchemy repository for any SQLAlchemy-compatible database."""

    model_class: type[ModelType]
    session: SessionType

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        created_model = self.model_class(**attributes)
        self.session.add(created_model)
        return created_model

    async def create_many(
        self,
        attributes_list: list[dict[str, Any]],
    ) -> list[ModelType]:
        if not attributes_list:
            return []
        models = []
        for attributes in attributes_list:
            created_model = self.model_class(**attributes)
            models.append(created_model)
            self.session.add(created_model)
        return models

    async def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        if model is None:
            raise NotFoundError("Entity not found")
        for field, value in attributes.items():
            self._validate_params(field=field, value=value)
            setattr(model, field, value)
        await self.session.flush()
        return model

    async def delete(self, model: ModelType) -> ModelType:
        if model is None:
            raise NotFoundError("Entity not found")
        await self.session.delete(model)
        return model

    async def update_by_filters(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return await self._modify_by_filters(
            filter_request=filter_request,
            attributes=attributes,
            op="update",
            unique=unique,
        )

    async def update_by(
        self,
        field: str,
        value: Any,
        attributes: dict[str, Any],
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return await self._modify_by(
            field=field,
            value=value,
            attributes=attributes,
            operator=operator,
            op="update",
            unique=unique,
        )

    async def delete_by_filters(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return await self._modify_by_filters(
            filter_request=filter_request,
            op="delete",
            unique=unique,
        )

    async def delete_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return await self._modify_by(
            field=field,
            value=value,
            op="delete",
            operator=operator,
            unique=unique,
        )

    async def create_or_update_by(
        self,
        attributes: dict[str, Any],
        update_fields: list[str] | None = None,
    ) -> ModelType:
        """Base implementation: fallback to create if no conflict columns."""
        for f, v in attributes.items():
            self._validate_params(field=f, value=v)
        conflict_cols = self._get_conflict_fields()
        if not conflict_cols:
            return await self.create(attributes)
        # Base fallback: try to find existing, update or create
        return await self.create(attributes)

    def _query(self) -> Select:
        return select(self.model_class)

    def _maybe_join(self, query: Select, field: str) -> Select:
        """Recursively join for unlimited depth dot-notation: a.b.c.d."""
        if "." not in field:
            return query
        parts = field.split(".")
        # parts[:-1] are relation names, parts[-1] is the column
        current_model = self.model_class
        already_joined: set = set()
        for rel_name in parts[:-1]:
            rel_attr = getattr(current_model, rel_name, None)
            if rel_attr is None:
                raise BadRequestError(
                    f"{current_model.__name__} has no relation {rel_name}",
                )
            target_cls = rel_attr.property.mapper.class_
            if target_cls not in already_joined:
                query = query.join(rel_attr)
                already_joined.add(target_cls)
            current_model = target_cls
        return query

    def _get_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
    ) -> ColumnElement[bool]:
        """Resolve column through unlimited depth dot-notation chain."""
        if "." in field:
            parts = field.split(".")
            current_model = self.model_class
            for rel_name in parts[:-1]:
                try:
                    rel_prop = getattr(current_model, rel_name).property
                    current_model = rel_prop.mapper.class_
                except Exception as exc:
                    raise BadRequestError(f"Wrong relation name: {rel_name}") from exc
            col_name = parts[-1]
            column = getattr(current_model, col_name, None)
            if column is None:
                raise BadRequestError(
                    f"{current_model.__name__} has no column {col_name}",
                )
            left = column
        else:
            if not hasattr(self.model_class, field):
                raise BadRequestError(
                    f"{self.model_class.__name__} has no field {field}",
                )
            left = getattr(self.model_class, field)

        match operator:
            case QueryOperator.IN:
                if not isinstance(value, list | tuple | set):
                    raise BadRequestError(
                        f"Value for IN must be a list, tuple or set, got {type(value).__name__}",
                    )
                return left.in_(value)
            case QueryOperator.NOT_IN:
                if not isinstance(value, list | tuple | set):
                    raise BadRequestError(
                        f"Value for NOT_IN must be a list, tuple or set, got {type(value).__name__}",
                    )
                return not_(left.in_(value))
            case QueryOperator.EQUALS:
                return left == value
            case QueryOperator.NOT_EQUAL:
                return left != value
            case QueryOperator.GREATER:
                return left > value
            case QueryOperator.EQUALS_OR_GREATER:
                return left >= value
            case QueryOperator.LESS:
                return left < value
            case QueryOperator.EQUALS_OR_LESS:
                return left <= value
            case QueryOperator.STARTS_WITH:
                if not isinstance(value, str):
                    raise BadRequestError(
                        f"Value for STARTS_WITH must be a string, got {type(value).__name__}",
                    )
                return left.startswith(value)
            case QueryOperator.NOT_START_WITH:
                if not isinstance(value, str):
                    raise BadRequestError(
                        f"Value for NOT_START_WITH must be a string, got {type(value).__name__}",
                    )
                return not_(left.startswith(value))
            case QueryOperator.ENDS_WITH:
                if not isinstance(value, str):
                    raise BadRequestError(
                        f"Value for ENDS_WITH must be a string, got {type(value).__name__}",
                    )
                return left.endswith(value)
            case QueryOperator.NOT_END_WITH:
                if not isinstance(value, str):
                    raise BadRequestError(
                        f"Value for NOT_END_WITH must be a string, got {type(value).__name__}",
                    )
                return not_(left.endswith(value))
            case QueryOperator.CONTAINS:
                if not isinstance(value, str):
                    raise BadRequestError(
                        f"Value for CONTAINS must be a string, got {type(value).__name__}",
                    )
                return left.contains(value)
            case QueryOperator.NOT_CONTAIN:
                if not isinstance(value, str):
                    raise BadRequestError(
                        f"Value for NOT_CONTAIN must be a string, got {type(value).__name__}",
                    )
                return not_(left.contains(value))
            case _:
                raise BadRequestError(f"Operator {operator} not supported")

    def _filter(self, query: Select, filter_request: FilterRequest) -> Select:
        condition = self._build_filter_node_condition(filter_request.chain)
        return query.where(condition)

    def _build_filter_node_condition(self, node: FilterNode) -> ColumnElement[bool]:
        if isinstance(node, FilterParam):
            return self._get_by(node.field, node.value, node.operator)
        conditions = [self._build_filter_node_condition(item) for item in node.items]
        if node.type == FilterType.AND:
            return and_(*conditions)
        return or_(*conditions)

    def _paginate(self, query: Select, skip: int = 0, limit: int = 100) -> Select:
        if limit > -1:
            query = query.offset(skip).limit(limit)
        return query

    def _sort_by(
        self,
        query: Select,
        sort_by: str | None = None,
        sort_type: SortTypeEnum | None = SortTypeEnum.asc,
    ) -> Select:
        if sort_by is None:
            if hasattr(self.model_class, "updated_at"):
                sort_by = "updated_at"
            else:
                return query
        try:
            order_column = getattr(self.model_class, sort_by)
        except AttributeError as exc:
            raise BadRequestError(
                f"Field {sort_by} not in the fields of the model {self.model_class.__name__}",
            ) from exc
        if sort_type == SortTypeEnum.desc:
            return query.order_by(order_column.desc())
        return query.order_by(order_column.asc())

    async def _all(self, query: Select) -> list[ModelType]:
        result = await self.session.scalars(query)
        return result.all()

    async def _one_or_none(self, query: Select) -> ModelType | None:
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def _count(self, query: Select) -> int:
        subq = query.subquery()
        result = await self.session.scalars(select(func.count()).select_from(subq))
        return result.one()

    def _get_conflict_fields(self) -> list[str]:
        mapper = inspect(self.model_class)
        table = mapper.local_table
        cols = {col.key for col in table.columns if col.unique}
        for constr in table.constraints:
            if isinstance(constr, UniqueConstraint):
                cols |= {c.key for c in constr.columns}
        return list(cols)

    def _get_model_field_type(self, _model: type[ModelType], _field: str) -> type:
        return getattr(_model, _field).type.python_type

    def _resolve_field_relation(self, field: str) -> tuple[type[ModelType], str]:
        """Resolve model and column name from field — unlimited depth."""
        if "." in field:
            parts = field.split(".")
            current_model = self.model_class
            for rel_name in parts[:-1]:
                if hasattr(current_model, rel_name):
                    current_model = getattr(
                        current_model,
                        rel_name,
                    ).property.mapper.class_
                else:
                    raise ValidationError(
                        f"{current_model.__name__} has no relation with {rel_name}",
                    )
            column_name = parts[-1]
        else:
            current_model = self.model_class
            column_name = field

        if column_name not in [c.key for c in inspect(current_model).columns]:
            raise ValidationError(f"Wrong field: {field}")

        return current_model, column_name

    async def _modify_by(
        self,
        field: str,
        value: Any,
        *,
        attributes: dict[str, Any] | None = None,
        operator: QueryOperator = QueryOperator.EQUALS,
        op: Literal["update", "delete"],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        expr = self._get_by(field, value, operator)
        conditions = list(expr) if isinstance(expr, tuple) else [expr]
        if op == "update":
            for f, v in (attributes or {}).items():
                self._validate_params(field=f, value=v)
            stmt = (
                update(self.model_class)
                .where(*conditions)
                .values(**(attributes or {}))
                .returning(self.model_class)
            )
        else:
            stmt = delete(self.model_class).where(*conditions).returning(self.model_class)
        select_stmt = self._query().from_statement(stmt)
        if unique:
            return await self._one_or_none(select_stmt)
        return await self._all(select_stmt)

    async def _modify_by_filters(
        self,
        filter_request: FilterRequest,
        *,
        attributes: dict[str, Any] | None = None,
        op: Literal["update", "delete"],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        clause = self._build_filter_node_condition(filter_request.chain)
        if op == "update":
            for f, v in (attributes or {}).items():
                self._validate_params(field=f, value=v)
            stmt = (
                update(self.model_class)
                .where(clause)
                .values(**(attributes or {}))
                .returning(self.model_class)
            )
        else:
            stmt = delete(self.model_class).where(clause).returning(self.model_class)
        select_stmt = self._query().from_statement(stmt)
        if unique:
            return await self._one_or_none(select_stmt)
        return await self._all(select_stmt)
