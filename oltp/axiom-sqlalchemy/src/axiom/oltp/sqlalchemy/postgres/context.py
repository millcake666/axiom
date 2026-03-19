# ruff: noqa: D100, D101, D102, D103, D105, D107
# mypy: disable-error-code="type-arg"
"""axiom.oltp.sqlalchemy.postgres.context — Session context for RoutingSession."""

from contextvars import ContextVar, Token

session_context: ContextVar[str] = ContextVar[str]("session_context")


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)
