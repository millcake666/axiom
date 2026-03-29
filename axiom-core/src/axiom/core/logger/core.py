"""axiom.core.logger.core — Structured logging configuration and helpers."""

import sys
from collections.abc import Callable
from typing import IO, Any

from loguru import logger

from axiom.core.logger.settings import LoggerSettings


def _build_json_serializer(
    fields: list[str] | None = None,
    extra_serializer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> Callable[[dict[str, Any]], str]:
    """Build a JSON serializer callable for loguru records."""
    active_fields = set(fields) if fields else None

    def _serialize(record: dict[str, Any]) -> str:
        import json
        from datetime import timezone

        data: dict[str, Any] = {
            "timestamp": record["time"].astimezone(timezone.utc).isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "logger_name": record["name"],
            "module": record["module"],
            "function": record["function"],
            "line": record["line"],
            "exception": None,
            "extra": record.get("extra", {}),
        }

        if record["exception"]:
            exc_type, exc_value, _ = record["exception"]
            data["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "value": str(exc_value) if exc_value else None,
            }

        if extra_serializer:
            data = extra_serializer(data)

        if active_fields:
            data = {k: v for k, v in data.items() if k in active_fields}

        return json.dumps(data, default=str) + "\n"

    return _serialize


def _make_sink(
    stream: IO[str],
    serializer: Callable[[dict[str, Any]], str],
) -> Callable[[Any], None]:
    """Return a callable sink that writes serialized JSON to the stream."""

    def sink(message: Any) -> None:
        record = message.record
        output = serializer(record)
        stream.write(output)
        stream.flush()

    return sink


def configure_logger(
    settings: LoggerSettings | None = None,
    serializer: Callable[[dict[str, Any]], str] | None = None,
    extra_serializer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    **overrides: Any,
) -> None:
    """Configure the loguru logger from settings, removing any existing sinks first.

    Safe to call multiple times; each call resets all previously registered sinks.
    When ``LOG_FORMAT`` is ``"auto"``, JSON is used for non-dev stages and plain
    text is used for ``APP_STAGE="dev"``.

    Args:
        settings: Logger settings instance; created from environment if omitted.
        serializer: Custom JSON serializer callable that receives a loguru record
            dict and returns a JSON string. Supersedes the built-in serializer.
        extra_serializer: Optional function to transform the record dict before
            JSON encoding. Ignored when ``serializer`` is provided.
        **overrides: Field-level overrides that shadow the corresponding
            ``LoggerSettings`` values (e.g. ``LOG_LEVEL="DEBUG"``).
    """
    if settings is None:
        settings = LoggerSettings()

    level = overrides.get("LOG_LEVEL", settings.LOG_LEVEL)
    fmt = overrides.get("LOG_FORMAT", settings.LOG_FORMAT)
    output = overrides.get("LOG_OUTPUT", settings.LOG_OUTPUT)
    file_path = overrides.get("LOG_FILE_PATH", settings.LOG_FILE_PATH)

    if fmt == "auto":
        fmt = "text" if settings.APP_STAGE == "dev" else "json"

    logger.remove()

    if fmt == "json":
        _serializer: Callable[[dict[str, Any]], str]
        if serializer is not None:
            _serializer = serializer
        else:
            _serializer = _build_json_serializer(
                fields=settings.LOG_JSON_FIELDS,
                extra_serializer=extra_serializer,
            )

        if output == "file" and file_path:
            _fp = file_path

            def _file_sink(message: Any) -> None:
                record = message.record
                out = _serializer(record)
                with open(_fp, "a", encoding="utf-8") as f:
                    f.write(out)

            logger.add(_file_sink, level=level)
        else:
            stream: IO[str] = sys.stderr if output == "stderr" else sys.stdout
            logger.add(_make_sink(stream, _serializer), level=level)
    else:
        if output == "file" and file_path:
            logger.add(file_path, level=level)
        else:
            stream = sys.stderr if output == "stderr" else sys.stdout
            logger.add(stream, level=level)


def get_logger(name: str | None = None) -> Any:
    """Return a loguru logger, optionally bound with a ``logger_name`` extra field.

    Args:
        name: Optional name to bind as ``logger_name`` in every log record.

    Returns:
        Loguru logger instance, bound with ``logger_name`` when name is given.
    """
    if name:
        return logger.bind(logger_name=name)
    return logger
