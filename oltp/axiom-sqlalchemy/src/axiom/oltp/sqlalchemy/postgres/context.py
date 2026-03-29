# mypy: disable-error-code="type-arg"
"""axiom.oltp.sqlalchemy.postgres.context — Session context for RoutingSession."""

from contextvars import ContextVar, Token

session_context: ContextVar[str] = ContextVar[str]("session_context")
"""Context variable storing the active session identifier."""


def get_session_context() -> str:
    """Return the current session context identifier.

    Returns:
        The session ID stored in the current context.

    Raises:
        LookupError: If no session context has been set in the current context.
    """
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    """Set the session context identifier and return a reset token.

    Args:
        session_id: The session identifier to store.

    Returns:
        A ``Token`` that can be passed to ``reset_session_context`` to restore
        the previous value.
    """
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    """Restore the session context to its value before the last ``set_session_context`` call.

    Args:
        context: The ``Token`` returned by ``set_session_context``.
    """
    session_context.reset(context)
