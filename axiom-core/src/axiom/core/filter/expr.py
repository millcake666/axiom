# ruff: noqa: D100, D101, D102, D103, D105, D107, E501
"""axiom.oltp.sqlalchemy.base.filter.schema — Filter schema definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Annotated, Any, Literal

from axiom.oltp.sqlalchemy.base.filter.type import FilterType, QueryOperator
from pydantic import BaseModel, Field


class FilterExpr(BaseModel, ABC):
    """Base class for all filter nodes."""

    kind: str

    @abstractmethod
    def extract_filter_params(self) -> list[FilterParam]:
        pass

    def __and__(self, other: FilterParam | FilterGroup) -> FilterGroup:
        return FilterGroup(type=FilterType.AND, items=[self, other])  # type: ignore[list-item]

    def __or__(self, other: FilterParam | FilterGroup) -> FilterGroup:
        return FilterGroup(type=FilterType.OR, items=[self, other])  # type: ignore[list-item]


class FilterParam(FilterExpr):
    """Atomic filter condition."""

    kind: Literal["param"] = "param"
    field: str = Field(..., examples=["name"])
    value: Any = Field(..., examples=["abc"])
    operator: QueryOperator = Field(..., examples=[QueryOperator.EQUALS])

    def extract_filter_params(self) -> list[FilterParam]:
        return [self]

    def __repr__(self) -> str:
        return f"FilterParam(field={self.field!r}, value={self.value!r}, operator={self.operator!r})"


class FilterGroup(FilterExpr):
    """Group of filter conditions with AND/OR operator."""

    kind: Literal["group"] = "group"
    type: FilterType = Field(..., examples=[FilterType.AND])
    items: list[FilterNode] = Field(..., examples=[[]])

    def extract_filter_params(self) -> list[FilterParam]:
        params = []
        for item in self.items:
            params.extend(item.extract_filter_params())
        return params

    def __repr__(self) -> str:
        items_repr = ", ".join(repr(item) for item in self.items)
        return f"FilterGroup(type={self.type!r}, items=[{items_repr}])"


FilterNode = Annotated[FilterParam | FilterGroup, Field(discriminator="kind")]


class FilterRequest(BaseModel):
    """Filter request with tree structure."""

    chain: FilterNode = Field(..., description="Root node of the filter tree")

    def extract_filter_params(self) -> list[FilterParam]:
        return self.chain.extract_filter_params()

    def __repr__(self) -> str:
        return f"FilterRequest(chain={self.chain!r})"
