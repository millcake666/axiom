"""Unit tests for AppStateManager."""

from unittest.mock import MagicMock

import pytest

from axiom.fastapi.app.state import AppStateManager


def _app_with(key: str, value: object) -> object:
    app = MagicMock()
    setattr(app.state, key, value)
    return app


def test_set_stores_value_on_app_state() -> None:
    app = MagicMock()
    mgr = AppStateManager(app)
    mgr.set("foo", 42)
    assert app.state.foo == 42


def test_get_returns_stored_value() -> None:
    app = MagicMock()
    app.state.svc = "my_service"
    mgr = AppStateManager(app)
    result = mgr.get("svc", str)
    assert result == "my_service"


def test_get_raises_runtime_error_when_key_missing() -> None:
    app = MagicMock(spec=[])
    app.state = MagicMock(spec=[])  # no attributes → getattr returns None
    mgr = AppStateManager(app)
    with pytest.raises(RuntimeError, match="not initialized"):
        mgr.get("missing", object)


def test_set_then_get_roundtrip() -> None:
    app = MagicMock()
    mgr = AppStateManager(app)
    sentinel = object()
    mgr.set("sentinel", sentinel)
    assert mgr.get("sentinel", object) is sentinel
