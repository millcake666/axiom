"""Unit tests for AsyncMailClient."""

from unittest.mock import AsyncMock, MagicMock

from axiom.email.client import AsyncMailClient
from axiom.email.models import EmailMessage, SendResult
from axiom.email.testing import AsyncFakeMailBackend, AsyncInMemoryMailBackend


class TestAsyncMailClientHappyPath:
    async def test_send_simple(self):
        backend = AsyncInMemoryMailBackend()
        client = AsyncMailClient(backend)
        result = await client.send(to=["a@b.com"], subject="Hi", html="<b>Hi</b>")
        assert result.success is True
        assert len(backend.sent_messages) == 1

    async def test_send_message(self):
        backend = AsyncInMemoryMailBackend()
        client = AsyncMailClient(backend)
        msg = EmailMessage(to=["x@y.com"], subject="Full")
        result = await client.send_message(msg)
        assert result.success is True


class TestAsyncMailClientLifecycle:
    async def test_startup_shutdown_delegated(self):
        backend = AsyncMock()
        backend.send = AsyncMock(return_value=SendResult(success=True))
        client = AsyncMailClient(backend)

        await client.startup()
        backend.startup.assert_awaited_once()

        await client.shutdown()
        backend.shutdown.assert_awaited_once()


class TestAsyncMailClientHooks:
    async def test_hooks_called_in_order(self):
        call_order = []
        hook = MagicMock()
        hook.before_send.side_effect = lambda m: call_order.append("before")
        hook.after_send.side_effect = lambda m, r: call_order.append("after")

        client = AsyncMailClient(AsyncFakeMailBackend(), hooks=[hook])
        await client.send(to=["a@b.com"], subject="Test")

        assert call_order == ["before", "after"]

    async def test_hooks_called_on_error(self):
        call_order = []
        hook = MagicMock()
        hook.before_send.side_effect = lambda m: call_order.append("before")
        hook.after_send.side_effect = lambda m, r: call_order.append("after")

        failing_backend = AsyncMock()
        failing_backend.send = AsyncMock(side_effect=RuntimeError("async boom"))

        client = AsyncMailClient(failing_backend, hooks=[hook])
        result = await client.send(to=["a@b.com"], subject="Fail")

        assert call_order == ["before", "after"]
        assert result.success is False
        assert "async boom" in result.error


class TestAsyncMailClientErrorHandling:
    async def test_backend_exception_returns_failed_result(self):
        failing_backend = AsyncMock()
        failing_backend.send = AsyncMock(side_effect=Exception("conn refused"))
        client = AsyncMailClient(failing_backend)
        result = await client.send(to=["a@b.com"], subject="X")
        assert result.success is False
        assert "conn refused" in result.error
