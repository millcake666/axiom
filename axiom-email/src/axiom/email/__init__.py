"""axiom.email — Framework-independent email client with plugin architecture.

Minimal example::

    from axiom.email import AsyncMailClient
    from axiom.email.testing import AsyncInMemoryMailBackend

    backend = AsyncInMemoryMailBackend()
    client = AsyncMailClient(backend)
    result = await client.send(to=["user@example.com"], subject="Hi", html="<b>Hello</b>")

Advanced example::

    from axiom.email import AsyncMailClient, LoggingHook, JinjaTemplateRenderer
    from axiom.email.providers.yandex import YandexAsyncSMTPBackend, YandexSMTPConfig

    config = YandexSMTPConfig(username="me@yandex.ru", password="app-password")
    backend = YandexAsyncSMTPBackend(config)
    renderer = JinjaTemplateRenderer()
    client = AsyncMailClient(backend, renderer=renderer, hooks=[LoggingHook()])

    html = renderer.render("<h1>Hello {{ name }}</h1>", {"name": "World"})
    await client.send(to=["user@example.com"], subject="Greetings", html=html)
"""

__version__ = "0.1.0"

from axiom.email.client import AsyncMailClient, SyncMailClient
from axiom.email.hooks.logging import LoggingHook
from axiom.email.models import Attachment, EmailAddress, EmailMessage, SendResult
from axiom.email.templating.jinja2 import JinjaTemplateRenderer

__all__ = [
    "AsyncMailClient",
    "Attachment",
    "EmailAddress",
    "EmailMessage",
    "JinjaTemplateRenderer",
    "LoggingHook",
    "SendResult",
    "SyncMailClient",
]
