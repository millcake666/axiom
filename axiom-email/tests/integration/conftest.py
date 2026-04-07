"""Integration test configuration with Docker socket resolution for macOS."""

import os
from pathlib import Path

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
