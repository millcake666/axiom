# Axiom

Axiom — plugin-based Python-монорепа с набором независимых библиотек под общим namespace `axiom.*`.
Пакеты можно использовать по отдельности или собирать в более крупную backend/platform-композицию.

Главная идея проекта сейчас такая:

- `axiom-core` дает общее ядро: настройки, ошибки, логирование, context vars, filter DSL и базовые схемы.
- Остальные пакеты подключаются поверх ядра и решают одну инфраструктурную задачу: HTTP, cache, Redis, email, object storage, OLTP-адаптеры.
- Единого runtime-registry для "плагинов" в коде нет. Плагинность здесь достигается через отдельные installable packages, общий namespace и общие абстракции.

## Что Уже Реализовано

| Пакет | Import namespace | Статус | Назначение |
|---|---|---|---|
| [`axiom-core`](./axiom-core/README.md) | `axiom.core` | рабочий | ядро: settings, logger, exceptions, context, filter, schema |
| [`axiom-fastapi`](./axiom-fastapi/README.md) | `axiom.fastapi` | рабочий, частично | FastAPI app factory, middleware, handlers, docs routes, runners |
| [`axiom-cache`](./axiom-cache/README.md) | `axiom.cache` | рабочий | cache-абстракции, in-memory и Redis backends, decorators |
| [`axiom-redis`](./axiom-redis/README.md) | `axiom.redis` | рабочий | sync/async Redis client wrapper и settings |
| [`axiom-email`](./axiom-email/README.md) | `axiom.email` | рабочий | email client, hooks, renderer, Yandex SMTP provider, testing backends |
| [`axiom-objectstore`](./axiom-objectstore/README.md) | `axiom.objectstore` | рабочий | local disk и S3 object store |
| [`axiom-sqlalchemy`](./oltp/axiom-sqlalchemy/README.md) | `axiom.oltp.sqlalchemy` | рабочий | SQLAlchemy repositories/controllers, filter DSL, middleware |
| [`axiom-beanie`](./oltp/axiom-beanie/README.md) | `axiom.oltp.beanie` | рабочий | Beanie/PyMongo repositories/controllers для MongoDB |
| [`axiom-auth`](./axiom-auth/README.md) | `axiom.auth` | заглушка | каркас auth/authorization-пакета без рабочей логики |
| [`axiom-queue`](./axiom-queue/README.md) | `axiom.queue` | заглушка | каркас очередей и stream/middleware-пакета |
| [`axiom-task`](./axiom-task/README.md) | `axiom.task` | заглушка | каркас background/scheduled task-пакета |
| [`axiom-clickhouse`](./olap/axiom-clickhouse/README.md) | `axiom.olap.clickhouse` | заглушка | заготовка OLAP-интеграции |
| [`axiom-opensearch`](./olap/axiom-opensearch/README.md) | `axiom.olap.opensearch` | заглушка | заготовка search/OLAP-интеграции |

## Архитектура На Высоком Уровне

```text
consumer application
    |
    +-- axiom.fastapi
    +-- axiom.cache ---- axiom.redis
    +-- axiom.email
    +-- axiom.objectstore
    +-- axiom.oltp.sqlalchemy
    +-- axiom.oltp.beanie
            |
            +-- axiom.core
```

Ключевые архитектурные принципы:

- Общий namespace. Все пакеты живут под `axiom.*` и собираются как PEP 420 namespace packages.
- Минимальная связанность. У большинства пакетов зависимость только на `axiom-core` и внешнюю библиотеку своей области.
- Общий словарь сущностей. Ошибки, фильтры, response schemas и настройки переиспользуются между пакетами.
- Выбор конкретного backend-а делается на уровне импортов и DI в приложении, а не через скрытую магию.

Отдельно важно:

- `examples/` сейчас содержит только markdown-описания сценариев. Готовых запускаемых примеров в репозитории пока нет.
- В `todo.md` есть планы на tracing, metrics, grpc, auth, очереди и другие плагины, но этих рабочих пакетов в текущем workspace нет.

