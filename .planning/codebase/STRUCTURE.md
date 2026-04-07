# Codebase Structure

**Analysis Date:** 2026-04-07

## Directory Layout

```
axiom/                              # Repository root
├── pyproject.toml                  # UV workspace root; dev tooling (ruff, mypy, pytest)
├── uv.lock                         # Workspace lockfile
├── Makefile                        # Developer commands (sync, lint, format, test, check-types)
├── mypy.ini                        # Mypy configuration
├── scripts/                        # Helper scripts (check_types.py, etc.)
├── tasks/                          # PRD task documents (.md files)
├── examples/
│   ├── crud/                       # Example: endpoint→controller→repository pattern
│   └── ddd/                        # Example: endpoint→controller→usecase→repository pattern
│
├── axiom-core/                     # Foundation package
│   └── src/axiom/core/
│       ├── context/                # ContextVar-based request context
│       ├── entities/               # BaseDomainDC, BaseSchema, BaseRequestSchema, BaseResponseSchema
│       ├── exceptions/             # BaseError, ErrorDetail, HTTP exception types
│       ├── filter/                 # FilterRequest, FilterParam, FilterGroup query DSL
│       ├── logger/                 # configure_logger(), get_logger() (loguru)
│       ├── project/                # ProjectInfo (reads pyproject.toml metadata)
│       ├── schema/                 # PaginationResponse, CountResponse
│       └── settings/               # BaseAppSettings, AppMixin, DebugMixin, make_env_prefix()
│
├── axiom-fastapi/                  # FastAPI integration package
│   └── src/axiom/fastapi/
│       ├── app/                    # create_app(), AppConfig
│       ├── docs/                   # Custom docs routes
│       ├── exception_handler/      # register_all_handlers(), domain/http/validation/unhandled handlers
│       ├── middleware/
│       │   ├── error/              # ErrorMiddleware (last-resort ASGI catch-all)
│       │   └── logging/            # RequestLoggingMiddleware
│       ├── rate_limiter/           # Rate limiting (stub)
│       └── runner/                 # run_uvicorn(), Gunicorn runner
│
├── axiom-auth/                     # Authentication & authorization
│   └── src/axiom/auth/
│       ├── basic/                  # HTTP Basic auth
│       ├── classic/                # Classic session/cookie auth
│       ├── token/                  # API token auth
│       ├── oauth2/
│       │   └── keycloak/           # Keycloak OAuth2 provider
│       ├── rbac/                   # Role-based access control
│       └── abac/                   # Attribute-based access control
│
├── axiom-cache/                    # Caching abstractions
│   └── src/axiom/cache/
│       ├── base/                   # AsyncCacheBackend, SyncCacheBackend ABCs
│       ├── inmemory/               # AsyncInMemoryCache, SyncInMemoryCache
│       ├── redis/                  # AsyncRedisCache, SyncRedisCache
│       ├── decorators/             # @cached, @invalidate
│       ├── key_maker/              # KeyMaker, FunctionKeyMaker
│       ├── serialization/          # SerializationStrategy, get_serializer()
│       ├── manager.py              # CacheManager
│       ├── schemas.py              # CacheInvalidateParams, ConvertParam
│       └── ttl.py                  # TTL helper
│
├── axiom-redis/                    # Low-level Redis client
│   └── src/axiom/redis/
│       ├── async_client.py         # AsyncRedisClient, create_async_redis_client()
│       ├── sync_client.py          # SyncRedisClient, create_sync_redis_client()
│       └── settings.py             # RedisSettings
│
├── axiom-email/                    # Email client with plugin backends
│   └── src/axiom/email/
│       ├── client.py               # AsyncMailClient, SyncMailClient
│       ├── interfaces.py           # Protocol: AsyncMailBackend, SyncMailBackend, TemplateRenderer, MailHook
│       ├── models.py               # EmailMessage, SendResult, EmailAddress, Attachment
│       ├── providers/
│       │   └── yandex/             # YandexAsyncSMTPBackend, YandexSMTPConfig
│       ├── hooks/                  # LoggingHook
│       ├── templating/             # JinjaTemplateRenderer
│       └── testing/                # AsyncInMemoryMailBackend (test double)
│
├── axiom-objectstore/              # Object/file storage
│   └── src/axiom/objectstore/
│       ├── abs/                    # AbstractAsyncObjectStore, AbstractSyncObjectStore
│       ├── s3/                     # AsyncS3ObjectStore, SyncS3ObjectStore, S3Config, S3Settings
│       └── local/                  # AsyncLocalDiskObjectStore, SyncLocalDiskObjectStore, LocalDiskConfig
│
├── axiom-queue/                    # Message queue abstractions
│   └── src/axiom/queue/
│       ├── rabbitmq/               # RabbitMQ backend
│       ├── redis_stream/           # Redis Streams backend
│       ├── kafka/                  # Kafka backend
│       └── middleware/
│           ├── logging/            # Queue message logging middleware
│           └── tracing/            # Queue message tracing middleware
│
├── axiom-task/                     # Distributed task queue integrations
│   └── src/axiom/task/
│       ├── celery/                 # Celery integration
│       ├── arq/                    # ARQ (asyncio task queue) integration
│       └── middleware/
│           ├── logging/            # Task logging middleware
│           └── tracing/            # Task tracing middleware
│
├── oltp/                           # OLTP data access packages (namespace: axiom.oltp.*)
│   ├── axiom-sqlalchemy/           # SQLAlchemy integration
│   │   └── src/axiom/oltp/sqlalchemy/
│   │       ├── abs/
│   │       │   ├── repository/     # AsyncBaseRepository, SyncBaseRepository (ABC)
│   │       │   └── controller/     # AsyncBaseController, SyncBaseController (ABC)
│   │       ├── base/
│   │       │   ├── repository/     # AsyncSQLAlchemyRepository, SyncSQLAlchemyRepository
│   │       │   ├── controller/     # AsyncSQLAlchemyController, SyncSQLAlchemyController
│   │       │   ├── filter/         # SQLAlchemy FilterRequest translation
│   │       │   ├── mixin/          # TimestampMixin, AsDictMixin
│   │       │   ├── schema/         # Base schema helpers
│   │       │   └── declarative.py  # Base, to_snake()
│   │       ├── postgres/
│   │       │   ├── repository/     # AsyncPostgresRepository, SyncPostgresRepository
│   │       │   ├── controller/     # AsyncPostgresController, SyncPostgresController
│   │       │   ├── context.py      # session_context ContextVar helpers
│   │       │   └── session.py      # RoutingSession (read/write routing)
│   │       ├── sqlite/
│   │       │   ├── repository/     # AsyncSQLiteRepository, SyncSQLiteRepository
│   │       │   └── controller/     # AsyncSQLiteController, SyncSQLiteController
│   │       ├── middleware/         # SQLAlchemy ASGI middleware
│   │       └── exception_handler/  # SQLAlchemy-specific exception handlers
│   │
│   └── axiom-beanie/               # Beanie MongoDB ODM integration
│       └── src/axiom/oltp/beanie/
│           ├── abs/
│           │   ├── repository/     # AsyncBaseRepository, SyncBaseRepository (ABC)
│           │   └── controller/     # AsyncBaseController, SyncBaseController (ABC)
│           └── base/
│               ├── repository/     # AsyncBeanieRepository, SyncMongoRepository
│               ├── controller/     # AsyncBeanieController, SyncMongoController
│               ├── document.py     # SyncDocument base
│               └── mixin/          # TimestampMixin
│
└── olap/                           # OLAP analytical packages (namespace: axiom.olap.*)
    ├── axiom-clickhouse/           # ClickHouse integration
    │   └── src/axiom/olap/clickhouse/
    └── axiom-opensearch/           # OpenSearch integration
        └── src/axiom/olap/opensearch/
```

