"""Integration tests for Yandex SMTP backends (skipped without credentials)."""

import os

import pytest

YANDEX_USER = os.environ.get("YANDEX_SMTP_USERNAME")
YANDEX_PASS = os.environ.get("YANDEX_SMTP_PASSWORD")
YANDEX_TO = os.environ.get("YANDEX_SMTP_TO")

skip_without_credentials = pytest.mark.skipif(
    not (YANDEX_USER and YANDEX_PASS and YANDEX_TO),
    reason="YANDEX_SMTP_USERNAME, YANDEX_SMTP_PASSWORD, YANDEX_SMTP_TO env vars required",
)


@skip_without_credentials
def test_yandex_sync_sends_real_email():
    from axiom.email.client import SyncMailClient
    from axiom.email.providers.yandex import YandexSMTPConfig, YandexSyncSMTPBackend

    config = YandexSMTPConfig(username=YANDEX_USER, password=YANDEX_PASS)
    backend = YandexSyncSMTPBackend(config)
    client = SyncMailClient(backend)
    result = client.send(
        to=[YANDEX_TO],
        subject="axiom-email integration test (sync)",
        text="This is a real integration test.",
    )
    assert result.success is True


@skip_without_credentials
async def test_yandex_async_sends_real_email():
    from axiom.email.client import AsyncMailClient
    from axiom.email.providers.yandex import YandexAsyncSMTPBackend, YandexSMTPConfig

    config = YandexSMTPConfig(username=YANDEX_USER, password=YANDEX_PASS)
    backend = YandexAsyncSMTPBackend(config)
    client = AsyncMailClient(backend)
    await client.startup()
    result = await client.send(
        to=[YANDEX_TO],
        subject="axiom-email integration test (async)",
        html="<b>This is a real integration test.</b>",
    )
    await client.shutdown()
    assert result.success is True
