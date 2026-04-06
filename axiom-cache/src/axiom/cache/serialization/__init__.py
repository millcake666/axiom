"""axiom.cache.serialization — Pluggable serialization strategies."""

from abc import ABC, abstractmethod
from typing import Any, Literal


class SerializationStrategy(ABC):
    """Abstract base class for serialization strategies."""

    @abstractmethod
    def serialize(self, value: Any) -> bytes:
        """Serialize value to bytes."""

    @abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes back to a value."""


SerializerType = Literal["orjson", "dill", "msgpack", "pydantic"]


def get_serializer(strategy: SerializerType) -> SerializationStrategy:
    """Return a serialization strategy instance by name."""
    if strategy == "orjson":
        from axiom.cache.serialization.orjson_strategy import OrjsonStrategy

        return OrjsonStrategy()
    elif strategy == "dill":
        from axiom.cache.serialization.dill_strategy import DillStrategy

        return DillStrategy()
    elif strategy == "msgpack":
        from axiom.cache.serialization.msgpack_strategy import MsgpackStrategy

        return MsgpackStrategy()
    elif strategy == "pydantic":
        from axiom.cache.serialization.pydantic_strategy import PydanticStrategy

        return PydanticStrategy()
    else:
        raise ValueError(f"Unknown serializer strategy: {strategy!r}")


__all__ = ["SerializationStrategy", "SerializerType", "get_serializer"]