## Directory Purposes

**`axiom-core/`:**
- Purpose: The only required dependency; all other packages depend on it
- Contains: Settings base classes, domain entity base class, exception hierarchy, filter DSL, request context, logger configuration, Pydantic schema bases, response schemas
- Key files: `axiom-core/src/axiom/core/exceptions/base.py`, `axiom-core/src/axiom/core/entities/domain.py`, `axiom-core/src/axiom/core/settings/base.py`, `axiom-core/src/axiom/core/filter/expr.py`

**`axiom-fastapi/`:**
- Purpose: FastAPI application factory and opinionated wiring; used by any axiom-based HTTP service
- Contains: `create_app()`, `AppConfig`, middleware, exception handlers, ASGI runners
- Key files: `axiom-fastapi/src/axiom/fastapi/app/builder.py`, `axiom-fastapi/src/axiom/fastapi/app/config.py`, `axiom-fastapi/src/axiom/fastapi/exception_handler/__init__.py`

**`oltp/axiom-sqlalchemy/`:**
- Purpose: Primary relational database access layer; provides the Repository + Controller pattern for SQLAlchemy
- Contains: Abstract generics, concrete implementations for Postgres and SQLite, `@transactional` decorator, `RoutingSession`
- Key files: `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/repository/async_.py`, `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/controller/async_.py`, `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/__init__.py`

