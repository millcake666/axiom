"""Unit tests for YandexAsyncSMTPBackend with mocked aiosmtplib."""

from unittest.mock import AsyncMock, patch

import pytest

from axiom.email.models import Attachment, EmailMessage
from axiom.email.providers.yandex.config import YandexSMTPConfig
from axiom.email.providers.yandex.async_backend import YandexAsyncSMTPBackend


def _make_config(**kwargs):
    defaults = {"username": "user@yandex.ru", "password": "secret"}
    defaults.update(kwargs)
    return YandexSMTPConfig(**defaults)


def _make_message(**kwargs):
    defaults = {"to": ["dst@example.com"], "subject": "Test", "text": "body"}
    defaults.update(kwargs)
    return EmailMessage(**defaults)


class TestYandexAsyncBackend:
    async def test_startup_shutdown_noop(self):
        backend = YandexAsyncSMTPBackend(_make_config())
        await backend.startup()
        await backend.shutdown()

    async def test_send_calls_aiosmtplib(self):
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            backend = YandexAsyncSMTPBackend(_make_config())
            result = await backend.send(_make_message())

        assert result.success is True
        mock_send.assert_awaited_once()

    async def test_smtp_exception_returns_failure(self):
        import aiosmtplib

        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = aiosmtplib.SMTPException("Auth failed")
            backend = YandexAsyncSMTPBackend(_make_config())
            result = await backend.send(_make_message())

        assert result.success is False
        assert "Auth failed" in result.error

    async def test_os_error_returns_failure(self):
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = OSError("timeout")
            backend = YandexAsyncSMTPBackend(_make_config())
            result = await backend.send(_make_message())

        assert result.success is False
        assert "timeout" in result.error

    async def test_cc_bcc_passed_as_recipients(self):
        kwargs_captured = {}

        async def capture(*args, **kw):
            kwargs_captured.update(kw)

        with patch("aiosmtplib.send", side_effect=capture):
            backend = YandexAsyncSMTPBackend(_make_config())
            msg = _make_message(cc=["cc@ex.com"], bcc=["bcc@ex.com"])
            await backend.send(msg)

        recipients = kwargs_captured.get("recipients", [])
        assert "cc@ex.com" in recipients
        assert "bcc@ex.com" in recipients
