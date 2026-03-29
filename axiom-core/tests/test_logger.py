"""Tests for axiom.core.logger module."""

import json

from axiom.core.logger import LoggerSettings, configure_logger, get_logger


def test_logger_text_format(capsys):
    """Logger in text format outputs human-readable text."""
    settings = LoggerSettings(LOG_FORMAT="text", LOG_OUTPUT="stderr", APP_STAGE="dev")
    configure_logger(settings)
    from loguru import logger

    logger.info("hello text")
    captured = capsys.readouterr()
    assert "hello text" in captured.err


def test_logger_json_format(capsys):
    """Logger in json format outputs valid JSON per line."""
    settings = LoggerSettings(LOG_FORMAT="json", LOG_OUTPUT="stderr", APP_STAGE="prod")
    configure_logger(settings)
    from loguru import logger

    logger.info("hello json")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    assert data["message"] == "hello json"
    assert "timestamp" in data
    assert "level" in data


def test_logger_auto_mode_dev(capsys):
    """Auto mode selects text format in dev stage."""
    settings = LoggerSettings(LOG_FORMAT="auto", APP_STAGE="dev", LOG_OUTPUT="stderr")
    configure_logger(settings)
    from loguru import logger

    logger.info("auto dev")
    captured = capsys.readouterr()
    # text format — not valid JSON line
    assert "auto dev" in captured.err


def test_logger_auto_mode_prod(capsys):
    """Auto mode selects json format in prod stage."""
    settings = LoggerSettings(LOG_FORMAT="auto", APP_STAGE="prod", LOG_OUTPUT="stderr")
    configure_logger(settings)
    from loguru import logger

    logger.info("auto prod")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    assert data["message"] == "auto prod"


def test_configure_logger_idempotent(capsys):
    """Repeated configure_logger calls don't accumulate sinks."""
    settings = LoggerSettings(LOG_FORMAT="json", LOG_OUTPUT="stderr")
    configure_logger(settings)
    configure_logger(settings)
    from loguru import logger

    logger.info("idempotent")
    captured = capsys.readouterr()
    lines = [ln for ln in captured.err.strip().splitlines() if ln]
    # Should appear exactly once
    assert len(lines) == 1


def test_default_json_fields(capsys):
    """Default JSON output includes all required fields."""
    settings = LoggerSettings(LOG_FORMAT="json", LOG_OUTPUT="stderr")
    configure_logger(settings)
    from loguru import logger

    logger.info("fields check")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    for field in [
        "timestamp",
        "level",
        "message",
        "logger_name",
        "module",
        "function",
        "line",
    ]:
        assert field in data


def test_custom_serializer(capsys):
    """Custom serializer fully replaces default JSON output."""
    import json as json_mod

    def my_serializer(record):
        return json_mod.dumps({"msg": record["message"], "lvl": record["level"].name}) + "\n"

    settings = LoggerSettings(LOG_FORMAT="json", LOG_OUTPUT="stderr")
    configure_logger(settings, serializer=my_serializer)
    from loguru import logger

    logger.info("custom")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    assert "msg" in data
    assert "timestamp" not in data


def test_extra_serializer(capsys):
    """Extra serializer adds fields on top of default."""

    def add_service(data):
        data["service"] = "test-svc"
        return data

    settings = LoggerSettings(LOG_FORMAT="json", LOG_OUTPUT="stderr")
    configure_logger(settings, extra_serializer=add_service)
    from loguru import logger

    logger.info("extra")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    assert data["service"] == "test-svc"
    assert "message" in data


def test_field_whitelist(capsys):
    """LOG_JSON_FIELDS whitelist limits output fields."""
    settings = LoggerSettings(
        LOG_FORMAT="json",
        LOG_OUTPUT="stderr",
        LOG_JSON_FIELDS=["message", "level"],
    )
    configure_logger(settings)
    from loguru import logger

    logger.info("whitelist")
    captured = capsys.readouterr()
    line = [ln for ln in captured.err.strip().splitlines() if ln][-1]
    data = json.loads(line)
    assert set(data.keys()) == {"message", "level"}


def test_get_logger_returns_bound():
    """get_logger with name returns bound logger."""
    log = get_logger("my-service")
    assert log is not None
