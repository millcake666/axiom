"""Unit tests for SyncMailClient."""

from unittest.mock import MagicMock

from axiom.email.client import SyncMailClient
from axiom.email.models import EmailMessage
from axiom.email.testing import FakeMailBackend, InMemoryMailBackend


class TestSyncMailClientHappyPath:
    def test_send_simple(self):
        backend = InMemoryMailBackend()
        client = SyncMailClient(backend)
        result = client.send(to=["a@b.com"], subject="Hi", text="Hello")
        assert result.success is True
        assert len(backend.sent_messages) == 1
        assert backend.sent_messages[0].subject == "Hi"

    def test_send_message(self):
        backend = InMemoryMailBackend()
        client = SyncMailClient(backend)
        msg = EmailMessage(to=["x@y.com"], subject="Full")
        result = client.send_message(msg)
        assert result.success is True


class TestSyncMailClientHooks:
    def test_hooks_called_in_order(self):
        call_order = []
        hook = MagicMock()
        hook.before_send.side_effect = lambda m: call_order.append("before")
        hook.after_send.side_effect = lambda m, r: call_order.append("after")

        backend = FakeMailBackend()
        client = SyncMailClient(backend, hooks=[hook])
        client.send(to=["a@b.com"], subject="Test")

        assert call_order == ["before", "after"]

    def test_hooks_called_even_on_error(self):
        call_order = []
        hook = MagicMock()
        hook.before_send.side_effect = lambda m: call_order.append("before")
        hook.after_send.side_effect = lambda m, r: call_order.append("after")

        failing_backend = MagicMock()
        failing_backend.send.side_effect = RuntimeError("boom")

        client = SyncMailClient(failing_backend, hooks=[hook])
        result = client.send(to=["a@b.com"], subject="Fail")

        assert call_order == ["before", "after"]
        assert result.success is False
        assert "boom" in result.error

    def test_multiple_hooks_all_called(self):
        hook1 = MagicMock()
        hook2 = MagicMock()
        client = SyncMailClient(FakeMailBackend(), hooks=[hook1, hook2])
        client.send(to=["a@b.com"], subject="X")
        hook1.before_send.assert_called_once()
        hook2.before_send.assert_called_once()


class TestSyncMailClientErrorHandling:
    def test_backend_exception_returns_failed_result(self):
        failing_backend = MagicMock()
        failing_backend.send.side_effect = Exception("SMTP down")
        client = SyncMailClient(failing_backend)
        result = client.send(to=["a@b.com"], subject="X")
        assert result.success is False
        assert "SMTP down" in result.error
