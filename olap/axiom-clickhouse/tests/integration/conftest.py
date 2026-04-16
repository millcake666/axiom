"""Integration test fixtures for axiom-clickhouse — ClickHouse testcontainers setup."""

import os
from pathlib import Path

import clickhouse_connect
import pytest
from testcontainers.clickhouse import ClickHouseContainer

_DOCKER_SOCKET_CANDIDATES = [
    Path.home() / ".docker" / "run" / "docker.sock",  # macOS Docker Desktop
    Path("/var/run/docker.sock"),  # Linux
    Path("/run/docker.sock"),  # Linux (alt)
]


def _resolve_docker_host() -> None:
    """Set DOCKER_HOST if not already set, using the first available socket."""
    if os.environ.get("DOCKER_HOST"):
        return

    for candidate in _DOCKER_SOCKET_CANDIDATES:
        if candidate.exists():
            os.environ["DOCKER_HOST"] = f"unix://{candidate}"
            os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
            return


@pytest.fixture(scope="module")
def clickhouse_container():
    """Start a ClickHouse container for integration tests."""
    _resolve_docker_host()
    with ClickHouseContainer() as container:
        yield container


@pytest.fixture(scope="module")
def ch_client(clickhouse_container: ClickHouseContainer):
    """Synchronous ClickHouse client connected to the test container."""
    client = clickhouse_connect.get_client(
        host=clickhouse_container.get_container_host_ip(),
        port=int(clickhouse_container.get_exposed_port(8123)),
        username=clickhouse_container.username,
        password=clickhouse_container.password,
        database=clickhouse_container.dbname,
    )
    yield client
    client.close()


@pytest.fixture(scope="module")
async def async_ch_client(clickhouse_container: ClickHouseContainer):
    """Asynchronous ClickHouse client connected to the test container."""
    client = await clickhouse_connect.get_async_client(
        host=clickhouse_container.get_container_host_ip(),
        port=int(clickhouse_container.get_exposed_port(8123)),
        username=clickhouse_container.username,
        password=clickhouse_container.password,
        database=clickhouse_container.dbname,
    )
    yield client
    await client.close()
