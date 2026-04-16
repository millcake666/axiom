"""Unit tests for axiom.olap.clickhouse.exception hierarchy."""

from axiom.core.exceptions import BaseError
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


class TestExceptionHierarchy:
    def test_clickhouse_error_is_base_error(self):
        assert issubclass(ClickHouseError, BaseError)

    def test_connection_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseConnectionError, ClickHouseError)

    def test_query_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseQueryError, ClickHouseError)

    def test_row_mapping_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseRowMappingError, ClickHouseError)

    def test_bulk_insert_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseBulkInsertError, ClickHouseError)

    def test_mutation_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseMutationError, ClickHouseError)

    def test_schema_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseSchemaError, ClickHouseError)

    def test_config_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseConfigError, ClickHouseError)

    def test_import_error_is_clickhouse_error(self):
        assert issubclass(ClickHouseImportError, ClickHouseError)


class TestClickHouseError:
    def test_code_and_status(self):
        err = ClickHouseError("oops")
        assert err.code == "clickhouse_error"
        assert err.status_code == 500
        assert err.message == "oops"

    def test_connection_error_status(self):
        err = ClickHouseConnectionError("conn failed")
        assert err.status_code == 503
        assert err.code == "clickhouse_connection_error"

    def test_query_error_status(self):
        err = ClickHouseQueryError("bad query")
        assert err.status_code == 500


class TestRowMappingError:
    def test_defaults(self):
        err = ClickHouseRowMappingError("map fail")
        assert err.row_index == 0
        assert err.field is None
        assert err.details == {"row_index": 0, "field": None}

    def test_with_values(self):
        err = ClickHouseRowMappingError("map fail", row_index=3, field="name")
        assert err.row_index == 3
        assert err.field == "name"
        assert err.details["field"] == "name"
        assert err.details["row_index"] == 3


class TestBulkInsertError:
    def test_defaults(self):
        err = ClickHouseBulkInsertError("bulk fail")
        assert err.failed_chunks == []
        assert err.details == {"failed_chunks": []}

    def test_with_chunks(self):
        err = ClickHouseBulkInsertError("bulk fail", failed_chunks=[0, 2])
        assert err.failed_chunks == [0, 2]


class TestMutationError:
    def test_defaults(self):
        err = ClickHouseMutationError("mutation fail")
        assert err.mutation_id == ""

    def test_with_id(self):
        err = ClickHouseMutationError("mutation fail", mutation_id="mut-123")
        assert err.mutation_id == "mut-123"
        assert err.details["mutation_id"] == "mut-123"
