# Architecture

**Analysis Date:** 2026-04-07

## Pattern Overview

**Overall:** Plugin Library / Framework Toolkit — UV monorepo of independently installable packages sharing a common `axiom.*` namespace.

**Key Characteristics:**
- Each package is an opt-in integration: consumers install only what they need (`axiom-core`, `axiom-fastapi`, `axiom-cache`, etc.)
- All packages are published under the PEP 420 implicit namespace `axiom.*` (no `__init__.py` at `src/axiom/`)
- Repository/Controller abstraction runs through all data-access packages — async and sync variants are first-class
- Cross-cutting concerns (exceptions, logging, context propagation) live in `axiom-core` and are referenced by every other package
- Each sub-package contains its own `exception/` sub-package with package-scoped error types

## Layers

**Foundation (axiom-core):**
- Purpose: Provides primitives shared across the entire framework
- Location: `axiom-core/src/axiom/core/`
- Contains: `BaseAppSettings` + mixins, `BaseError`/`ErrorDetail`, `BaseDomainDC` (UUID + timestamp dataclass), `RequestContext` (ContextVar-based), `FilterRequest`/`FilterParam`/`FilterGroup` query DSL, response schemas (`PaginationResponse`, `CountResponse`), logger (`loguru`), `ProjectInfo`
- Depends on: `loguru`, `pydantic`, `pydantic-settings`, `tomlkit`
- Used by: every other axiom package

**Web Framework Integration (axiom-fastapi):**
- Purpose: Wraps FastAPI with opinionated defaults — app factory, middleware, exception handlers, runners
- Location: `axiom-fastapi/src/axiom/fastapi/`
- Contains: `create_app(AppConfig)` factory, `AppConfig`, `ErrorMiddleware`, `RequestLoggingMiddleware`, `register_all_handlers()`, `UvicornSettings`/`run_uvicorn()`, Gunicorn runner, `rate_limiter/` package (stub)
- Depends on: `axiom-core`, `fastapi`, `uvicorn`, `structlog`, `tomlkit`
- Used by: application services built on top of this framework

**Authentication (axiom-auth):**
- Purpose: Multi-scheme authentication and RBAC/ABAC authorization
- Location: `axiom-auth/src/axiom/auth/`
- Sub-packages: `basic/`, `classic/`, `token/`, `oauth2/` (with `keycloak/` sub-package), `rbac/`, `abac/`
- Depends on: `axiom-core`
- Used by: application endpoints, middleware

**Caching (axiom-cache):**
- Purpose: Backend-agnostic caching with decorators
- Location: `axiom-cache/src/axiom/cache/`
- Contains: `AsyncCacheBackend`/`SyncCacheBackend` ABCs, `AsyncInMemoryCache`/`SyncInMemoryCache`, `AsyncRedisCache`/`SyncRedisCache`, `CacheManager`, `@cached`/`@invalidate` decorators, `KeyMaker`/`FunctionKeyMaker`, `TTL`, `SerializationStrategy`
- Depends on: `axiom-redis`
- Used by: application services needing caching

**Redis Client (axiom-redis):**
- Purpose: Low-level async/sync Redis client with settings
- Location: `axiom-redis/src/axiom/redis/`
- Contains: `AsyncRedisClient`, `SyncRedisClient`, factory functions, `RedisSettings`
- Depends on: `redis` (external)
- Used by: `axiom-cache`, direct Redis consumers

**Email (axiom-email):**
- Purpose: Framework-independent email client with backend/renderer/hook plugin architecture
- Location: `axiom-email/src/axiom/email/`
- Contains: `AsyncMailClient`/`SyncMailClient`, Protocol interfaces (`AsyncMailBackend`, `SyncMailBackend`, `TemplateRenderer`, `MailHook`), `EmailMessage`/`SendResult` models, `JinjaTemplateRenderer`, `LoggingHook`, SMTP providers (`yandex/`), `AsyncInMemoryMailBackend` (testing)
- Depends on: `axiom-core`, `aiosmtplib`, `jinja2`
- Used by: application services sending email

**Object Store (axiom-objectstore):**
- Purpose: File/object storage with local disk and S3 backends
- Location: `axiom-objectstore/src/axiom/objectstore/`
- Contains: `AbstractAsyncObjectStore`/`AbstractSyncObjectStore` ABCs, `AsyncS3ObjectStore`/`SyncS3ObjectStore`, `AsyncLocalDiskObjectStore`/`SyncLocalDiskObjectStore`, `S3Config`/`S3Settings`/`LocalDiskConfig`
- Depends on: `aiobotocore`/`botocore`
- Used by: file-handling application services

**Queue (axiom-queue):**
- Purpose: Message broker producer/consumer abstractions
- Location: `axiom-queue/src/axiom/queue/`
- Sub-packages: `rabbitmq/`, `redis_stream/`, `kafka/`, `middleware/` (with `logging/`, `tracing/` sub-packages)
- Depends on: broker-specific libraries
- Used by: event-driven application services

