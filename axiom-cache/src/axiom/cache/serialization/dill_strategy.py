"""axiom.cache.serialization.dill_strategy — dill serialization strategy."""

from __future__ import annotations

from typing import Any

import dill  # type: ignore[import-untyped]  # nosec B403

from axiom.cache.serialization import SerializationStrategy


class DillStrategy(SerializationStrategy):
    """Serialization using dill for Python object pickling."""

    def serialize(self, value: Any) -> bytes:
        """Serialize value to bytes using dill."""
        return dill.dumps(value)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes using dill."""
        return dill.loads(data)  # noqa: S301  # nosec B301
