"""axiom.core.context.var — Type-safe ContextVar wrapper."""

from contextvars import ContextVar, Token
from typing import Generic, TypeVar

T = TypeVar("T")


class TypedContextVar(Generic[T]):
    """Type-safe wrapper around contextvars.ContextVar.

    Provides get/set/reset operations with generic type support.
    """

    def __init__(self, name: str, type_: type[T], default: T | None = None) -> None:
        """Initialize TypedContextVar.

        Args:
            name: Name of the underlying ContextVar.
            type_: Expected type of the value.
            default: Optional default value; if provided, the ContextVar is
                created with that default.
        """
        self._name = name
        self._type = type_
        self._has_default = default is not None
        if default is not None:
            self._var: ContextVar[T] = ContextVar(name, default=default)
        else:
            self._var = ContextVar(name)

    def get(self) -> T | None:
        """Return the current value, or None if not set.

        Returns:
            Current value or None.
        """
        try:
            return self._var.get()
        except LookupError:
            return None

    def get_or_raise(self) -> T:
        """Return the current value, raising if not set.

        Returns:
            Current value.

        Raises:
            RuntimeError: If the variable is not set in the current context.
        """
        try:
            return self._var.get()
        except LookupError as err:
            raise RuntimeError(
                f"Context variable '{self._name}' is not set in the current context. "
                f"Make sure to set it before accessing.",
            ) from err

    def set(self, value: T) -> Token[T]:
        """Set the context variable and return a reset token.

        Args:
            value: Value to set.

        Returns:
            Token that can be passed to reset() to restore the previous value.
        """
        return self._var.set(value)

    def reset(self, token: Token[T]) -> None:
        """Restore the variable to its value before the matching set() call.

        Args:
            token: Token returned by a previous set() call.
        """
        self._var.reset(token)

    def is_set(self) -> bool:
        """Return True if a value is currently set in this context.

        Returns:
            True if set, False otherwise.
        """
        try:
            self._var.get()
            return True
        except LookupError:
            return False
