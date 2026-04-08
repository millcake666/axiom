# Архитектура Axiom

## Что Это За Архитектура

Axiom — это не один framework и не одна прикладная платформа, а набор совместимых библиотек.
Плагины в Axiom не регистрируются централизованно во время запуска приложения. Вместо этого проект устроен как monorepo из installable packages под общим namespace `axiom.*`.

Практический смысл такой схемы:

- можно взять только `axiom-core` и не тянуть остальную инфраструктуру;
- можно подключить `axiom-fastapi` с app factory, handlers и rate limiter, но не использовать MongoDB или S3;
- можно использовать `axiom-cache` отдельно от `axiom-fastapi`;
- можно держать несколько data adapters (`sqlalchemy`, `beanie`) рядом, но не смешивать их в одном сервисе.

## Слои

### 1. Ядро

`axiom-core` — обязательная база для остальных пакетов.

Что лежит в ядре:

- `settings`: `BaseAppSettings`, `AppMixin`, `DebugMixin`
- `exceptions`: `BaseError`, HTTP-aware subclasses, `ErrorDetail`
- `context`: `TypedContextVar`, `RequestContext`, `REQUEST_CONTEXT`
- `filter`: `FilterParam`, `FilterGroup`, `FilterRequest`, `QueryOperator`
- `logger`: `configure_logger`, `get_logger`, `LoggerSettings`
- `schema`: `PaginationResponse`, `CountResponse`
- `entities`: `BaseDomainDC`, `BaseSchema`, `BaseRequestSchema`, `BaseResponseSchema`
- `project`: `ProjectInfo` для чтения metadata из `pyproject.toml`

### 2. Интеграционные плагины

Пакеты этого слоя решают одну инфраструктурную задачу и по возможности не навязывают остальным свое устройство:

- `axiom-fastapi` (app factory, middleware, exception handlers, docs routes, runners, rate limiting)
- `axiom-cache`
- `axiom-redis`
- `axiom-email`
- `axiom-objectstore`

### 3. Data adapters

Это адаптеры к конкретным persistent backends, но со схожим стилем API:

- `axiom.oltp.sqlalchemy`
- `axiom.oltp.beanie`

Общий паттерн здесь один и тот же:

- repository отвечает за CRUD/query operations;
- controller добавляет transaction/pagination/error semantics;
- `axiom-core.filter` дает общий DSL для фильтрации;
- `axiom-core.schema` дает общий формат пагинации и count-ответов.

## Карта Зависимостей

```text
axiom-core
├── axiom-fastapi
├── axiom-redis
│   └── axiom-cache
├── axiom-email
├── axiom-objectstore
├── axiom-auth           (пока каркас)
├── axiom-queue          (пока каркас)
├── axiom-task           (пока каркас)
├── axiom.oltp.sqlalchemy
└── axiom.oltp.beanie
```

Практическое следствие:

- изменения в `axiom-core` потенциально затрагивают почти весь workspace;
- documentation drift особенно опасен в `core`, `sqlalchemy`, `beanie`, `fastapi`;
- зрелые пакеты уже можно использовать отдельно, но они все еще разделяют общий vocabulary проекта.

## Публичные Точки Расширения

### Core-level

- новые settings mixins поверх `BaseAppSettings`
- свои exception classes на базе `BaseError`
- собственные filter builders поверх `FilterParam`/`FilterGroup`

### Cache

- кастомные backend-реализации через `AsyncCacheBackend` / `SyncCacheBackend`
- кастомные key makers через `KeyMaker`
- кастомные serializers через `SerializationStrategy`

### Email

- backend-реализации через `AsyncMailBackend` / `SyncMailBackend`
- renderers через `TemplateRenderer`
- hooks через `MailHook`

### Object Store

- object store backends через `AbstractAsyncObjectStore` / `AbstractSyncObjectStore`

### SQLAlchemy / Beanie

- свои model/document classes
- свои repository subclasses
- свои controller subclasses с другим transaction lifecycle

## Как Идет Поток Данных

### HTTP-сервис на FastAPI + SQLAlchemy

Типовой поток:

1. `create_app(AppConfig)` создает FastAPI app.
2. `RequestLoggingMiddleware` добавляет `request_id` и пишет request/response logs.
3. При подключенном `RateLimitMiddleware` или `rate_limit()` dependency `RateLimiterService` проверяет квоты через `app.state`.
4. `ErrorMiddleware` ловит необработанные исключения.
5. endpoint вызывает controller.
6. controller делегирует repository.
7. repository применяет `FilterRequest` и делает запрос к БД.
8. controller оборачивает список в `PaginationResponse` или поднимает `NotFoundError`.
9. handlers сериализуют `BaseError` в `ErrorDetail`.

### Data access

Для `sqlalchemy` и `beanie` общий внешний стиль похож:

- `create`, `create_many`
- `get_by`, `get_by_filters`, `get_all`, `count`
- `update`, `update_by`, `update_by_filters`
- `delete`, `delete_by`, `delete_by_filters`
- `create_or_update`, `create_or_update_by`, `create_or_update_many`

Но реализация backend-specific:

- `axiom-sqlalchemy` работает через SQLAlchemy sessions и dialect-specific upsert;
- `axiom-beanie` async-ветка работает через Beanie, sync-ветка — через PyMongo + `SyncDocument`.

## Архитектурно Задумано И Что Реализовано Сейчас

По `.planning/codebase` и `todo.md` видно более широкий замысел: tracing, metrics, auth, tasks, queues, OLAP, grpc и т.д.
В текущем коде это состояние дел:

- реализованы: core, fastapi, cache, redis, email, objectstore, sqlalchemy, beanie;
- пока только каркас: auth, queue, task, clickhouse, opensearch.

Если `.planning/codebase` конфликтует с реальным кодом, для использования библиотеки нужно ориентироваться на код.
В документации проекта это считается приоритетом.

## Нужные Уточнения

- `examples/` пока не соответствуют описанию "reference applications" и служат скорее набросками структуры.
- `axiom-fastapi.rate_limiter` реализован, но in-memory backend подходит только для single-process сценариев; для distributed usage нужен Redis backend.
- `axiom-fastapi` использует `structlog`, тогда как `axiom-core` использует `loguru`; это стоит учитывать при общей log strategy.
- В `axiom-sqlalchemy` базовые репозитории экспортируются публично, но upsert по-настоящему реализован в `sqlite`/`postgres` репозиториях.
