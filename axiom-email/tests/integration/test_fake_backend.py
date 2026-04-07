"""Integration tests: full send flow with fake backends."""

from unittest.mock import MagicMock

import pytest

from axiom.email.client import AsyncMailClient, SyncMailClient
from axiom.email.hooks.logging import LoggingHook
from axiom.email.models import Attachment, EmailMessage
from axiom.email.templating.jinja2 import JinjaTemplateRenderer
from axiom.email.testing import AsyncInMemoryMailBackend, InMemoryMailBackend


class TestSyncIntegration:
    def test_send_stores_message(self):
        backend = InMemoryMailBackend()
        client = SyncMailClient(backend)
        client.send(to=["a@b.com"], subject="Hello", text="Hi there")
        assert len(backend.sent_messages) == 1
        assert backend.sent_messages[0].to == ["a@b.com"]

    def test_send_with_attachments_cc_bcc(self):
        backend = InMemoryMailBackend()
        client = SyncMailClient(backend)
        att = Attachment(filename="doc.pdf", content=b"data", content_type="application/pdf")
        msg = EmailMessage(
            to=["a@b.com"],
            subject="With attachments",
            html="<b>body</b>",
            cc=["cc@b.com"],
            bcc=["bcc@b.com"],
            headers={"X-Priority": "1"},
            attachments=[att],
        )
        result = client.send_message(msg)
        assert result.success is True
        stored = backend.sent_messages[0]
        assert stored.cc == ["cc@b.com"]
        assert stored.bcc == ["bcc@b.com"]
        assert len(stored.attachments) == 1

    def test_logging_hook_called(self):
        hook = MagicMock(spec=LoggingHook)
        backend = InMemoryMailBackend()
        client = SyncMailClient(backend, hooks=[hook])
        client.send(to=["a@b.com"], subject="Test")
        hook.before_send.assert_called_once()
        hook.after_send.assert_called_once()

    def test_jinja_renderer_integration(self):
        backend = InMemoryMailBackend()
        renderer = JinjaTemplateRenderer()
        client = SyncMailClient(backend, renderer=renderer)
        html = renderer.render("<h1>Hello {{ name }}</h1>", {"name": "Axiom"})
        msg = EmailMessage(to=["a@b.com"], subject="Rendered", html=html)
        result = client.send_message(msg)
        assert result.success is True
        assert "Axiom" in backend.sent_messages[0].html

    def test_backend_error_returns_failed_send_result(self):
        failing_backend = MagicMock()
        failing_backend.send.side_effect = Exception("Connection refused")
        client = SyncMailClient(failing_backend)
        result = client.send(to=["a@b.com"], subject="X")
        assert result.success is False
        assert result.error is not None

    def test_clear_resets_stored_messages(self):
        backend = InMemoryMailBackend()
        client = SyncMailClient(backend)
        client.send(to=["a@b.com"], subject="1")
        client.send(to=["b@b.com"], subject="2")
        assert len(backend.sent_messages) == 2
        backend.clear()
        assert len(backend.sent_messages) == 0


class TestAsyncIntegration:
    async def test_send_stores_message(self):
        backend = AsyncInMemoryMailBackend()
        client = AsyncMailClient(backend)
        result = await client.send(to=["a@b.com"], subject="Async Hello", html="<b>Hi</b>")
        assert result.success is True
        assert len(backend.sent_messages) == 1

    async def test_lifecycle_startup_shutdown(self):
        backend = AsyncInMemoryMailBackend()
        client = AsyncMailClient(backend)
        await client.startup()
        result = await client.send(to=["a@b.com"], subject="After startup")
        await client.shutdown()
        assert result.success is True

    async def test_logging_hook_async(self):
        hook = MagicMock(spec=LoggingHook)
        backend = AsyncInMemoryMailBackend()
        client = AsyncMailClient(backend, hooks=[hook])
        await client.send(to=["a@b.com"], subject="Test")
        hook.before_send.assert_called_once()
        hook.after_send.assert_called_once()

    async def test_jinja_renderer_async(self):
        backend = AsyncInMemoryMailBackend()
        renderer = JinjaTemplateRenderer()
        html = renderer.render("<p>{{ greeting }}</p>", {"greeting": "Hello Async"})
        client = AsyncMailClient(backend)
        msg = EmailMessage(to=["a@b.com"], subject="Async Rendered", html=html)
        result = await client.send_message(msg)
        assert result.success is True
        assert "Hello Async" in backend.sent_messages[0].html

    async def test_async_backend_error_returns_failed_result(self):
        from unittest.mock import AsyncMock

        failing_backend = AsyncMock()
        failing_backend.send = AsyncMock(side_effect=Exception("async crash"))
        client = AsyncMailClient(failing_backend)
        result = await client.send(to=["a@b.com"], subject="X")
        assert result.success is False
        assert "async crash" in result.error
