"""Integration tests for axiom.core public API."""

import json

from axiom.core import (
    REQUEST_CONTEXT,
    AppMixin,
    BaseAppSettings,
    BaseDomainDC,
    BaseError,
    BaseSchema,
    DebugMixin,
    LoggerSettings,
    NotFoundError,
    PaginatedResponse,
    RequestContext,
    TypedContextVar,
    ValidationError,
    configure_logger,
    get_logger,
    make_env_prefix,
    set_request_context,
)


def test_all_imports():
    """All public API symbols are importable from axiom.core."""
    assert configure_logger is not None
    assert get_logger is not None
    assert LoggerSettings is not None
    assert BaseAppSettings is not None
    assert AppMixin is not None
    assert DebugMixin is not None
    assert make_env_prefix is not None
    assert RequestContext is not None
    assert TypedContextVar is not None
    assert REQUEST_CONTEXT is not None
    assert set_request_context is not None
    assert BaseError is not None
    assert NotFoundError is not None
    assert ValidationError is not None
    assert BaseSchema is not None
    assert BaseDomainDC is not None
    assert PaginatedResponse is not None


def test_logger_reads_app_stage_from_settings(capsys):
    """Logger auto mode reads APP_STAGE from LoggerSettings to pick format."""
    # prod stage -> json
    settings = LoggerSettings(APP_STAGE="prod", LOG_FORMAT="auto", LOG_OUTPUT="stderr")
    configure_logger(settings)
    from loguru import logger

    logger.info("integration test")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    assert data["message"] == "integration test"
