"""Unit tests for YandexSyncSMTPBackend with mocked smtplib."""

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from axiom.email.models import Attachment, EmailMessage
from axiom.email.providers.yandex.config import YandexSMTPConfig
from axiom.email.providers.yandex.sync_backend import YandexSyncSMTPBackend


def _make_config(**kwargs):
    defaults = {"username": "user@yandex.ru", "password": "secret"}
    defaults.update(kwargs)
    return YandexSMTPConfig(**defaults)


def _make_message(**kwargs):
    defaults = {"to": ["dst@example.com"], "subject": "Test", "text": "body"}
    defaults.update(kwargs)
    return EmailMessage(**defaults)


class TestYandexSyncBackendTLS:
    def test_sends_via_smtp_ssl(self):
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
            backend = YandexSyncSMTPBackend(_make_config(use_tls=True))
            result = backend.send(_make_message())

        assert result.success is True
        mock_smtp.login.assert_called_once_with("user@yandex.ru", "secret")
        mock_smtp.sendmail.assert_called_once()

    def test_smtp_exception_returns_failure(self):
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)
        mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
            backend = YandexSyncSMTPBackend(_make_config())
            result = backend.send(_make_message())

        assert result.success is False
        assert result.error is not None


class TestYandexSyncBackendSTARTTLS:
    def test_sends_via_starttls(self):
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)

        with patch("smtplib.SMTP", return_value=mock_smtp):
            backend = YandexSyncSMTPBackend(_make_config(use_tls=False, port=587))
            result = backend.send(_make_message())

        assert result.success is True
        mock_smtp.starttls.assert_called_once()


class TestYandexSyncBackendContent:
    def test_multipart_text_and_html(self):
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)
        sent_data = {}

        def capture_sendmail(from_, to, data):
            sent_data["data"] = data

        mock_smtp.sendmail.side_effect = capture_sendmail

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
            backend = YandexSyncSMTPBackend(_make_config())
            backend.send(_make_message(text="plain", html="<b>html</b>"))

        assert "plain" in sent_data["data"]
        assert "html" in sent_data["data"]

    def test_cc_bcc_in_recipients(self):
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)
        recipients_used = {}

        def capture_sendmail(from_, to, data):
            recipients_used["to"] = to

        mock_smtp.sendmail.side_effect = capture_sendmail

        with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
            backend = YandexSyncSMTPBackend(_make_config())
            msg = _make_message(cc=["cc@ex.com"], bcc=["bcc@ex.com"])
            backend.send(msg)

        assert "cc@ex.com" in recipients_used["to"]
        assert "bcc@ex.com" in recipients_used["to"]

    def test_attachment_included(self):
        mock_smtp = MagicMock()
        mock_smtp.__enter__ = lambda s: s
        mock_smtp.__exit__ = MagicMock(return_value=False)
        sent_data = {}

        def capture(from_, to, data):
            sent_data["data"] = data

        mock_smtp.sendmail.side_effect = capture

        att = Attachment(filename="test.pdf", content=b"pdfdata", content_type="application/pdf")
        with patch("smtplib.SMTP_SSL", return_value=mock_smtp):
            backend = YandexSyncSMTPBackend(_make_config())
            backend.send(_make_message(attachments=[att]))

        assert "test.pdf" in sent_data["data"]

    def test_os_error_returns_failure(self):
        with patch("smtplib.SMTP_SSL", side_effect=OSError("no route to host")):
            backend = YandexSyncSMTPBackend(_make_config())
            result = backend.send(_make_message())

        assert result.success is False
        assert "no route to host" in result.error
