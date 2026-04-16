"""axiom.olap.clickhouse.query.builder — Translates query specs into ClickHouse SQL."""

from __future__ import annotations

import re
from typing import Any

from axiom.core.filter import FilterGroup, FilterParam, FilterRequest, FilterType, QueryOperator
from axiom.olap.clickhouse.query.specs import (
    GroupBySpec,
    MetricSpec,
    PageSpec,
    SortSpec,
)

# Whitelist for column/field names
_COLUMN_RE = re.compile(r"^[a-zA-Z0-9_.]+$")


def _py_to_ch_type(value: Any) -> str:
    """Infer ClickHouse parameter type from a Python value.

    Args:
        value: Python value to infer type from.

    Returns:
        ClickHouse type string (e.g. 'String', 'Int64', 'Float64').
    """
    if isinstance(value, bool):
        return "UInt8"
    if isinstance(value, int):
        return "Int64"
    if isinstance(value, float):
        return "Float64"
    if isinstance(value, (list, tuple)):
        items = list(value)
        return f"Array({_py_to_ch_type(items[0])})" if items else "Array(String)"
    return "String"


# Allowed time_series intervals mapped to ClickHouse functions
_INTERVAL_MAP: dict[str, str] = {
    "1m": "toStartOfMinute",
    "5m": "toStartOfFiveMinutes",
    "10m": "toStartOfTenMinutes",
    "15m": "toStartOfFifteenMinutes",
    "30m": "toStartOfInterval(toDateTime({field}), INTERVAL 30 MINUTE)",
    "1h": "toStartOfHour",
    "2h": "toStartOfInterval(toDateTime({field}), INTERVAL 2 HOUR)",
    "3h": "toStartOfInterval(toDateTime({field}), INTERVAL 3 HOUR)",
    "6h": "toStartOfInterval(toDateTime({field}), INTERVAL 6 HOUR)",
    "12h": "toStartOfInterval(toDateTime({field}), INTERVAL 12 HOUR)",
    "1d": "toStartOfDay",
    "1w": "toStartOfWeek",
}

ALLOWED_INTERVALS = frozenset(_INTERVAL_MAP.keys())


def _validate_column(name: str) -> str:
    """Validate that a column name contains only safe characters.

    Args:
        name: Column name to validate.

    Returns:
        The validated column name.

    Raises:
        ValueError: If the column name contains invalid characters.
    """
    if not _COLUMN_RE.match(name):
        raise ValueError(
            f"Invalid column name {name!r}. Only [a-zA-Z0-9_.] characters are allowed.",
        )
    return name


def _escape_like_value(value: str) -> str:
    """Escape special LIKE characters in a string value.

    Args:
        value: String value to escape.

    Returns:
        Escaped string with backslash, percent, and underscore escaped.
    """
    value = value.replace("\\", "\\\\")
    value = value.replace("%", "\\%")
    value = value.replace("_", "\\_")
    return value


