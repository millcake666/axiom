"""axiom.olap.clickhouse.query.specs — CH-specific query spec objects (mini-DSL)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from axiom.core.filter import FilterRequest, SortTypeEnum


class AggFunction(StrEnum):
    """Aggregation functions supported by ClickHouse query specs."""

    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    UNIQ = "UNIQ"
    QUANTILE = "QUANTILE"
    ANY = "ANY"
    ARRAY_AGG = "ARRAY_AGG"


class PageSpec(BaseModel):
    """Pagination specification for query results."""

    offset: int = 0
    limit: int = Field(default=100, ge=1, le=10000)


class SortSpec(BaseModel):
    """Sort specification for a single field."""

    field: str
    direction: SortTypeEnum = SortTypeEnum.asc


class MetricSpec(BaseModel):
    """Aggregation metric specification."""

    function: AggFunction
    field: str
    alias: str


class GroupBySpec(BaseModel):
    """Group-by specification for aggregation queries."""

    fields: list[str]


class AggregateSpec(BaseModel):
    """Full aggregation query specification."""

    metrics: list[MetricSpec]
    group_by: GroupBySpec | None = None
    having: FilterRequest | None = None
    order_by: list[SortSpec] | None = None
    page: PageSpec | None = None


class CHQuerySpec(BaseModel):
    """ClickHouse read query specification."""

    filters: FilterRequest | None = None
    columns: list[str] | None = None
    order_by: list[SortSpec] | None = None
    page: PageSpec | None = None


__all__ = [
    "AggFunction",
    "AggregateSpec",
    "CHQuerySpec",
    "GroupBySpec",
    "MetricSpec",
    "PageSpec",
    "SortSpec",
]
