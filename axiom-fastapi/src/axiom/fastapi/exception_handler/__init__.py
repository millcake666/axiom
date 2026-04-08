"""axiom.fastapi.exception_handler — FastAPI exception handlers for axiom applications."""

from axiom.fastapi.exception_handler.domain import register_domain_handler
from axiom.fastapi.exception_handler.http import register_http_handler
from axiom.fastapi.exception_handler.unhandled import register_unhandled_handler
from axiom.fastapi.exception_handler.validation import register_validation_handler


def register_all_handlers(app: object, *, use_logger: bool = True) -> None:
    """Register all standard exception handlers on the FastAPI app.

    Registers in order: domain → validation → http → unhandled.

    Args:
        app: FastAPI application instance.
        use_logger: Whether to log errors via loguru.
    """
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        raise TypeError(f"Expected FastAPI, got {type(app).__name__}")
    register_domain_handler(app, use_logger=use_logger)
    register_validation_handler(app)
    register_http_handler(app)
    register_unhandled_handler(app, use_logger=use_logger)


__all__ = [
    "register_all_handlers",
    "register_domain_handler",
    "register_http_handler",
    "register_unhandled_handler",
    "register_validation_handler",
]
