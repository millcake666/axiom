# axiom-fastapi

`axiom-fastapi` — интеграционный пакет для FastAPI-приложений внутри экосистемы Axiom.

## Когда Использовать

Пакет полезен, если вам нужны:

- единый app factory;
- стандартные handlers для ошибок и validation;
- request logging middleware;
- ASGI error middleware;
- настраиваемые Swagger/ReDoc routes;
- thin wrapper над `uvicorn` и `gunicorn`.

## Что Уже Реализовано

- `AppConfig` и `create_app()`
- `register_all_handlers()`
- `RequestLoggingMiddleware`
- `ErrorMiddleware`
- `DocsConfig` и `include_docs_routes()`
- `UvicornSettings`, `run_uvicorn()`
- `GunicornSettings`, `run_gunicorn()` при установленном extra `gunicorn`

Текущий статус модуля `rate_limiter`:

- пакет существует;
- публичного рабочего API внутри него сейчас нет.

## Установка

```bash
uv add axiom-fastapi
uv add axiom-fastapi[gunicorn]
```

## Минимальный Пример

```python
from axiom.fastapi.app import AppConfig, create_app
from axiom.fastapi.middleware.logging import RequestLoggingMiddleware

app = create_app(
    AppConfig(
        title="Users API",
        version="0.1.0",
        description="Сервис на Axiom FastAPI",
    ),
)
app.add_middleware(RequestLoggingMiddleware)
```

## Public API

```python
from axiom.fastapi.app import AppConfig, create_app
from axiom.fastapi.docs import DocsConfig, include_docs_routes
from axiom.fastapi.exception_handler import register_all_handlers
from axiom.fastapi.middleware.error import ErrorMiddleware
from axiom.fastapi.middleware.logging import RequestLoggingMiddleware
from axiom.fastapi.runner import GunicornSettings, UvicornSettings, run_uvicorn
```

## Конфигурация

`AppConfig` поддерживает:

- `title`, `version`, `description`
- `pyproject_path` для автозаполнения metadata через `ProjectInfo`
- `docs_url`, `redoc_url`, `openapi_url`
- `middleware`
- `exception_handlers`
- `register_default_handlers`
- `docs_config`

## Интеграция С Другими Пакетами

- с `axiom-core`: ошибки, context, project metadata;
- с `axiom-sqlalchemy`: middleware session scope и integrity handler можно подключать отдельно;
- с вашим приложением: пакет не генерирует endpoints и не скрывает FastAPI, а только собирает общие куски.

## Ограничения И Текущий Статус

- `rate_limiter` пока не реализован.
- Логирование внутри пакета сейчас построено на `structlog`, а не на `axiom.core.logger`.
- `run_gunicorn()` зависит от наличия `gunicorn`; без extra рабочий сценарий — `run_uvicorn()` или обычный запуск FastAPI через uvicorn.
- Связка `AppConfig.docs_config` + `create_app()` выглядит незавершенной: `include_docs_routes()` опирается на `app.docs_url` / `app.redoc_url`, а `create_app()` при `docs_config` передает их как `None`. Это лучше считать участком, который требует уточнения перед production-использованием.

## Связанный Код

- `src/axiom/fastapi/app/`
- `src/axiom/fastapi/docs/`
- `src/axiom/fastapi/exception_handler/`
- `src/axiom/fastapi/middleware/`
- `tests/test_app_builder.py`
- `tests/test_exception_handlers.py`
- `tests/test_middleware_logging.py`