**`oltp/axiom-beanie/`:**
- Purpose: MongoDB data access layer mirroring the SQLAlchemy Repository + Controller pattern
- Key files: `oltp/axiom-beanie/src/axiom/oltp/beanie/__init__.py`

**`axiom-email/`:**
- Purpose: Email sending with swappable backends and hooks; `testing/` sub-package provides test doubles
- Key files: `axiom-email/src/axiom/email/interfaces.py`, `axiom-email/src/axiom/email/client.py`

**`examples/`:**
- Purpose: Reference implementations showing correct usage patterns; not production code
- Contains: `crud/` (3-layer: endpoint→controller→repository) and `ddd/` (4-layer: endpoint→controller→usecase→repository)

**`tasks/`:**
- Purpose: PRD/specification markdown files for features; developer planning artifacts
- Not runtime code; not committed as part of any package

**`.planning/codebase/`:**
- Purpose: AI-generated analysis documents for context loading
- Generated: Yes
- Committed: Yes

## Key File Locations

**Entry Points:**
- `axiom-fastapi/src/axiom/fastapi/app/builder.py`: `create_app(config)` — the application factory
- `axiom-fastapi/src/axiom/fastapi/runner/uvicorn.py`: `run_uvicorn()` — ASGI server startup
- `axiom-fastapi/src/axiom/fastapi/runner/gunicorn.py`: Gunicorn multi-worker startup

**Configuration:**
- `pyproject.toml`: Workspace root; ruff, mypy, pytest config shared across all packages
- `axiom-core/src/axiom/core/settings/base.py`: `BaseAppSettings`, composable `AppMixin`/`DebugMixin`
- Each package has its own `{package}/pyproject.toml` declaring local dependencies

**Core Logic:**
- `axiom-core/src/axiom/core/exceptions/base.py`: `BaseError`, `ErrorDetail`
- `axiom-core/src/axiom/core/filter/expr.py`: `FilterRequest`, `FilterParam`, `FilterGroup`
- `axiom-core/src/axiom/core/context/request.py`: `RequestContext`, `REQUEST_CONTEXT`, `set_request_context()`
- `axiom-core/src/axiom/core/logger/core.py`: `configure_logger()`, `get_logger()`
- `axiom-core/src/axiom/core/schema/response.py`: `PaginationResponse[T]`, `CountResponse`
- `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/repository/async_.py`: `AsyncBaseRepository` ABC
- `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/controller/async_.py`: `AsyncBaseController` ABC

**Testing:**
- Each package has a `tests/` directory at its package root (e.g., `axiom-cache/tests/`, `oltp/axiom-sqlalchemy/tests/`)
- `axiom-email/tests/unit/` and `axiom-email/tests/integration/` — split by test type
- `oltp/axiom-sqlalchemy/tests/fixtures/` — shared pytest fixtures

## Namespace Conventions

**Python namespace packages:**
- `src/axiom/` — implicit namespace package: **no `__init__.py`** at this level in any package
- `src/axiom/oltp/` — implicit namespace package: **no `__init__.py`**
- `src/axiom/olap/` — implicit namespace package: **no `__init__.py`**
- Each `src/axiom/{module}/__init__.py` sets `__version__ = "0.1.0"` and optional re-exports