## Быстрый Старт

Минимальная композиция для HTTP-сервиса на SQLite:

```bash
uv add axiom-core axiom-fastapi axiom-sqlalchemy[sqlite]
```

```python
from axiom.fastapi.app import AppConfig, create_app
from axiom.fastapi.middleware.logging import RequestLoggingMiddleware

app = create_app(
    AppConfig(
        title="Users API",
        version="0.1.0",
        description="Минимальный сервис на базе Axiom",
    ),
)
app.add_middleware(RequestLoggingMiddleware)
```

Если нужен самый маленький пример без HTTP, начните с `axiom-core` или `axiom-cache`:

```python
from axiom.cache.inmemory import AsyncInMemoryCache

cache = AsyncInMemoryCache()
await cache.set("health", {"ok": True}, ttl=30)
value = await cache.get("health")
```

Более прикладные сценарии вынесены в отдельные документы:

- [`docs/quickstart.md`](./docs/quickstart.md)
- [`docs/architecture.md`](./docs/architecture.md)
- [`docs/plugins.md`](./docs/plugins.md)
- [`docs/development.md`](./docs/development.md)

## Как Устроено Расширение Через Пакеты

Типовой путь расширения выглядит так:

1. Новый пакет добавляется как отдельный workspace member со своим `pyproject.toml`.
2. Код публикуется в `src/axiom/...` под общим namespace.
3. Пакет либо переиспользует абстракции `axiom-core`, либо вводит свои локальные протоколы/ABC.
4. README пакета документирует только реально существующий API и ограничения.
5. Тесты живут внутри самого пакета, а не в общем корне.

Это означает, что Axiom ближе к "набору совместимых инфраструктурных библиотек", чем к монолитному framework.

## Текущее Состояние Проекта

На текущий момент проект уже полезен для:

- базового FastAPI-сервиса с единым error handling и request logging;
- кэширования через in-memory и Redis;
- отправки email с hook/template abstraction;
- работы с local disk и S3-compatible object store;
- CRUD и filter-driven data access через SQLAlchemy или Beanie.

Что еще не стабилизировано:

- `axiom-auth`, `axiom-queue`, `axiom-task`, `axiom-clickhouse`, `axiom-opensearch` пока являются в основном namespace-заглушками;
- `axiom-fastapi.rate_limiter` пока не реализован;
- у `axiom-sqlalchemy` dialect-specific upsert реализован в `sqlite` и `postgres`, а базовый `AsyncSQLAlchemyRepository`/`SyncSQLAlchemyRepository` не должен рассматриваться как полноценный upsert backend;
- часть архитектурного замысла из `.planning/codebase` и `todo.md` опережает текущее состояние кода.

## Навигация По Документации

Общая документация:

- [`docs/quickstart.md`](./docs/quickstart.md)
- [`docs/architecture.md`](./docs/architecture.md)
- [`docs/plugins.md`](./docs/plugins.md)
- [`docs/development.md`](./docs/development.md)

Документация по пакетам:

- [`axiom-core`](./axiom-core/README.md)
- [`axiom-fastapi`](./axiom-fastapi/README.md)
- [`axiom-cache`](./axiom-cache/README.md)
- [`axiom-redis`](./axiom-redis/README.md)
- [`axiom-email`](./axiom-email/README.md)
- [`axiom-objectstore`](./axiom-objectstore/README.md)
- [`axiom-sqlalchemy`](./oltp/axiom-sqlalchemy/README.md)
- [`axiom-beanie`](./oltp/axiom-beanie/README.md)
- [`axiom-auth`](./axiom-auth/README.md)
- [`axiom-queue`](./axiom-queue/README.md)
- [`axiom-task`](./axiom-task/README.md)
- [`axiom-clickhouse`](./olap/axiom-clickhouse/README.md)
- [`axiom-opensearch`](./olap/axiom-opensearch/README.md)

Материалы по архитектурным сценариям:

- [`examples/README.md`](./examples/README.md)
