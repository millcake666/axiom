# Обзор Плагинов Axiom

## Рабочие Пакеты

| Пакет | Namespace | Зрелость | Ключевой public API | Документация |
|---|---|---|---|---|
| `axiom-core` | `axiom.core` | высокая | `BaseAppSettings`, `BaseError`, `FilterRequest`, `configure_logger` | [`axiom-core/README.md`](../axiom-core/README.md) |
| `axiom-fastapi` | `axiom.fastapi` | средняя/высокая | `AppConfig`, `create_app`, `RequestLoggingMiddleware`, `rate_limit`, `RateLimitMiddleware`, `run_uvicorn` | [`axiom-fastapi/README.md`](../axiom-fastapi/README.md) |
| `axiom-cache` | `axiom.cache` | высокая | `AsyncInMemoryCache`, `AsyncRedisCache`, `cached`, `invalidate`, `CacheManager` | [`axiom-cache/README.md`](../axiom-cache/README.md) |
| `axiom-redis` | `axiom.redis` | высокая | `AsyncRedisClient`, `SyncRedisClient`, `RedisSettings`, factory functions | [`axiom-redis/README.md`](../axiom-redis/README.md) |
| `axiom-email` | `axiom.email` | высокая | `AsyncMailClient`, `SyncMailClient`, `JinjaTemplateRenderer`, `LoggingHook` | [`axiom-email/README.md`](../axiom-email/README.md) |
| `axiom-objectstore` | `axiom.objectstore` | высокая | `AsyncLocalDiskObjectStore`, `AsyncS3ObjectStore`, `S3Config`, `LocalDiskConfig` | [`axiom-objectstore/README.md`](../axiom-objectstore/README.md) |
| `axiom-sqlalchemy` | `axiom.oltp.sqlalchemy` | высокая | `Base`, `TimestampMixin`, `AsyncSQLiteRepository`, `AsyncSQLAlchemyController` | [`oltp/axiom-sqlalchemy/README.md`](../oltp/axiom-sqlalchemy/README.md) |
| `axiom-beanie` | `axiom.oltp.beanie` | высокая | `AsyncBeanieRepository`, `AsyncBeanieController`, `SyncMongoRepository` | [`oltp/axiom-beanie/README.md`](../oltp/axiom-beanie/README.md) |

## Пакеты-Заглушки

| Пакет | Namespace | Что есть в коде сейчас | Документация |
|---|---|---|---|
| `axiom-auth` | `axiom.auth` | только package skeleton: `basic`, `classic`, `token`, `oauth2`, `rbac`, `abac` | [`axiom-auth/README.md`](../axiom-auth/README.md) |
| `axiom-queue` | `axiom.queue` | только namespace-заготовка backend-ов и middleware | [`axiom-queue/README.md`](../axiom-queue/README.md) |
| `axiom-task` | `axiom.task` | только namespace-заготовка backend-ов и middleware | [`axiom-task/README.md`](../axiom-task/README.md) |
| `axiom-clickhouse` | `axiom.olap.clickhouse` | только package shell | [`olap/axiom-clickhouse/README.md`](../olap/axiom-clickhouse/README.md) |
| `axiom-opensearch` | `axiom.olap.opensearch` | только package shell | [`olap/axiom-opensearch/README.md`](../olap/axiom-opensearch/README.md) |

## Как Выбирать Пакет

### Если нужен HTTP-слой

- берите `axiom-fastapi`, если нужен app factory, middleware и стандартные handlers;
- подключайте `axiom-fastapi[rate-limiter]`, если нужен встроенный rate limiter;
- для distributed-limit сценариев используйте Redis backend, а не in-memory backend.

### Если нужен cache

- `axiom-cache` для декораторов и единых cache backends;
- `axiom-redis`, если нужен low-level Redis client без decorator layer.

### Если нужен data access

- `axiom-sqlalchemy`, если проект уже на SQLAlchemy или нужна relational DB;
- `axiom-beanie`, если основной storage — MongoDB/Beanie;
- использовать оба пакета в одной монорепе можно, но в одном bounded context лучше не смешивать разные persistence styles без явной причины.

### Если нужен file/object storage

- `axiom-objectstore` для local disk и S3-compatible storage;
- если нужен presigned URL, используйте S3 backend, а не общий abstract interface.

### Если нужен email

- `axiom-email` уже дает рабочий client layer, hooks, renderer и testing backends;
- реальный SMTP provider в коде сейчас один: Yandex.

## Что Еще Требует Уточнения

- В проекте виден замысел на более широкий набор плагинов, чем реально реализовано.
- Для нового разработчика безопасно считать "production-ready" только те пакеты, у которых есть и код, и тесты, и README с примерами.
- Для stub-пакетов эта страница сознательно не пытается угадать будущий API.
