"""Tests for gunicorn runner."""

from unittest.mock import patch

import pytest

from axiom.fastapi.runner import GunicornSettings


def test_gunicorn_settings_defaults() -> None:
    s = GunicornSettings()
    assert s.host == "0.0.0.0"  # noqa: S104
    assert s.port == 8000
    assert s.workers == 1
    assert s.timeout == 30


def test_run_gunicorn_invokes_app() -> None:
    try:
        from axiom.fastapi.runner import GunicornApplication, run_gunicorn
    except ImportError:
        pytest.skip("gunicorn not installed")

    settings = GunicornSettings(host="127.0.0.1", port=9998)
    with patch.object(GunicornApplication, "run") as mock_run:
        run_gunicorn("myapp:create_app", settings)
    mock_run.assert_called_once()
