"""axiom.olap.clickhouse.client.factory — ClickHouse sync and async client factory."""

from __future__ import annotations

from typing import Any

import clickhouse_connect  # type: ignore[import-untyped]

from axiom.olap.clickhouse.settings.base import ClickHouseSettings


class ClickHouseClientFactory:
    """Factory for creating ClickHouse sync and async clients."""

    @staticmethod
    def create_sync_client(settings: ClickHouseSettings) -> Any:
        """Create a synchronous ClickHouse client from settings.

        Args:
            settings: ClickHouse connection settings.

        Returns:
            Synchronous clickhouse_connect Client.
        """
        return clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            username=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DATABASE,
            secure=settings.CLICKHOUSE_SECURE,
            connect_timeout=settings.CLICKHOUSE_CONNECT_TIMEOUT,
            send_receive_timeout=settings.CLICKHOUSE_SEND_RECEIVE_TIMEOUT,
        )

    @staticmethod
    async def create_async_client(settings: ClickHouseSettings) -> Any:
        """Create an asynchronous ClickHouse client from settings.

        Args:
            settings: ClickHouse connection settings.

        Returns:
            Asynchronous clickhouse_connect AsyncClient.
        """
        return await clickhouse_connect.get_async_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            username=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DATABASE,
            secure=settings.CLICKHOUSE_SECURE,
            connect_timeout=settings.CLICKHOUSE_CONNECT_TIMEOUT,
            send_receive_timeout=settings.CLICKHOUSE_SEND_RECEIVE_TIMEOUT,
        )
