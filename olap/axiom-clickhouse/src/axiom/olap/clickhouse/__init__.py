"""axiom.olap.clickhouse — ClickHouse integration for analytical queries and data ingestion."""

from axiom.olap.clickhouse.client.factory import ClickHouseClientFactory
from axiom.olap.clickhouse.exception import (
    ClickHouseBulkInsertError,
    ClickHouseConfigError,
    ClickHouseConnectionError,
    ClickHouseError,
    ClickHouseImportError,
    ClickHouseMutationError,
    ClickHouseQueryError,
    ClickHouseRowMappingError,
    ClickHouseSchemaError,
)
from axiom.olap.clickhouse.query.builder import ClickHouseQueryBuilder
from axiom.olap.clickhouse.query.specs import (
    AggFunction,
    AggregateSpec,
    CHQuerySpec,
    GroupBySpec,
    MetricSpec,
    PageSpec,
    SortSpec,
)
from axiom.olap.clickhouse.repository.agg.async_ import AsyncClickHouseAggRepository
from axiom.olap.clickhouse.repository.agg.sync_ import ClickHouseAggRepository
from axiom.olap.clickhouse.repository.base.async_ import AsyncClickHouseBaseRepository
from axiom.olap.clickhouse.repository.base.sync_ import ClickHouseBaseRepository
from axiom.olap.clickhouse.repository.facade.async_ import AsyncClickHouseRepository
from axiom.olap.clickhouse.repository.facade.async_typed import AsyncTypedClickHouseRepository
from axiom.olap.clickhouse.repository.facade.sync_ import ClickHouseRepository
from axiom.olap.clickhouse.repository.facade.typed import TypedClickHouseRepository
from axiom.olap.clickhouse.repository.mutation.async_ import AsyncClickHouseMutationManager
from axiom.olap.clickhouse.repository.mutation.sync_ import ClickHouseMutationManager
from axiom.olap.clickhouse.repository.read.async_ import AsyncClickHouseReadRepository
from axiom.olap.clickhouse.repository.read.async_typed import AsyncTypedClickHouseReadRepository
from axiom.olap.clickhouse.repository.read.sync_ import ClickHouseReadRepository
from axiom.olap.clickhouse.repository.read.typed import TypedClickHouseReadRepository
from axiom.olap.clickhouse.repository.schema.async_ import AsyncClickHouseSchemaManager
from axiom.olap.clickhouse.repository.schema.sync_ import ClickHouseSchemaManager
from axiom.olap.clickhouse.repository.versioned.async_ import AsyncVersionedClickHouseRepository
from axiom.olap.clickhouse.repository.versioned.sync_ import VersionedClickHouseRepository
from axiom.olap.clickhouse.repository.write.async_ import AsyncClickHouseWriteRepository
from axiom.olap.clickhouse.repository.write.sync_ import ClickHouseWriteRepository
from axiom.olap.clickhouse.result.models import (
    AggregateResult,
    BulkInsertResult,
    ColumnInfo,
    MutationStatus,
    PagedResult,
    QueryResult,
    SingleInsertResult,
    TableInfo,
)
from axiom.olap.clickhouse.settings.base import ClickHouseSettings

__version__ = "0.1.0"

__all__ = [
    # Settings & client
    "ClickHouseClientFactory",
    "ClickHouseSettings",
    # Exceptions
    "ClickHouseBulkInsertError",
    "ClickHouseConfigError",
    "ClickHouseConnectionError",
    "ClickHouseError",
    "ClickHouseImportError",
    "ClickHouseMutationError",
    "ClickHouseQueryError",
    "ClickHouseRowMappingError",
    "ClickHouseSchemaError",
    # Query builder
    "ClickHouseQueryBuilder",
    # Query specs
    "AggFunction",
    "AggregateSpec",
    "CHQuerySpec",
    "GroupBySpec",
    "MetricSpec",
    "PageSpec",
    "SortSpec",
    # Result models
    "AggregateResult",
    "BulkInsertResult",
    "ColumnInfo",
    "MutationStatus",
    "PagedResult",
    "QueryResult",
    "SingleInsertResult",
    "TableInfo",
    # Repositories — base
    "AsyncClickHouseBaseRepository",
    "ClickHouseBaseRepository",
    # Repositories — read
    "AsyncClickHouseReadRepository",
    "AsyncTypedClickHouseReadRepository",
    "ClickHouseReadRepository",
    "TypedClickHouseReadRepository",
    # Repositories — write
    "AsyncClickHouseWriteRepository",
    "ClickHouseWriteRepository",
    # Repositories — aggregation
    "AsyncClickHouseAggRepository",
    "ClickHouseAggRepository",
    # Repositories — versioned
    "AsyncVersionedClickHouseRepository",
    "VersionedClickHouseRepository",
    # Schema & mutation management
    "AsyncClickHouseMutationManager",
    "AsyncClickHouseSchemaManager",
    "ClickHouseMutationManager",
    "ClickHouseSchemaManager",
    # Facades
    "AsyncClickHouseRepository",
    "AsyncTypedClickHouseRepository",
    "ClickHouseRepository",
    "TypedClickHouseRepository",
]
