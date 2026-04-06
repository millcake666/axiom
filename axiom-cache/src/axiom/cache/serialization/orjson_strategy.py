"""axiom.cache.serialization.orjson_strategy — orjson serialization strategy."""

from typing import Any

import orjson

from axiom.cache.serialization import SerializationStrategy


class OrjsonStrategy(SerializationStrategy):
    """Serialization using orjson for fast JSON encoding/decoding."""

    def serialize(self, value: Any) -> bytes:
        """Serialize value to JSON bytes using orjson."""
        return orjson.dumps(value)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize JSON bytes using orjson."""
        return orjson.loads(data)