**Task (axiom-task):**
- Purpose: Distributed task queue integrations
- Location: `axiom-task/src/axiom/task/`
- Sub-packages: `celery/`, `arq/`, `middleware/` (with `logging/`, `tracing/` sub-packages)
- Depends on: `celery` or `arq`
- Used by: background task processing

**OLTP — SQLAlchemy (axiom.oltp.sqlalchemy):**
- Purpose: SQLAlchemy ORM repository/controller layer with Postgres and SQLite backends
- Location: `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/`
- Contains: `AsyncBaseRepository`/`SyncBaseRepository` (abstract, generic), `AsyncSQLAlchemyRepository`/`SyncSQLAlchemyRepository` (base implementation), `AsyncPostgresRepository`/`SyncPostgresRepository`, SQLite variants, `AsyncBaseController`/`SyncBaseController`, `Base` declarative base, `TimestampMixin`/`AsDictMixin`, `RoutingSession` (read/write routing), `FilterRequest` integration, `@transactional` decorator
- Depends on: `axiom-core`, `sqlalchemy`, `asyncpg`/`psycopg2`
- Used by: application data access layers targeting PostgreSQL or SQLite

**OLTP — Beanie (axiom.oltp.beanie):**
- Purpose: Beanie MongoDB ODM repository/controller layer
- Location: `oltp/axiom-beanie/src/axiom/oltp/beanie/`
- Contains: `AsyncBeanieRepository`/`SyncMongoRepository`, `AsyncBeanieController`/`SyncMongoController`, abstract base classes, `SyncDocument`, `TimestampMixin`
- Depends on: `axiom-core`, `beanie`, `motor`
- Used by: MongoDB-backed application data access layers

**OLAP — ClickHouse (axiom.olap.clickhouse):**
- Purpose: ClickHouse integration for analytical queries
- Location: `olap/axiom-clickhouse/src/axiom/olap/clickhouse/`
- Depends on: `clickhouse-driver` or `asynch`

**OLAP — OpenSearch (axiom.olap.opensearch):**
- Purpose: OpenSearch integration for full-text search and analytics
- Location: `olap/axiom-opensearch/src/axiom/olap/opensearch/`
- Depends on: `opensearch-py`

## Data Flow

**HTTP Request Lifecycle (using axiom-fastapi):**

1. Request arrives at Uvicorn/Gunicorn ASGI server
2. `ErrorMiddleware` wraps the entire request for last-resort error catching
3. `RequestLoggingMiddleware` logs request metadata, sets `RequestContext` (request_id, user, tenant) via `ContextVar`
4. FastAPI routes the request to the endpoint handler
5. Endpoint calls Controller methods (e.g., `AsyncPostgresController.get_by_id()`)
6. Controller delegates to Repository (e.g., `AsyncPostgresRepository`) which executes the database query
7. Repository returns ORM model; Controller wraps it in `PaginationResponse` or raises `NotFoundError`
8. FastAPI exception handlers (`register_all_handlers`) convert `BaseError` subclasses to structured JSON (`ErrorDetail`)
9. Response returns through middleware chain

**Repository→Controller Data Flow:**

1. API endpoint receives Pydantic request schema
2. `AsyncBaseController.extract_attributes_from_schema(schema)` converts it to a `dict[str, Any]`
3. Controller method (decorated with `@transactional`) calls `repository.create/update/delete(...)`
4. Repository builds and executes SQLAlchemy query within session transaction
5. Result returned as ORM model; controller raises `NotFoundError`/`UnprocessableError` on failures

**Filter Query Flow:**

1. Caller constructs `FilterRequest(chain=FilterParam(field=..., value=..., operator=...))` or uses `&`/`|` operators to build `FilterGroup`
2. Repository's `get_by_filters(filter_request)` processes the tree via `extract_filter_params()`
3. Repository's `_filter()` translates each `FilterParam` into a SQLAlchemy `WHERE` clause

**State Management:**
- No global mutable state; per-request state uses Python `contextvars.ContextVar` (`REQUEST_CONTEXT` in `axiom-core/src/axiom/core/context/request.py`)
- Settings loaded once from `.env` via `pydantic-settings` `BaseAppSettings`

## Key Abstractions

**BaseError:**
- Purpose: Root exception type for all domain errors; carries `code`, `status_code`, `message`, `details`
- Examples: `axiom-core/src/axiom/core/exceptions/base.py`
- Pattern: Subclass with class-level `code` and `status_code` overrides; converted to `ErrorDetail` for API responses

**BaseDomainDC:**
- Purpose: UUID-identified domain entity with UTC timestamps; equality/hash by `id`
- Examples: `axiom-core/src/axiom/core/entities/domain.py`
- Pattern: `@dataclass` inheritance; `to_dict()` / `from_dict()` for serialization

