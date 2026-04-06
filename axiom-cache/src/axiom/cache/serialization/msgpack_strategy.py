"""axiom.cache.serialization.msgpack_strategy — msgpack serialization strategy."""

from typing import Any

import msgpack  # type: ignore[import-untyped]

from axiom.cache.serialization import SerializationStrategy


class MsgpackStrategy(SerializationStrategy):
    """Serialization using msgpack for compact binary encoding."""

    def serialize(self, value: Any) -> bytes:
        """Serialize value to bytes using msgpack."""
        return msgpack.packb(value, use_bin_type=True)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes using msgpack."""
        return msgpack.unpackb(data, raw=False)
