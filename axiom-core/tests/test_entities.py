"""Tests for axiom.core.entities module."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from axiom.core.entities import BaseDomainDC, BaseRequestSchema, BaseSchema, PaginatedResponse

# --- BaseSchema ---


class UserORM:
    """Fake ORM model."""

    def __init__(self, name: str, age: int):  # noqa: D107
        self.name = name
        self.age = age


class UserSchema(BaseSchema):  # noqa: D101
    name: str
    age: int


def test_base_schema_from_orm():
    """BaseSchema supports from_attributes (ORM model)."""
    orm = UserORM("Alice", 30)
    schema = UserSchema.model_validate(orm)
    assert schema.name == "Alice"
    assert schema.age == 30


def test_request_schema_validation():
    """BaseRequestSchema validates incoming data."""

    class CreateUser(BaseRequestSchema):
        name: str
        age: int

    user = CreateUser(name="Bob", age=25)
    assert user.name == "Bob"


# --- PaginatedResponse ---


def test_paginated_response():
    """PaginatedResponse computes has_next correctly."""

    class Item(BaseSchema):
        id: int

    items = [Item(id=i) for i in range(10)]

    resp = PaginatedResponse[Item](items=items, total=25, page=1, page_size=10)
    assert resp.has_next is True

    resp2 = PaginatedResponse[Item](items=items, total=10, page=1, page_size=10)
    assert resp2.has_next is False


# --- BaseDomainDC ---


def test_domain_dc_defaults():
    """BaseDomainDC generates id, created_at, updated_at automatically."""
    dc = BaseDomainDC()
    assert isinstance(dc.id, UUID)
    assert isinstance(dc.created_at, datetime)
    assert isinstance(dc.updated_at, datetime)


def test_to_dict_serialization():
    """to_dict serializes UUID to str and datetime to ISO."""
    dc = BaseDomainDC()
    d = dc.to_dict()
    assert isinstance(d["id"], str)
    assert isinstance(d["created_at"], str)
    assert isinstance(d["updated_at"], str)


def test_from_dict():
    """from_dict deserializes dict back to dataclass."""
    original = BaseDomainDC()
    d = original.to_dict()
    restored = BaseDomainDC.from_dict(d)
    assert restored.id == original.id


def test_equality_by_id():
    """Two BaseDomainDC instances are equal if they share the same id."""
    shared_id = uuid4()
    a = BaseDomainDC(id=shared_id)
    b = BaseDomainDC(id=shared_id)
    c = BaseDomainDC()
    assert a == b
    assert a != c


def test_nested_dc_serialization():
    """to_dict handles nested dataclasses."""

    @dataclass
    class Address(BaseDomainDC):
        street: str = "Main St"

    @dataclass
    class Person(BaseDomainDC):
        address: Address = field(default_factory=Address)

    person = Person()
    d = person.to_dict()
    assert isinstance(d["address"], dict)
    assert d["address"]["street"] == "Main St"
