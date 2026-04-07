"""Unit tests for axiom.email.models."""

import pytest

from axiom.email.models import Attachment, EmailAddress, EmailMessage, SendResult


class TestEmailAddress:
    def test_str_with_name(self):
        addr = EmailAddress(email="user@example.com", name="John Doe")
        assert str(addr) == "John Doe <user@example.com>"

    def test_str_without_name(self):
        addr = EmailAddress(email="user@example.com")
        assert str(addr) == "user@example.com"

    def test_default_name_empty(self):
        addr = EmailAddress(email="a@b.com")
        assert addr.name == ""


class TestAttachment:
    def test_defaults(self):
        att = Attachment(filename="file.txt", content=b"hello")
        assert att.content_type == "application/octet-stream"
        assert att.inline is False
        assert att.content_id == ""

    def test_custom_fields(self):
        att = Attachment(
            filename="img.png",
            content=b"\x89PNG",
            content_type="image/png",
            inline=True,
            content_id="img001",
        )
        assert att.inline is True
        assert att.content_id == "img001"


class TestEmailMessage:
    def test_required_fields(self):
        msg = EmailMessage(to=["a@b.com"], subject="Hello")
        assert msg.to == ["a@b.com"]
        assert msg.subject == "Hello"

    def test_defaults(self):
        msg = EmailMessage(to=[], subject="")
        assert msg.text is None
        assert msg.html is None
        assert msg.from_ is None
        assert msg.cc == []
        assert msg.bcc == []
        assert msg.reply_to is None
        assert msg.headers == {}
        assert msg.attachments == []

    def test_full_message(self):
        msg = EmailMessage(
            to=["a@b.com", "c@d.com"],
            subject="Test",
            text="plain",
            html="<b>html</b>",
            from_="sender@x.com",
            cc=["e@f.com"],
            bcc=["g@h.com"],
            reply_to="reply@x.com",
            headers={"X-Custom": "value"},
            attachments=[Attachment(filename="f.txt", content=b"data")],
        )
        assert len(msg.to) == 2
        assert msg.headers["X-Custom"] == "value"
        assert len(msg.attachments) == 1

    def test_mutable_defaults_are_independent(self):
        msg1 = EmailMessage(to=[], subject="a")
        msg2 = EmailMessage(to=[], subject="b")
        msg1.cc.append("x@y.com")
        assert msg2.cc == []


class TestSendResult:
    def test_success(self):
        result = SendResult(success=True, message_id="<abc123@mail>")
        assert result.success is True
        assert result.message_id == "<abc123@mail>"
        assert result.error is None

    def test_failure(self):
        result = SendResult(success=False, error="Connection refused")
        assert result.success is False
        assert result.error == "Connection refused"
        assert result.message_id is None

    def test_minimal(self):
        result = SendResult(success=True)
        assert result.message_id is None
        assert result.error is None
