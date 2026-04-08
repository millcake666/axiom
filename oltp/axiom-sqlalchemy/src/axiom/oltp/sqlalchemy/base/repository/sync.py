# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="name-defined,valid-type,type-arg,attr-defined,assignment,arg-type,misc,call-overload,call-arg"
"""axiom.oltp.sqlalchemy.base.repository.sync — Sync SQLAlchemy repository."""

from collections.abc import Sequence
from typing import Any, Literal

from axiom.core.exceptions.http import BadRequestError, NotFoundError, ValidationError
from axiom.core.filter.expr import FilterNode, FilterParam, FilterRequest
from axiom.core.filter.type import FilterType, QueryOperator, SortTypeEnum
from axiom.oltp.sqlalchemy.abs.repository.sync import SyncBaseRepository
from axiom.oltp.sqlalchemy.base.declarative import Base
from sqlalchemy import Select, UniqueConstraint, and_, delete, func, inspect, not_, or_, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.expression import select


class SyncSQLAlchemyRepository[
    ModelType: Base,
    SessionType: Session,
    QueryType: Select,
](SyncBaseRepository):
    """Sync SQLAlchemy repository for any SQLAlchemy-compatible database."""

    model_class: type[ModelType]
    session: SessionType

    def create(self, attributes: dict[str, Any]) -> ModelType:
        created_model = self.model_class(**attributes)
        self.session.add(created_model)
        return created_model

    def create_many(self, attributes_list: list[dict[str, Any]]) -> list[ModelType]:
        if not attributes_list:
            return []
        models = []
        for attributes in attributes_list:
            created_model = self.model_class(**attributes)
            models.append(created_model)
            self.session.add(created_model)
        return models

    def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        if model is None:
            raise NotFoundError("Entity not found")
        for field, value in attributes.items():
            self._validate_params(field=field, value=value)
            setattr(model, field, value)
        self.session.flush()
        return model

    def delete(self, model: ModelType) -> ModelType:
        if model is None:
            raise NotFoundError("Entity not found")
        self.session.delete(model)
        return model

    def update_by_filters(
        self,
        filter_request: FilterRequest,
        attributes: dict[str, Any],
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return self._modify_by_filters(
            filter_request=filter_request,
            attributes=attributes,
            op="update",
            unique=unique,
        )

    def update_by(
        self,
        field: str,
        value: Any,
        attributes: dict[str, Any],
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return self._modify_by(
            field=field,
            value=value,
            attributes=attributes,
            operator=operator,
            op="update",
            unique=unique,
        )

    def delete_by_filters(
        self,
        filter_request: FilterRequest,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return self._modify_by_filters(
            filter_request=filter_request,
            op="delete",
            unique=unique,
        )

    def delete_by(
        self,
        field: str,
        value: Any,
        operator: QueryOperator = QueryOperator.EQUALS,
        unique: bool = False,
    ) -> ModelType | None | list[ModelType]:
        return self._modify_by(
            field=field,
            value=value,
            op="delete",
            operator=operator,
            unique=unique,
        )

    def update_many(self, models: Sequence[ModelType]) -> list[ModelType]:
        if not models:
            return []
        dicts = [self._model_to_dict(m) for m in models]
        self.session.execute(update(self.model_class), dicts)
        return list(models)

    def delete_many(self, models: Sequence[ModelType]) -> list[ModelType]:
        if not models:
            return []
        mapper = inspect(self.model_class)
        pk_col_name = list(mapper.primary_key)[0].key
        ids = [getattr(m, pk_col_name) for m in models]
        pk_col = getattr(self.model_class, pk_col_name)
        stmt = delete(self.model_class).where(pk_col.in_(ids)).returning(self.model_class)
        select_stmt = self._query().from_statement(stmt)
        return self._all(select_stmt)

    def _query(self) -> Select:
        return select(self.model_class)

    def _maybe_join(self, query: Select, field: str) -> Select:
        if "." not in field:
            return query
        parts = field.split(".")
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

    def _all(self, query: Select) -> list[ModelType]:
        result = self.session.scalars(query)
        return result.all()

    def _one_or_none(self, query: Select) -> ModelType | None:
        result = self.session.scalars(query)
        return result.one_or_none()

    def _count(self, query: Select) -> int:
        subq = query.subquery()
        result = self.session.scalars(select(func.count()).select_from(subq))
        return result.one()

    def _get_conflict_fields(self) -> list[str]:
        mapper = inspect(self.model_class)
        table = mapper.local_table
        cols = {col.key for col in table.columns if col.unique}
        for constr in table.constraints:
            if isinstance(constr, UniqueConstraint):
                cols |= {c.key for c in constr.columns}
        return list(cols)

    def _model_to_dict(self, model: ModelType) -> dict:
        mapper = inspect(self.model_class)
        return {col.key: getattr(model, col.key) for col in mapper.columns}

    def _get_model_field_type(self, _model: type[ModelType], _field: str) -> type:
        return getattr(_model, _field).type.python_type

    def _resolve_field_relation(self, field: str) -> tuple[type[ModelType], str]:
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

    def _modify_by(
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
            return self._one_or_none(select_stmt)
        return self._all(select_stmt)

    def _modify_by_filters(
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
            return self._one_or_none(select_stmt)
        return self._all(select_stmt)
