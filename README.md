# Axiom

A Python monorepo of composable packages for building production-grade services. All packages share the `axiom.*`
namespace and are designed to work independently or together.

**Package manager:** [uv](https://docs.astral.sh/uv/) · **Python:** 3.13+ · **Build system:** Hatchling

---

## Architecture

```
axiom/
├── axiom-core/              # Foundation — config, logger, exception, context, entity
├── axiom-fastapi/           # FastAPI base — middleware/, rate_limiter/ packages inside
│   ├── middleware/          #   cors, logging, tracing, auth middleware
│   └── rate_limiter/        #   rate limiting
│
├── axiom-auth/              # Auth — basic, email, api_token, oauth2/keycloak, abac, rbac
├── axiom-cache/             # Cache abstractions — InMemory + Redis backends
├── axiom-email/             # Email sending abstractions and backends
├── axiom-grpc/              # gRPC server and client plugin
│   └── middleware/          #   logging, tracing middleware
├── axiom-lock/              # Distributed locking with cascading lock support
├── axiom-metric/            # Metrics — prometheus, statsd backends
├── axiom-migration/         # Database migrations via Alembic
├── axiom-objectstore/       # Object/file storage — s3, local backends
│   ├── base/                #   base classes and client factory
│   ├── abs/                 #   abstract repository interfaces
│   ├── s3/                  #   S3-compatible storage via aiobotocore
│   └── local/               #   local disk storage
├── axiom-queue/             # Message queue — rabbitmq, redis_stream, kafka backends
│   └── middleware/          #   logging, tracing middleware
├── axiom-redis/             # Async Redis client and utilities
├── axiom-serialization/     # Data serialization and validation
├── axiom-task/              # Async task queue — celery, arq backends
│   └── middleware/          #   logging, tracing middleware
├── axiom-tracing/           # Distributed tracing — OpenTelemetry + Jaeger
├── axiom-vault/             # HashiCorp Vault secrets management
│
├── oltp/                    # Transactional data packages
│   ├── axiom-sqlalchemy/    # SQLAlchemy — base, abs, postgres, sqlite
│   ├── axiom-beanie/        # Beanie MongoDB ODM — base, abs
│   ├── axiom-audit/         # User action audit trail
│   └── axiom-history/       # DB state history and point-in-time reconstruction
│
└── olap/                    # Analytical data packages
    ├── axiom-clickhouse/    # ClickHouse integration
    └── axiom-opensearch/    # OpenSearch integration
```

---

## Packages

### Foundation

| Package         | Description                                                                                                     |
|-----------------|-----------------------------------------------------------------------------------------------------------------|
| `axiom-core`    | Foundation for all axiom.* packages. Modules: **config**, **logger**, **exception**, **context**, **entity**   |
| `axiom-fastapi` | Base for FastAPI applications. Packages: **middleware** (cors, logging, tracing, auth), **rate_limiter**        |
| `axiom-vault`   | HashiCorp Vault — secrets backend for `axiom.core.config`                                                       |

### Data Layer

| Package               | Sub-packages             | Description                                                      |
|-----------------------|--------------------------|------------------------------------------------------------------|
| `axiom-redis`         | —                        | Async Redis client and utilities                                 |
| `axiom-cache`         | `inmemory`, `redis`      | Cache abstractions — `InMemoryCache`, `RedisCache` backends      |
| `axiom-objectstore`   | `base`, `abs`, `s3`, `local` | Object and file storage — S3-compatible and local disk       |

### OLTP — Transactional (`oltp/`)

| Package            | Sub-packages                        | Description                                                     |
|--------------------|-------------------------------------|-----------------------------------------------------------------|
| `axiom-sqlalchemy` | `base`, `abs`, `postgres`, `sqlite` | SQLAlchemy ORM — declarative models, mixins, repository pattern |
| `axiom-beanie`     | `base`, `abs`                       | Beanie MongoDB ODM — document models, repositories              |
| `axiom-audit`      | —                                   | User action audit trail                                         |
| `axiom-history`    | —                                   | Full history tracking and point-in-time reconstruction          |

### OLAP — Analytical (`olap/`)

| Package            | Description                                                      |
|--------------------|------------------------------------------------------------------|
| `axiom-clickhouse` | ClickHouse integration for analytical queries and data ingestion |
| `axiom-opensearch` | OpenSearch integration for full-text search and analytics        |

### Messaging & Tasks

| Package       | Backends                            | Description                                 |
|---------------|-------------------------------------|---------------------------------------------|
| `axiom-task`  | `celery`, `arq`                     | Delayed and scheduled async task queue      |
| `axiom-queue` | `rabbitmq`, `redis_stream`, `kafka` | Event/message queue producer-consumer       |
| `axiom-email` | —                                   | Email sending with multiple backend support |

### Auth & Security

| Package      | Sub-packages                                                      | Description                                     |
|--------------|-------------------------------------------------------------------|-------------------------------------------------|
| `axiom-auth` | `basic`, `email`, `api_token`, `oauth2/keycloak`, `abac`, `rbac` | Multi-scheme auth and access control            |
| `axiom-lock` | —                                                                 | Distributed locking with cascading lock support |

### Observability

| Package         | Sub-packages           | Description                                    |
|-----------------|------------------------|------------------------------------------------|
| `axiom-metric`  | `prometheus`, `statsd` | Application metrics collection                 |
| `axiom-tracing` | —                      | Distributed tracing via OpenTelemetry + Jaeger |

### Infrastructure

| Package               | Description                                        |
|-----------------------|----------------------------------------------------|
| `axiom-migration`     | Database migrations via Alembic                    |
| `axiom-serialization` | Data serialization, validation, and transformation |
| `axiom-grpc`          | gRPC server and client plugin                      |

---

## Architectural Patterns

Axiom supports two primary patterns. See [`examples/`](./examples/) for runnable reference applications.

### 1. CRUD — Simple Repository Pattern

```
endpoint → controller → repository
```

Best for: straightforward CRUD, admin APIs, simple microservices.

### 2. DDD — Domain-Driven Design

```
endpoint → controller → use case → repository
```

Best for: complex business logic, domain-rich services, multi-aggregate operations.

---

## Business Layer

Axiom supports two approaches for the business/domain layer:

### 1. Dataclass Entities (framework-agnostic)

```python
from axiom.core.entity import AggregateRoot
from dataclasses import dataclass


@dataclass
class Order(AggregateRoot):
    customer_id: str
    total: float
```

Persist with `axiom-sqlalchemy` or `axiom-beanie` without coupling domain to ORM.

### 2. ORM Model Entities

```python
# SQLAlchemy (oltp/axiom-sqlalchemy)
from axiom.oltp.sqlalchemy.base import Base

class OrderModel(Base):
    __tablename__ = "order"
    ...

# Beanie (oltp/axiom-beanie)
from axiom.oltp.beanie.base import BaseDocument

class OrderDocument(BaseDocument):
    ...
```

---

## axiom-core Modules

```python
# Exceptions
from axiom.core.exception import AxiomError, NotFoundError, ValidationError

# Entities (dataclass base)
from axiom.core.entity import Entity, UUIDEntity, AggregateRoot

# Context (per-request ContextVars)
from axiom.core.context import request_id, user_id, trace_id, tenant_id

# Logging
from axiom.core.logger import get_logger, configure_logging

# Settings / Config
from axiom.core.config import BaseSettings
```

---

## axiom-core.config + axiom-vault

```python
from axiom.core.config import BaseSettings
from axiom.vault import VaultSettings


class AppSettings(BaseSettings):
    database_url: str
    secret_key: str


# With Vault as secrets backend
settings = AppSettings.from_vault(VaultSettings(addr="http://vault:8200"))
```

---

## Caching

```python
from axiom.cache.inmemory import InMemoryCache
from axiom.cache.redis import RedisCache
from axiom.redis import create_redis_client

cache = InMemoryCache()                                    # dev/test
cache = RedisCache(create_redis_client("redis://..."))     # production

await cache.set("key", "value", ttl=60)
value = await cache.get("key")
```

---

## Object Storage

```python
from axiom.objectstore.s3 import S3ObjectStore
from axiom.objectstore.local import LocalObjectStore

store = S3ObjectStore(bucket="my-bucket", region="us-east-1")
store = LocalObjectStore(root="/var/data")                 # dev/test

await store.put("uploads/file.pdf", data)
stream = await store.get("uploads/file.pdf")
```

---

## Metrics

```python
from axiom.metric.prometheus import PrometheusMetric
from axiom.metric.statsd import StatsDMetric
```

---

## Tracing

```python
from axiom.tracing import setup_tracing, get_tracer

setup_tracing(service_name="my-service", jaeger_host="jaeger:6831")
tracer = get_tracer(__name__)

with tracer.start_as_current_span("operation"):
    ...
```

---

## Auth

```python
from axiom.auth.basic import BasicAuthBackend
from axiom.auth.email import EmailPasswordBackend
from axiom.auth.api_token import ApiTokenBackend
from axiom.auth.oauth2 import OAuth2Backend
from axiom.auth.oauth2.keycloak import KeycloakBackend
from axiom.auth.abac import AbacPolicy
from axiom.auth.rbac import RbacPolicy
```

---

## Installation

```bash
# Foundation
uv add axiom-core

# FastAPI applications
uv add axiom-fastapi

# With SQLAlchemy + migrations
uv add axiom-sqlalchemy axiom-migration

# With Redis + caching
uv add axiom-redis axiom-cache

# Observability
uv add axiom-metric axiom-tracing

# Object storage
uv add axiom-objectstore

# Secrets management
uv add axiom-vault
```

---

## Development

```bash
git clone <repo>
uv sync --all-packages --all-groups

make lint            # ruff check
make format          # ruff format
make check-types     # mypy
uv run pytest        # tests
make check-precommit # all pre-commit hooks
```

---

## CI / CD

| Workflow        | Trigger                      | Jobs                                                       |
|-----------------|------------------------------|------------------------------------------------------------|
| `ci.yml`        | Push/PR to `main`            | Pre-commit hooks → Tests (Python 3.13) in sequence         |
| `auto-tag.yml`  | Push to `main`               | Read version from each `pyproject.toml`, create tag if new |
| `release.yml`   | Push tag `axiom-*-v*.*.*`    | Build package → GitHub Release                             |

Tags are per-package: `axiom-core-v1.0.0`, `axiom-sqlalchemy-v0.2.1`, etc.

---

## Workspace

```toml
[tool.uv.workspace]
members = ["axiom-*", "oltp/axiom-*", "olap/axiom-*"]
```

---

## Contributing

```bash
# Scaffold a new package
mkdir -p axiom-mypkg/src/axiom/mypkg
echo '"""axiom.mypkg — description."""' > axiom-mypkg/src/axiom/mypkg/__init__.py
# Add pyproject.toml — workspace picks it up via axiom-* glob
```

---

## Roadmap

### Core

- [ ] `axiom.core.entity` — base entity classes (`Entity`, `UUIDEntity`, `AggregateRoot`, `ValueObject`)
- [ ] `axiom.core.exception` — base exception hierarchy (`AxiomError`, `NotFoundError`, `ValidationError`, `ConflictError`)
- [ ] `axiom.core.context` — async context propagation via `contextvars` (request id, user id, trace id, tenant id)
- [ ] `axiom.core.logger` — structured JSON logging with context injection
- [ ] `axiom.core.config` — `BaseSettings` with env-file and Vault backend support

### FastAPI

- [ ] `axiom.fastapi.middleware.cors` — CORS middleware configuration
- [ ] `axiom.fastapi.middleware.logging` — structured request/response logging
- [ ] `axiom.fastapi.middleware.tracing` — OpenTelemetry span injection per request
- [ ] `axiom.fastapi.middleware.auth` — pluggable authentication middleware
- [ ] `axiom.fastapi.rate_limiter` — token-bucket / sliding-window rate limiting

### Data — OLTP

- [ ] `axiom.oltp.sqlalchemy.base` — declarative base, session factory, engine factory
- [ ] `axiom.oltp.sqlalchemy.abs` — abstract repository interface (`AbstractRepository[T]`)
- [ ] `axiom.oltp.sqlalchemy.postgres` — PostgreSQL-specific session and dialect config
- [ ] `axiom.oltp.sqlalchemy.sqlite` — SQLite session (testing / local dev)
- [ ] `axiom.oltp.beanie.base` — Beanie `BaseDocument` with common fields
- [ ] `axiom.oltp.beanie.abs` — abstract MongoDB repository interface
- [ ] `axiom.oltp.audit` — automatic audit trail on entity mutations
- [ ] `axiom.oltp.history` — point-in-time reconstruction from change log

### Data — OLAP

- [ ] `axiom.olap.clickhouse.base` — async ClickHouse client factory
- [ ] `axiom.olap.clickhouse.abs` — abstract query/ingest repository
- [ ] `axiom.olap.opensearch.base` — async OpenSearch client factory
- [ ] `axiom.olap.opensearch.abs` — abstract search/index repository

### Cache & Storage

- [ ] `axiom.cache.base` — `BaseCache` abstract interface
- [ ] `axiom.cache.inmemory` — `InMemoryCache` (TTL, LRU eviction)
- [ ] `axiom.cache.redis` — `RedisCache` backed by `axiom-redis`
- [ ] `axiom.objectstore.base` — `BaseObjectStore` abstract interface
- [ ] `axiom.objectstore.abs` — abstract file repository (`put`, `get`, `delete`, `list`)
- [ ] `axiom.objectstore.s3` — S3-compatible implementation via `aiobotocore`
- [ ] `axiom.objectstore.local` — local disk implementation for dev/test

### Messaging & Tasks

- [ ] `axiom.queue.rabbitmq` — RabbitMQ producer/consumer via `aio-pika`
- [ ] `axiom.queue.redis_stream` — Redis Streams producer/consumer
- [ ] `axiom.queue.kafka` — Kafka producer/consumer via `aiokafka`
- [ ] `axiom.queue.middleware.logging` — structured message logging middleware
- [ ] `axiom.queue.middleware.tracing` — trace context propagation in messages
- [ ] `axiom.task.celery` — Celery worker integration with axiom context
- [ ] `axiom.task.arq` — arq async task queue integration
- [ ] `axiom.task.middleware.logging` — task execution logging
- [ ] `axiom.task.middleware.tracing` — trace span per task execution

### Auth & Security

- [ ] `axiom.auth.basic` — HTTP Basic authentication backend
- [ ] `axiom.auth.email` — email + password authentication
- [ ] `axiom.auth.api_token` — static/rotating API token authentication
- [ ] `axiom.auth.oauth2` — OAuth2 / OIDC base (authorization code, client credentials)
- [ ] `axiom.auth.oauth2.keycloak` — Keycloak OIDC integration
- [ ] `axiom.auth.rbac` — role-based access control
- [ ] `axiom.auth.abac` — attribute-based access control
- [ ] `axiom.lock` — distributed lock abstraction with Redis backend

### Observability

- [ ] `axiom.metric.prometheus` — Prometheus metrics exposition (counters, histograms, gauges)
- [ ] `axiom.metric.statsd` — StatsD metrics client
- [ ] `axiom.tracing` — OpenTelemetry tracer setup with Jaeger exporter
- [ ] `axiom.grpc.middleware.logging` — gRPC interceptor for structured logging
- [ ] `axiom.grpc.middleware.tracing` — gRPC interceptor for trace propagation

### Infrastructure

- [ ] `axiom.migration` — Alembic migration runner with multi-database support
- [ ] `axiom.serialization` — JSON/MessagePack serialization with pydantic support
- [ ] `axiom.vault` — HashiCorp Vault client for secrets and dynamic credentials
- [ ] `axiom.email` — email sending via SMTP / SendGrid / SES backends

### Developer Experience

- [ ] Per-package example applications in `examples/`
- [ ] CRUD example: FastAPI + SQLAlchemy + Redis cache
- [ ] DDD example: FastAPI + use cases + SQLAlchemy + domain events
- [ ] Docker Compose dev environment (Postgres, Redis, RabbitMQ, Jaeger, Vault)
- [ ] Package scaffolding script (`make new-package PKG=axiom-mypkg`)
