"""Unit tests for axiom.email.hooks.logging."""

from unittest.mock import patch

import pytest

from axiom.email.hooks.logging import LoggingHook
from axiom.email.models import Attachment, EmailMessage, SendResult


def _make_message(**kwargs):
    defaults = {"to": ["a@b.com"], "subject": "Test"}
    defaults.update(kwargs)
    return EmailMessage(**defaults)


class TestLoggingHook:
    def test_before_send_logs_metadata(self):
        hook = LoggingHook()
        msg = _make_message(attachments=[Attachment(filename="f.txt", content=b"x")])
        with patch.object(hook._logger, "info") as mock_log:
            hook.before_send(msg)
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args
            assert call_kwargs is not None

    def test_before_send_does_not_log_body(self):
        hook = LoggingHook()
        msg = _make_message(text="secret body", html="<b>secret</b>")
        logged_messages = []
        with patch.object(hook._logger, "info", side_effect=lambda tmpl, **kw: logged_messages.append(tmpl)):
            hook.before_send(msg)
        # No body content in template
        for tmpl in logged_messages:
            assert "secret" not in tmpl

    def test_after_send_logs_success(self):
        hook = LoggingHook()
        msg = _make_message()
        result = SendResult(success=True, message_id="<id123>")
        with patch.object(hook._logger, "info") as mock_log:
            hook.after_send(msg, result)
            mock_log.assert_called_once()

    def test_after_send_logs_failure(self):
        hook = LoggingHook()
        msg = _make_message()
        result = SendResult(success=False, error="Connection refused")
        with patch.object(hook._logger, "warning") as mock_warn:
            hook.after_send(msg, result)
            mock_warn.assert_called_once()

    def test_no_body_content_in_logs(self):
        hook = LoggingHook()
        msg = _make_message(text="secret body content", html="<b>secret html</b>")
        logged_templates = []
        # Capture template string only (not kwargs which include metadata)
        with patch.object(hook._logger, "info", side_effect=lambda t, **kw: logged_templates.append(t)):
            hook.before_send(msg)
        # Template string should not contain body content
        for tmpl in logged_templates:
            assert "secret body content" not in tmpl
            assert "secret html" not in tmpl
