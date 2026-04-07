"""Integration tests for SMTP backends using Mailpit testcontainer."""

import pytest
from testcontainers.mailpit import MailpitContainer

from axiom.email.client import AsyncMailClient, SyncMailClient
from axiom.email.models import EmailMessage
from axiom.email.providers.yandex import (
    YandexAsyncSMTPBackend,
    YandexSMTPConfig,
    YandexSyncSMTPBackend,
)

from .conftest import _resolve_docker_host

_TEST_PASSWORD = "test"  # noqa: S105 — test credentials, not production secrets


@pytest.fixture(scope="module")
def mailpit():
    """Start Mailpit container for all integration tests."""
    _resolve_docker_host()
    with MailpitContainer(image="axllent/mailpit:v1.21") as container:
        yield container


class TestMailpitSyncSMTP:
    """Integration tests for sync SMTP backend with real Mailpit server."""

    def test_sync_sends_email_successfully(self, mailpit: MailpitContainer):
        config = YandexSMTPConfig(
            username="test@localhost",
            password=_TEST_PASSWORD,
            host=mailpit.get_container_host_ip(),
            port=mailpit.get_exposed_smtp_port(),
            use_tls=False,
            default_from="test@localhost",
        )
        backend = YandexSyncSMTPBackend(config)
        client = SyncMailClient(backend)
        result = client.send(
            to=["recipient@localhost"],
            subject="Sync test via Mailpit",
            text="This email was sent to Mailpit container.",
        )
        assert result.success is True

    def test_sync_sends_html_and_text(self, mailpit: MailpitContainer):
        config = YandexSMTPConfig(
            username="test@localhost",
            password=_TEST_PASSWORD,
            host=mailpit.get_container_host_ip(),
            port=mailpit.get_exposed_smtp_port(),
            use_tls=False,
            default_from="test@localhost",
        )
        backend = YandexSyncSMTPBackend(config)
        client = SyncMailClient(backend)
        msg = EmailMessage(
            to=["user@localhost"],
            subject="HTML + Text via Mailpit",
            text="Plain text version",
            html="<b>HTML version</b>",
        )
        result = client.send_message(msg)
        assert result.success is True

    def test_sync_send_with_cc_and_bcc(self, mailpit: MailpitContainer):
        config = YandexSMTPConfig(
            username="test@localhost",
            password=_TEST_PASSWORD,
            host=mailpit.get_container_host_ip(),
            port=mailpit.get_exposed_smtp_port(),
            use_tls=False,
            default_from="test@localhost",
        )
        backend = YandexSyncSMTPBackend(config)
        client = SyncMailClient(backend)
        msg = EmailMessage(
            to=["to@localhost"],
            subject="With CC/BCC",
            text="Body",
            cc=["cc@localhost"],
            bcc=["bcc@localhost"],
        )
        result = client.send_message(msg)
        assert result.success is True


class TestMailpitAsyncSMTP:
    """Integration tests for async SMTP backend with real Mailpit server."""

    async def test_async_sends_email_successfully(self, mailpit: MailpitContainer):
        config = YandexSMTPConfig(
            username="test@localhost",
            password=_TEST_PASSWORD,
            host=mailpit.get_container_host_ip(),
            port=mailpit.get_exposed_smtp_port(),
            use_tls=False,
            validate_certs=False,
            default_from="test@localhost",
        )
        backend = YandexAsyncSMTPBackend(config)
        client = AsyncMailClient(backend)
        await client.startup()
        result = await client.send(
            to=["recipient@localhost"],
            subject="Async test via Mailpit",
            html="<b>This email was sent to Mailpit container.</b>",
        )
        await client.shutdown()
        assert result.success is True

    async def test_async_sends_html_and_text(self, mailpit: MailpitContainer):
        config = YandexSMTPConfig(
            username="test@localhost",
            password=_TEST_PASSWORD,
            host=mailpit.get_container_host_ip(),
            port=mailpit.get_exposed_smtp_port(),
            use_tls=False,
            validate_certs=False,
            default_from="test@localhost",
        )
        backend = YandexAsyncSMTPBackend(config)
        client = AsyncMailClient(backend)
        await client.startup()
        msg = EmailMessage(
            to=["user@localhost"],
            subject="Async HTML + Text via Mailpit",
            text="Plain text",
            html="<h1>HTML</h1>",
        )
        result = await client.send_message(msg)
        await client.shutdown()
        assert result.success is True
