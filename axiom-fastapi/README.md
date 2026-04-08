# axiom-fastapi

`axiom-fastapi` — интеграционный пакет для FastAPI-приложений внутри экосистемы Axiom.

## Когда Использовать

Пакет полезен, если вам нужны:

- единый app factory;
- стандартные handlers для ошибок и validation;
- request logging middleware;
- ASGI error middleware;
- настраиваемые Swagger/ReDoc routes;
- rate limiting через middleware или per-route dependency;
- thin wrapper над `uvicorn` и `gunicorn`.

## Что Уже Реализовано

- `AppConfig` и `create_app()`
- `AppStateManager`
- `register_all_handlers()`
- `RequestLoggingMiddleware`
- `ErrorMiddleware`
- `DocsConfig` и `include_docs_routes()`
- `UvicornSettings`, `run_uvicorn()`
- `GunicornSettings`, `run_gunicorn()` при установленном extra `gunicorn`
- `axiom.fastapi.rate_limiter` с in-memory/Redis backend-ами, policy providers, middleware и dependency factory

## Установка

```bash
uv add axiom-fastapi
uv add axiom-fastapi[gunicorn]
uv add axiom-fastapi[rate-limiter]
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

## Минимальный Пример Rate Limiting

```python
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from axiom.fastapi.exception_handler import register_all_handlers
from axiom.fastapi.rate_limiter import (
    IPPolicy,
    RateLimitConfig,
    rate_limit,
    rate_limiter_lifespan,
)

config = RateLimitConfig(policies=[IPPolicy(limit="100/minute")])


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with rate_limiter_lifespan(app, config):
        yield


app = FastAPI(lifespan=lifespan)
register_all_handlers(app)


@app.get("/items", dependencies=[Depends(rate_limit("10/minute"))])
async def list_items() -> dict[str, list[object]]:
    return {"items": []}
```

Для multi-worker / multi-instance сценариев используйте Redis backend и extra `rate-limiter`.

## Public API

```python
from axiom.fastapi.app import AppConfig, AppStateManager, create_app
from axiom.fastapi.docs import DocsConfig, include_docs_routes
from axiom.fastapi.exception_handler import register_all_handlers
from axiom.fastapi.middleware.error import ErrorMiddleware
from axiom.fastapi.middleware.logging import RequestLoggingMiddleware
from axiom.fastapi.rate_limiter import (
    IPPolicy,
    RateLimitConfig,
    RateLimitMiddleware,
    RateLimiterService,
    RedisRateLimitBackend,
    rate_limit,
    rate_limiter_lifespan,
    setup_rate_limiter,
)
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

`RateLimitConfig` и `RateLimitSettings` поддерживают:

- включение и отключение limiter-а через `enabled` / `RATE_LIMIT_ENABLED`
- environment namespace через `env` / `RATE_LIMIT_ENV`
- `failure_strategy`, `key_prefix`, `exempt_paths`
- список policy для global middleware или dynamic provider

Backend wiring остается явным: для Redis backend-а нужно передать `redis_client` в `rate_limiter_lifespan()` или `setup_rate_limiter()`.

## Интеграция С Другими Пакетами

- с `axiom-core`: ошибки, project metadata, canonical logger, settings base classes;
- с `axiom-redis`: Redis backend для распределенного rate limiting;
- с `axiom.oltp.sqlalchemy` или любым async repository: `PostgresPolicyProvider` через `PolicyRepository`;
- с вашим приложением: пакет не генерирует endpoints и не скрывает FastAPI, а только собирает общие куски.

## Ограничения И Текущий Статус

- `InMemoryRateLimitBackend` подходит только для dev/test и single-process сценариев.
- Для distributed rate limiting нужен Redis backend и явный lifecycle `startup()` / `shutdown()` через `rate_limiter_lifespan()`.
- Global rate limiting через `RateLimitMiddleware` требует одного разделяемого `RateLimiterService`.
- Логирование внутри пакета сейчас частично построено на `structlog`, а не на `axiom.core.logger`.
- `run_gunicorn()` зависит от наличия `gunicorn`; без extra рабочий сценарий — `run_uvicorn()` или обычный запуск FastAPI через uvicorn.
- Связка `AppConfig.docs_config` + `create_app()` выглядит незавершенной: `include_docs_routes()` опирается на `app.docs_url` / `app.redoc_url`, а `create_app()` при `docs_config` передает их как `None`. Это лучше считать участком, который требует уточнения перед production-использованием.

## Связанный Код

- `src/axiom/fastapi/app/`
- `src/axiom/fastapi/docs/`
- `src/axiom/fastapi/exception_handler/`
- `src/axiom/fastapi/middleware/`
- `src/axiom/fastapi/rate_limiter/`
- `tests/test_app_builder.py`
- `tests/test_exception_handlers.py`
- `tests/test_middleware_logging.py`
- `tests/unit/rate_limiter/`
- `tests/integration/rate_limiter/`
