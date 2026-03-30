"""axiom.cache.serialization.pydantic_strategy — Pydantic-aware serialization strategy."""

from __future__ import annotations

from typing import Any

import orjson

from axiom.cache.serialization import SerializationStrategy


class PydanticStrategy(SerializationStrategy):
    """Serialization strategy that handles Pydantic models via model_dump()."""

    def serialize(self, value: Any) -> bytes:
        """Serialize a Pydantic BaseModel or plain value to JSON bytes."""
        try:
            from pydantic import BaseModel

            if isinstance(value, BaseModel):
                return orjson.dumps(value.model_dump())
        except ImportError:
            pass
        return orjson.dumps(value)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize JSON bytes to a plain Python value."""
        return orjson.loads(data)