def _build_condition(
    param: FilterParam,
    counter: list[int],
    params_dict: dict[str, Any],
) -> str:
    """Build a single SQL condition from a FilterParam.

    Args:
        param: The filter parameter to translate.
        counter: Mutable single-element list used as a shared counter for param naming.
        params_dict: Dictionary that will receive named parameter values.

    Returns:
        SQL condition string with {pN} placeholders.
    """
    field = _validate_column(param.field)
    op = param.operator
    value = param.value

    def next_key() -> str:
        key = f"p{counter[0]}"
        counter[0] += 1
        return key

    if op == QueryOperator.EQUALS:
        key = next_key()
        params_dict[key] = value
        return f"{field} = {{{key}:{_py_to_ch_type(value)}}}"

    elif op == QueryOperator.NOT_EQUAL:
        key = next_key()
        params_dict[key] = value
        return f"{field} != {{{key}:{_py_to_ch_type(value)}}}"

    elif op == QueryOperator.IN:
        key = next_key()
        items = list(value) if not isinstance(value, list) else value
        params_dict[key] = items
        elem_type = _py_to_ch_type(items[0]) if items else "String"
        return f"{field} IN {{{key}:Array({elem_type})}}"

    elif op == QueryOperator.NOT_IN:
        key = next_key()
        items = list(value) if not isinstance(value, list) else value
        params_dict[key] = items
        elem_type = _py_to_ch_type(items[0]) if items else "String"
        return f"{field} NOT IN {{{key}:Array({elem_type})}}"

    elif op == QueryOperator.GREATER:
        key = next_key()
        params_dict[key] = value
        return f"{field} > {{{key}:{_py_to_ch_type(value)}}}"

    elif op == QueryOperator.EQUALS_OR_GREATER:
        key = next_key()
        params_dict[key] = value
        return f"{field} >= {{{key}:{_py_to_ch_type(value)}}}"

    elif op == QueryOperator.LESS:
        key = next_key()
        params_dict[key] = value
        return f"{field} < {{{key}:{_py_to_ch_type(value)}}}"

    elif op == QueryOperator.EQUALS_OR_LESS:
        key = next_key()
        params_dict[key] = value
        return f"{field} <= {{{key}:{_py_to_ch_type(value)}}}"

    elif op == QueryOperator.STARTS_WITH:
        key = next_key()
        escaped = _escape_like_value(str(value))
        params_dict[key] = f"{escaped}%"
        return f"{field} LIKE {{{key}:String}}"

    elif op == QueryOperator.NOT_START_WITH:
        key = next_key()
        escaped = _escape_like_value(str(value))
        params_dict[key] = f"{escaped}%"
        return f"{field} NOT LIKE {{{key}:String}}"

    elif op == QueryOperator.ENDS_WITH:
        key = next_key()
        escaped = _escape_like_value(str(value))
        params_dict[key] = f"%{escaped}"
        return f"{field} LIKE {{{key}:String}}"

    elif op == QueryOperator.NOT_END_WITH:
        key = next_key()
        escaped = _escape_like_value(str(value))
        params_dict[key] = f"%{escaped}"
        return f"{field} NOT LIKE {{{key}:String}}"

    elif op == QueryOperator.CONTAINS:
        key = next_key()
        escaped = _escape_like_value(str(value))
        params_dict[key] = f"%{escaped}%"
        return f"{field} LIKE {{{key}:String}}"

    elif op == QueryOperator.NOT_CONTAIN:
        key = next_key()
        escaped = _escape_like_value(str(value))
        params_dict[key] = f"%{escaped}%"
        return f"{field} NOT LIKE {{{key}:String}}"

    else:
        raise ValueError(f"Unsupported QueryOperator: {op!r}")


def _build_node(
    node: FilterParam | FilterGroup,
    counter: list[int],
    params_dict: dict[str, Any],
) -> str:
    """Recursively build SQL from a filter tree node.

    Args:
        node: FilterParam or FilterGroup to translate.
        counter: Mutable counter for unique parameter names.
        params_dict: Dictionary that receives named parameter values.

    Returns:
        SQL fragment string.
    """
    if isinstance(node, FilterParam):
        return _build_condition(node, counter, params_dict)
    elif isinstance(node, FilterGroup):
        joiner = " AND " if node.type == FilterType.AND else " OR "
        parts = [_build_node(item, counter, params_dict) for item in node.items]
        if len(parts) == 1:
            return parts[0]
        return "(" + joiner.join(parts) + ")"
    else:
        raise ValueError(f"Unknown filter node type: {type(node)!r}")


def build_where(filter_request: FilterRequest) -> tuple[str, dict[str, Any]]:
    """Translate a FilterRequest into a WHERE clause and parameters dict.

    Args:
        filter_request: The filter request to translate.

    Returns:
        Tuple of (where_clause, params_dict). where_clause is the SQL fragment
        after WHERE (without the WHERE keyword). params_dict maps {pN} names to values.
    """
    counter: list[int] = [0]
    params: dict[str, Any] = {}
    clause = _build_node(filter_request.chain, counter, params)
    return clause, params


def build_order_by(sort_specs: list[SortSpec]) -> str:
    """Build an ORDER BY clause from a list of SortSpec objects.

    Args:
        sort_specs: List of sort specifications.

    Returns:
        ORDER BY clause string (without the ORDER BY keyword), or empty string.
    """
    if not sort_specs:
        return ""
    parts = []
    for spec in sort_specs:
        field = _validate_column(spec.field)
        direction = "ASC" if spec.direction.value == "asc" else "DESC"
        parts.append(f"{field} {direction}")
    return ", ".join(parts)


def build_limit_offset(page_spec: PageSpec) -> str:
    """Build a LIMIT/OFFSET clause from a PageSpec.

    Args:
        page_spec: Pagination specification.

    Returns:
        LIMIT ... OFFSET ... clause string.
    """
    return f"LIMIT {page_spec.limit} OFFSET {page_spec.offset}"