**BaseSchema / BaseRequestSchema / BaseResponseSchema:**
- Purpose: Typed Pydantic DTOs for API request/response payloads
- Examples: `axiom-core/src/axiom/core/entities/schema.py`
- Pattern: ORM-mode, alias population enabled; `BaseResponseSchema.model_response()` serializes with aliases

**AsyncBaseRepository[ModelType, SessionType, QueryType] / SyncBaseRepository:**
- Purpose: Generic CRUD + filter + pagination contract for data access
- Examples: `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/repository/async_.py`
- Pattern: ABC with abstract `_query()`, `_filter()`, `_paginate()`, `_sort_by()`, `_all()`, `_one_or_none()`; concrete methods (`get_by`, `get_by_filters`, `count`) are pre-implemented on the abstract class

**AsyncBaseController[ModelType] / SyncBaseController:**
- Purpose: Service layer sitting between endpoints and repositories; handles transactions, field exclusions, pagination wrapping
- Examples: `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/controller/async_.py`
- Pattern: `@transactional` decorator wraps mutations; `abstract processing_transaction()` implemented by concrete subclass (postgres/sqlite)

**FilterRequest / FilterParam / FilterGroup:**
- Purpose: Composable query filter DSL with `&`/`|` operators
- Examples: `axiom-core/src/axiom/core/filter/expr.py`
- Pattern: Pydantic discriminated union tree; `extract_filter_params()` flattens to list for ORM consumption

**Protocol-based email backends (AsyncMailBackend, SyncMailBackend, TemplateRenderer, MailHook):**
- Purpose: Structural subtyping for email provider/renderer/hook extensibility
- Examples: `axiom-email/src/axiom/email/interfaces.py`
- Pattern: `@runtime_checkable` `Protocol`; concrete implementations in `providers/` sub-packages

**AppConfig + create_app():**
- Purpose: Declarative FastAPI application configuration and factory
- Examples: `axiom-fastapi/src/axiom/fastapi/app/config.py`, `axiom-fastapi/src/axiom/fastapi/app/builder.py`
- Pattern: Pydantic model with `model_validator` to auto-fill metadata from `pyproject.toml`; `create_app(config)` wires middleware and exception handlers

## Entry Points

**ASGI Application Factory:**
- Location: `axiom-fastapi/src/axiom/fastapi/app/builder.py` → `create_app(config: AppConfig)`
- Triggers: Called by application service's own `main.py` / app module
- Responsibilities: Creates `FastAPI` instance, registers `ErrorMiddleware`, registers all exception handlers, optionally adds custom docs routes

**Uvicorn Runner:**
- Location: `axiom-fastapi/src/axiom/fastapi/runner/uvicorn.py` → `run_uvicorn(app, settings: UvicornSettings)`
- Triggers: Called from application `__main__` or startup script
- Responsibilities: Calls `uvicorn.run()` with configured host/port/workers/reload

**Gunicorn Runner:**
- Location: `axiom-fastapi/src/axiom/fastapi/runner/gunicorn.py`
- Triggers: Production deployments with gunicorn workers
- Responsibilities: Runs multiple uvicorn workers via gunicorn

## Error Handling

**Strategy:** Layered error taxonomy rooted at `BaseError`; all domain errors carry machine-readable `code` + HTTP `status_code`; FastAPI handlers convert them to JSON

**Patterns:**
- Domain errors: Subclass `axiom.core.exceptions.base.BaseError` with overridden `code`/`status_code` class attributes
- HTTP-level exceptions: `axiom.core.exceptions.http` defines `NotFoundError` (404), `UnprocessableError` (422), `ValidationError` (400), etc.
- FastAPI layer: `register_all_handlers()` in `axiom-fastapi/src/axiom/fastapi/exception_handler/__init__.py` registers handlers in order: domain → validation → http → unhandled
- Last resort: `ErrorMiddleware` (`axiom-fastapi/src/axiom/fastapi/middleware/error/`) catches any unhandled exceptions before they escape ASGI
- Each package maintains its own `exception/` sub-package extending the base hierarchy

## Cross-Cutting Concerns

**Logging:** `loguru`-based via `axiom-core/src/axiom/core/logger/core.py`; `configure_logger(settings)` configures sinks; `get_logger(name)` returns a bound logger; JSON format in non-dev stages, plain text in `dev`; `RequestLoggingMiddleware` logs per-request

**Validation:** `pydantic` v2 throughout; `BaseSchema`/`BaseRequestSchema`/`BaseResponseSchema` are the canonical DTO base classes; `FilterRequest` uses pydantic discriminated unions for query parameters

**Authentication:** Pluggable via `axiom-auth` sub-packages; no global auth middleware is pre-wired — consumers compose the appropriate scheme (basic, token, OAuth2/Keycloak, RBAC, ABAC)

---

*Architecture analysis: 2026-04-07*
