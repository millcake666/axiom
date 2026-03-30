"""Round-trip tests for all serialization strategies."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from axiom.cache.serialization import get_serializer
from axiom.cache.serialization.dill_strategy import DillStrategy
from axiom.cache.serialization.msgpack_strategy import MsgpackStrategy
from axiom.cache.serialization.orjson_strategy import OrjsonStrategy
from axiom.cache.serialization.pydantic_strategy import PydanticStrategy


class SampleModel(BaseModel):
    """Simple Pydantic model for testing."""

    name: str
    value: int


class TestOrjsonStrategy:
    """Tests for OrjsonStrategy."""

    def test_roundtrip_dict(self) -> None:
        """Serialize and deserialize a dict."""
        s = OrjsonStrategy()
        data = {"key": "value", "num": 42}
        assert s.deserialize(s.serialize(data)) == data

    def test_roundtrip_list(self) -> None:
        """Serialize and deserialize a list."""
        s = OrjsonStrategy()
        data = [1, 2, 3]
        assert s.deserialize(s.serialize(data)) == data

    def test_roundtrip_string(self) -> None:
        """Serialize and deserialize a string."""
        s = OrjsonStrategy()
        assert s.deserialize(s.serialize("hello")) == "hello"

    def test_serialize_returns_bytes(self) -> None:
        """serialize() returns bytes."""
        s = OrjsonStrategy()
        assert isinstance(s.serialize({"x": 1}), bytes)

    def test_get_serializer_orjson(self) -> None:
        """get_serializer('orjson') returns OrjsonStrategy."""
        s = get_serializer("orjson")
        assert isinstance(s, OrjsonStrategy)


class TestDillStrategy:
    """Tests for DillStrategy."""

    def test_roundtrip_dict(self) -> None:
        """Serialize and deserialize a dict."""
        s = DillStrategy()
        data = {"a": 1, "b": [2, 3]}
        assert s.deserialize(s.serialize(data)) == data

    def test_roundtrip_lambda(self) -> None:
        """Dill can serialize lambdas."""
        s = DillStrategy()
        fn = lambda x: x * 2  # noqa: E731
        result = s.deserialize(s.serialize(fn))
        assert result(5) == 10

    def test_serialize_returns_bytes(self) -> None:
        """serialize() returns bytes."""
        s = DillStrategy()
        assert isinstance(s.serialize(42), bytes)

    def test_get_serializer_dill(self) -> None:
        """get_serializer('dill') returns DillStrategy."""
        s = get_serializer("dill")
        assert isinstance(s, DillStrategy)


class TestMsgpackStrategy:
    """Tests for MsgpackStrategy."""

    def test_roundtrip_dict(self) -> None:
        """Serialize and deserialize a dict."""
        s = MsgpackStrategy()
        data = {"x": 1, "y": "hello"}
        assert s.deserialize(s.serialize(data)) == data

    def test_roundtrip_list(self) -> None:
        """Serialize and deserialize a list."""
        s = MsgpackStrategy()
        data = [1, 2, "three"]
        assert s.deserialize(s.serialize(data)) == data

    def test_serialize_returns_bytes(self) -> None:
        """serialize() returns bytes."""
        s = MsgpackStrategy()
        assert isinstance(s.serialize({"k": "v"}), bytes)

    def test_get_serializer_msgpack(self) -> None:
        """get_serializer('msgpack') returns MsgpackStrategy."""
        s = get_serializer("msgpack")
        assert isinstance(s, MsgpackStrategy)


class TestPydanticStrategy:
    """Tests for PydanticStrategy."""

    def test_roundtrip_pydantic_model(self) -> None:
        """Serialize a Pydantic model and get back its dict."""
        s = PydanticStrategy()
        model = SampleModel(name="test", value=99)
        result = s.deserialize(s.serialize(model))
        assert result == {"name": "test", "value": 99}

    def test_roundtrip_plain_dict(self) -> None:
        """Serialize a plain dict."""
        s = PydanticStrategy()
        data = {"a": 1}
        assert s.deserialize(s.serialize(data)) == data

    def test_serialize_returns_bytes(self) -> None:
        """serialize() returns bytes."""
        s = PydanticStrategy()
        assert isinstance(s.serialize({"k": "v"}), bytes)

    def test_get_serializer_pydantic(self) -> None:
        """get_serializer('pydantic') returns PydanticStrategy."""
        s = get_serializer("pydantic")
        assert isinstance(s, PydanticStrategy)
