"""Unit tests for ClickHouseSettings."""

from axiom.olap.clickhouse.settings.base import ClickHouseSettings


def test_settings_defaults():
    """ClickHouseSettings has correct default values."""
    settings = ClickHouseSettings()
    assert settings.CLICKHOUSE_HOST == "localhost"
    assert settings.CLICKHOUSE_PORT == 8123
    assert settings.CLICKHOUSE_USER == "default"
    assert settings.CLICKHOUSE_PASSWORD == ""
    assert settings.CLICKHOUSE_DATABASE == "default"
    assert settings.CLICKHOUSE_SECURE is False
    assert settings.CLICKHOUSE_CONNECT_TIMEOUT == 10
    assert settings.CLICKHOUSE_SEND_RECEIVE_TIMEOUT == 300


def test_settings_override():
    """ClickHouseSettings values can be overridden."""
    settings = ClickHouseSettings(
        CLICKHOUSE_HOST="my-host",
        CLICKHOUSE_PORT=9000,
        CLICKHOUSE_USER="admin",
        CLICKHOUSE_PASSWORD="secret",  # noqa: S106
        CLICKHOUSE_DATABASE="analytics",
        CLICKHOUSE_SECURE=True,
    )
    assert settings.CLICKHOUSE_HOST == "my-host"
    assert settings.CLICKHOUSE_PORT == 9000
    assert settings.CLICKHOUSE_USER == "admin"
    assert settings.CLICKHOUSE_PASSWORD == "secret"  # noqa: S105
    assert settings.CLICKHOUSE_DATABASE == "analytics"
    assert settings.CLICKHOUSE_SECURE is True
