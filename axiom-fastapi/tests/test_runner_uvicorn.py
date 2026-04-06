"""Tests for uvicorn runner."""

from unittest.mock import patch

from axiom.fastapi.runner import UvicornSettings, run_uvicorn


def test_run_uvicorn_calls_uvicorn_run() -> None:
    settings = UvicornSettings(host="127.0.0.1", port=9999)
    with patch("axiom.fastapi.runner.uvicorn.uvicorn.run") as mock_run:
        run_uvicorn("myapp:app", settings)
    mock_run.assert_called_once_with(
        "myapp:app",
        host="127.0.0.1",
        port=9999,
        workers=1,
        reload=False,
        log_level="info",
        factory=False,
    )


def test_uvicorn_settings_defaults() -> None:
    s = UvicornSettings()
    assert s.host == "0.0.0.0"  # noqa: S104
    assert s.port == 8000
    assert s.workers == 1
