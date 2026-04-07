# axiom-email

`axiom-email` — framework-independent email client с backend/hook/renderer архитектурой.

## Когда Использовать

Пакет полезен, если вам нужен:

- один API для sync и async отправки email;
- hooks перед и после отправки;
- template renderer для HTML-писем;
- in-memory backend для тестов;
- SMTP provider без привязки к FastAPI или другому framework.

## Что Уже Реализовано

| Группа | Сущности |
|---|---|
| Clients | `AsyncMailClient`, `SyncMailClient` |
| Protocols | `AsyncMailBackend`, `SyncMailBackend`, `TemplateRenderer`, `MailHook` |
| Models | `EmailMessage`, `SendResult`, `EmailAddress`, `Attachment` |
| Hooks | `LoggingHook` |
| Rendering | `JinjaTemplateRenderer` |
| Providers | `YandexAsyncSMTPBackend`, `YandexSyncSMTPBackend`, `YandexSMTPConfig` |
| Testing | `AsyncInMemoryMailBackend`, `InMemoryMailBackend`, `AsyncFakeMailBackend`, `FakeMailBackend` |

## Установка

```bash
uv add axiom-email
uv add axiom-email[jinja2]
uv add axiom-email[aiosmtplib]
uv add axiom-email[all]
```

## Минимальный Пример

```python
from axiom.email import AsyncMailClient
from axiom.email.testing import AsyncInMemoryMailBackend

backend = AsyncInMemoryMailBackend()
client = AsyncMailClient(backend)

result = await client.send(
    to=["user@example.com"],
    subject="Hello",
    html="<b>Hello</b>",
)
```

Рендеринг шаблона делается явно:

```python
from axiom.email import JinjaTemplateRenderer

renderer = JinjaTemplateRenderer()
html = renderer.render("<h1>Hello {{ name }}</h1>", {"name": "Axiom"})
```

Пример с Yandex SMTP:

```python
from axiom.email import AsyncMailClient
from axiom.email.providers.yandex import YandexAsyncSMTPBackend, YandexSMTPConfig

config = YandexSMTPConfig(
    username="user@yandex.ru",
    password="app-password",
)
backend = YandexAsyncSMTPBackend(config)
client = AsyncMailClient(backend)
```

## Конфигурация

`YandexSMTPConfig` поддерживает:

- `username`
- `password`
- `host`
- `port`
- `use_tls`
- `default_from`
- `validate_certs`

## Интеграция С Другими Пакетами

- пакет не зависит от `axiom-fastapi` и может использоваться в CLI, workers или plain Python apps;
- `LoggingHook` использует `axiom.core.logger`;
- testing backends хорошо подходят для unit/integration tests других пакетов.

## Ограничения И Текущий Статус

- Из реальных provider implementations в коде сейчас есть только Yandex SMTP.
- Renderer хранится в client-е, но автоматического шага "template -> render -> send" клиент сам не делает: шаблон нужно рендерить явно.
- SMTP backends создают новое соединение на каждую отправку. Это простой и предсказуемый, но не самый дешевый по latency путь.

## Связанный Код

- `src/axiom/email/client.py`
- `src/axiom/email/interfaces.py`
- `src/axiom/email/providers/yandex/`
- `src/axiom/email/testing/`
- `tests/unit/test_client_async.py`
- `tests/unit/test_renderer.py`
- `tests/integration/test_fake_backend.py`
