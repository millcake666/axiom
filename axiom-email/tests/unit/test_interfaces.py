"""Unit tests for axiom.email.interfaces — Protocol satisfaction checks."""

import pytest

from axiom.email.interfaces import AsyncMailBackend, MailHook, SyncMailBackend, TemplateRenderer
from axiom.email.models import EmailMessage, SendResult
from axiom.email.testing import AsyncFakeMailBackend, AsyncInMemoryMailBackend, FakeMailBackend, InMemoryMailBackend


class MinimalTemplateRenderer:
    def render(self, template: str, context: dict) -> str:
        return template


class MinimalHook:
    def before_send(self, message: EmailMessage) -> None:
        pass

    def after_send(self, message: EmailMessage, result: SendResult) -> None:
        pass


def test_fake_backend_satisfies_sync_protocol():
    assert isinstance(FakeMailBackend(), SyncMailBackend)


def test_in_memory_backend_satisfies_sync_protocol():
    assert isinstance(InMemoryMailBackend(), SyncMailBackend)


def test_async_fake_backend_satisfies_async_protocol():
    assert isinstance(AsyncFakeMailBackend(), AsyncMailBackend)


def test_async_in_memory_satisfies_async_protocol():
    assert isinstance(AsyncInMemoryMailBackend(), AsyncMailBackend)


def test_minimal_renderer_satisfies_protocol():
    assert isinstance(MinimalTemplateRenderer(), TemplateRenderer)


def test_minimal_hook_satisfies_protocol():
    assert isinstance(MinimalHook(), MailHook)
