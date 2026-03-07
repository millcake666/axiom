# Axiom

A Python monorepo of composable packages for building production-grade services. All packages share the `axiom.*`
namespace and are designed to work independently or together.

**Package manager:** [uv](https://docs.astral.sh/uv/) · **Python:** 3.13+ · **Build system:** Hatchling

---

## Architecture

```
axiom/
├── axiom-core/              # Foundation — settings, logging, exceptions, context, entities
├── axiom-fastapi/           # FastAPI base — middleware/, rate_limiter/ packages inside
│   ├── middleware/          #   cors, logging, tracing, auth middleware
│   └── rate_limiter/        #   rate limiting
│
├── axiom-auth/              # Auth — basic, email, api_token, oauth2/keycloak, abac, rbac
├── axiom-cache/             # Cache abstractions — InMemory + Redis backends
├── axiom-email/             # Email sending abstractions and backends
├── axiom-grpc/              # gRPC server and client plugin
├── axiom-lock/              # Distributed locking with cascading lock support
├── axiom-metric/            # Metrics — prometheus, statsd backends
├── axiom-migration/         # Database migrations via Alembic
├── axiom-queue/             # Message queue — rabbitmq, redis_stream, kafka backends
├── axiom-redis/             # Async Redis client and utilities
├── axiom-s3/                # S3-compatible object storage
├── axiom-serialization/     # Data serialization and validation
├── axiom-task/              # Async task queue — celery, arq backends
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

| Package         | Description                                                                                                       |
|-----------------|-------------------------------------------------------------------------------------------------------------------|
| `axiom-core`    | Foundation for all axiom.* packages. Modules: **settings**, **logger**, **exceptions**, **context**, **entities** |
| `axiom-fastapi` | Base for FastAPI applications. Packages: **middleware** (cors, logging, tracing, auth), **rate_limiter**          |
| `axiom-vault`   | HashiCorp Vault — secrets backend for `axiom.core.settings`                                                       |

### Data Layer

| Package       | Description                                                    |
|---------------|----------------------------------------------------------------|
| `axiom-redis` | Async Redis client and utilities                               |
| `axiom-cache` | Cache abstractions — `InMemoryCache`, `RedisCache` backends    |
| `axiom-s3`    | S3-compatible object storage (AWS S3, MinIO) via `aiobotocore` |

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

| Package      | Sub-packages                                                     | Description                                     |
|--------------|------------------------------------------------------------------|-------------------------------------------------|
| `axiom-auth` | `basic`, `email`, `api_token`, `oauth2/keycloak`, `abac`, `rbac` | Multi-scheme auth and access control            |
| `axiom-lock` | —                                                                | Distributed locking with cascading lock support |

### Observability

| Package         | Sub-packages           | Description                                    |
|-----------------|------------------------|------------------------------------------------|
| `axiom-metric`  | `prometheus`, `statsd` | Application metrics collection                 |
| `axiom-tracing` | —                      | Distributed tracing via OpenTelemetry + Jaeger |

### Infrastructure

| Package               | Sub-modules | Description                                        |
|-----------------------|-------------|----------------------------------------------------|
| `axiom-migration`     | —           | Database migrations via Alembic                    |
| `axiom-serialization` | —           | Data serialization, validation, and transformation |
| `axiom-grpc`          | —           | gRPC server and client plugin                      |

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
from axiom.core.entities import AggregateRoot
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
from axiom.sqlalchemy.base import Base

class OrderModel(Base):
    __tablename__ = "order"
    ...

# Beanie (oltp/axiom-beanie)
from axiom.beanie.base import BaseDocument

class OrderDocument(BaseDocument):
    ...
```

---

## axiom-core Modules

```python
# Exceptions
from axiom.core.exceptions import AxiomError, NotFoundError, ValidationError

# Entities (dataclass base)
from axiom.core.entities import Entity, UUIDEntity, AggregateRoot

# Context (per-request ContextVars)
from axiom.core.context import request_id, user_id, trace_id, tenant_id

# Logging
from axiom.core.logger import get_logger, configure_logging

# Settings
from axiom.core.settings import BaseSettings
```

---

## axiom-core.settings + axiom-vault

```python
from axiom.core.settings import BaseSettings
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
uv add axiom-s3

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

| Workflow         | Trigger           | Jobs                                       |
|------------------|-------------------|--------------------------------------------|
| `tests.yml`      | Push/PR to `main` | Tests (Python 3.13), mypy                  |
| `pre-commit.yml` | Push/PR to `main` | Pre-commit hooks                           |
| `release.yml`    | Push tag `v*.*.*` | Build all packages → GitHub Release + PyPI |

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
