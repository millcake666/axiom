"""Tests for axiom.core.context module."""

import asyncio

import pytest

from axiom.core.context import (
    REQUEST_CONTEXT,
    BaseContext,
    RequestContext,
    TypedContextVar,
    set_request_context,
)


def test_typed_context_var_get_set():
    """TypedContextVar get/set works correctly."""
    var: TypedContextVar[int] = TypedContextVar("test_int", int)
    token = var.set(42)
    assert var.get() == 42
    var.reset(token)


def test_get_or_raise_unset():
    """get_or_raise raises RuntimeError when not set."""
    var: TypedContextVar[str] = TypedContextVar("unset_var", str)
    with pytest.raises(RuntimeError, match="unset_var"):
        var.get_or_raise()


def test_is_set():
    """is_set returns False when not set, True after set."""
    var: TypedContextVar[str] = TypedContextVar("is_set_var", str)
    assert var.is_set() is False
    token = var.set("hello")
    assert var.is_set() is True
    var.reset(token)
    assert var.is_set() is False


def test_request_context_defaults():
    """RequestContext has correct fields."""
    ctx = RequestContext(request_id="req-123")
    assert ctx.request_id == "req-123"
    assert ctx.user is None
    assert ctx.tenant is None
    assert ctx.extra == {}


def test_set_request_context():
    """set_request_context sets REQUEST_CONTEXT."""
    token = set_request_context("req-abc", user="john", tenant="acme")
    ctx = REQUEST_CONTEXT.get_or_raise()
    assert ctx.request_id == "req-abc"
    assert ctx.user == "john"
    assert ctx.tenant == "acme"
    REQUEST_CONTEXT.reset(token)


def test_context_isolation_between_tasks():
    """Context vars are isolated between async tasks."""

    async def run():
        var: TypedContextVar[str] = TypedContextVar("isolated", str)

        async def task_a():
            token = var.set("A")
            await asyncio.sleep(0)
            assert var.get() == "A"
            var.reset(token)

        async def task_b():
            token = var.set("B")
            await asyncio.sleep(0)
            assert var.get() == "B"
            var.reset(token)

        await asyncio.gather(task_a(), task_b())

    asyncio.run(run())


def test_base_context_is_base():
    """BaseContext is a base class."""
    assert issubclass(RequestContext, BaseContext)