**Package wheel build:**
Every `pyproject.toml` sets:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/axiom"]
```
This causes hatchling to publish the entire `src/axiom/` tree under the `axiom` namespace.

## Naming Conventions

**Files:**
- `snake_case.py` for all Python modules
- `async_.py` for async variants (avoids shadowing `async` keyword), `sync.py` for sync
- `__init__.py` in every sub-package re-exports the public API with explicit `__all__`

**Directories:**
- `snake_case` for sub-package directories
- `exception/` (singular) sub-package in every package/sub-package for scoped exceptions
- `abs/` for abstract base classes, `base/` for concrete base implementations

**Classes:**
- `Async{Name}` / `Sync{Name}` prefix for async/sync variants (e.g., `AsyncBaseRepository`, `SyncPostgresController`)
- `Base{Name}` for abstract base classes (e.g., `BaseError`, `BaseDomainDC`, `BaseAppSettings`)
- `{Name}Mixin` for composable mixin classes (e.g., `TimestampMixin`, `AsDictMixin`, `AppMixin`)
- `{Name}Settings` for Pydantic settings models (e.g., `RedisSettings`, `UvicornSettings`)
- `{Name}Config` for Pydantic configuration models (e.g., `AppConfig`, `S3Config`)

**Package names:**
- Singular: `axiom-metric` not `axiom-metrics`, `axiom-task` not `axiom-tasks`
- Hyphenated distribution names: `axiom-{module}`
- Import namespace: `axiom.{module}` (e.g., `from axiom.cache import AsyncRedisCache`)

## Where to Add New Code

**New top-level plugin package (e.g., `axiom-vault`):**
- Create `axiom-vault/src/axiom/vault/__init__.py` (with `__version__` and re-exports)
- Create `axiom-vault/pyproject.toml` with `[tool.hatch.build.targets.wheel] packages = ["src/axiom"]`
- Add `"axiom-vault"` to `[tool.uv.workspace] members` in root `pyproject.toml`
- Create `axiom-vault/tests/` directory
- Add `exception/` sub-package inside `axiom-vault/src/axiom/vault/`

**New sub-package within existing package (e.g., new auth provider):**
- Create directory: `axiom-auth/src/axiom/auth/{provider}/`
- Add `__init__.py` with docstring `"""axiom.auth.{provider} — ..."""`
- Add `exception/` sub-package: `axiom-auth/src/axiom/auth/{provider}/exception/__init__.py`

**New OLTP data backend:**
- Create `oltp/axiom-{backend}/src/axiom/oltp/{backend}/`
- Implement `abs/repository/` and `abs/controller/` extending the abstract bases from `axiom-core`
- Mirror the existing pattern: `abs/` (pure ABCs) → `base/` (concrete defaults) → `{dialect}/` (backend-specific)

**New OLAP data backend:**
- Create `olap/axiom-{backend}/src/axiom/olap/{backend}/`

**New email backend (provider):**
- Create `axiom-email/src/axiom/email/providers/{name}/`
- Implement `AsyncMailBackend` or `SyncMailBackend` Protocol from `axiom-email/src/axiom/email/interfaces.py`

**Utilities / helpers:**
- Shared domain utilities → `axiom-core/src/axiom/core/`
- Package-scoped utilities → inside the relevant package's `src/axiom/{module}/`

**Tests:**
- Co-locate with package: `{package-dir}/tests/`
- Split unit/integration when needed: `tests/unit/`, `tests/integration/`
- Shared fixtures: `tests/fixtures/`

## Special Directories

**`tasks/`:**
- Purpose: PRD markdown specification files used during development planning
- Generated: No (human-written)
- Committed: Yes (but not part of any installable package)

**`.planning/`:**
- Purpose: AI analysis and planning documents for GSD workflow
- Generated: Yes
- Committed: Yes

**`.beads/`:**
- Purpose: Dolt-based data store for the Beads project tracking system
- Generated: Yes (managed by beads tooling)
- Committed: Partially (Dolt database files)

**`{package}/.ruff_cache/`:**
- Purpose: Ruff linter cache per package
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-04-07*
