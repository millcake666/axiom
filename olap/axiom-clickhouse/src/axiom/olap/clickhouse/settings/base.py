"""axiom.olap.clickhouse.settings.base — ClickHouseSettings definition."""

from axiom.core.settings import BaseAppSettings


class ClickHouseSettings(BaseAppSettings):
    """Settings for ClickHouse connection."""

    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 8123
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "default"
    CLICKHOUSE_SECURE: bool = False
    CLICKHOUSE_CONNECT_TIMEOUT: int = 10
    CLICKHOUSE_SEND_RECEIVE_TIMEOUT: int = 300