def build_group_by(group_by_spec: GroupBySpec) -> str:
    """Build a GROUP BY clause from a GroupBySpec.

    Args:
        group_by_spec: Group-by specification.

    Returns:
        GROUP BY clause string (without the GROUP BY keyword).
    """
    validated = [_validate_column(f) for f in group_by_spec.fields]
    return ", ".join(validated)


def build_having(filter_request: FilterRequest) -> tuple[str, dict[str, Any]]:
    """Build a HAVING clause from a FilterRequest.

    Args:
        filter_request: The filter request to translate into a HAVING clause.

    Returns:
        Tuple of (having_clause, params_dict).
    """
    return build_where(filter_request)


def build_select_columns(columns: list[str]) -> str:
    """Build a SELECT column list from a list of column names.

    Args:
        columns: List of column names to select.

    Returns:
        Comma-separated column list string, or '*' if empty.
    """
    if not columns:
        return "*"
    validated = [_validate_column(c) for c in columns]
    return ", ".join(validated)


def build_select_metrics(metrics: list[MetricSpec]) -> str:
    """Build a SELECT expression for aggregation metrics.

    Args:
        metrics: List of metric specifications.

    Returns:
        Comma-separated aggregation expressions with aliases.
    """
    parts = []
    for metric in metrics:
        field = _validate_column(metric.field)
        alias = _validate_column(metric.alias)
        parts.append(f"{metric.function.value}({field}) AS {alias}")
    return ", ".join(parts)


def build_time_bucket(time_field: str, interval: str) -> str:
    """Build a time bucket expression for time-series aggregation.

    Args:
        time_field: Name of the datetime field to bucket.
        interval: Time interval string (e.g., '1h', '1d').

    Returns:
        SQL expression for the time bucket.

    Raises:
        ValueError: If the interval is not in the allowed set.
    """
    if interval not in ALLOWED_INTERVALS:
        raise ValueError(
            f"Interval {interval!r} not allowed. Allowed intervals: {sorted(ALLOWED_INTERVALS)}",
        )
    field = _validate_column(time_field)
    template = _INTERVAL_MAP[interval]
    if "{field}" in template:
        return template.replace("{field}", field)
    return f"{template}({field})"


class ClickHouseQueryBuilder:
    """Stateless builder that translates query specs into ClickHouse SQL fragments.

    All methods are thin wrappers around the module-level builder functions.
    Can be used as an object where dependency injection is preferred.
    """

    def build_where(self, filter_request: FilterRequest) -> tuple[str, dict[str, Any]]:
        """Translate a FilterRequest into a WHERE clause and parameters dict."""
        return build_where(filter_request)

    def build_order_by(self, sort_specs: list[SortSpec]) -> str:
        """Build an ORDER BY clause from a list of SortSpec objects."""
        return build_order_by(sort_specs)

    def build_limit_offset(self, page_spec: PageSpec) -> str:
        """Build a LIMIT/OFFSET clause from a PageSpec."""
        return build_limit_offset(page_spec)

    def build_group_by(self, group_by_spec: GroupBySpec) -> str:
        """Build a GROUP BY clause from a GroupBySpec."""
        return build_group_by(group_by_spec)

    def build_having(self, filter_request: FilterRequest) -> tuple[str, dict[str, Any]]:
        """Build a HAVING clause from a FilterRequest."""
        return build_having(filter_request)

    def build_select_columns(self, columns: list[str]) -> str:
        """Build a SELECT column list from a list of column names."""
        return build_select_columns(columns)

    def build_select_metrics(self, metrics: list[MetricSpec]) -> str:
        """Build a SELECT expression for aggregation metrics."""
        return build_select_metrics(metrics)

    def build_time_bucket(self, time_field: str, interval: str) -> str:
        """Build a time bucket expression for time-series aggregation."""
        return build_time_bucket(time_field, interval)


__all__ = [
    "ALLOWED_INTERVALS",
    "ClickHouseQueryBuilder",
    "build_group_by",
    "build_having",
    "build_limit_offset",
    "build_order_by",
    "build_select_columns",
    "build_select_metrics",
    "build_time_bucket",
    "build_where",
    "py_to_ch_type",
    "validate_identifier",
]

py_to_ch_type = _py_to_ch_type
validate_identifier = _validate_column
