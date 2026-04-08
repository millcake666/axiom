# External Integrations

**Analysis Date:** 2026-04-09

## APIs & External Services

**Email (SMTP):**
- Yandex SMTP — outbound email delivery
  - SDK/Client: `aiosmtplib>=3.0` (async), stdlib `smtplib` (sync)
  - Configuration: `YandexSMTPConfig` dataclass in `axiom-email/src/axiom/email/providers/yandex/config.py`
  - Fields: `username`, `password`, `host` (default `smtp.yandex.ru`), `port` (default `465`), `use_tls`, `default_from`
  - Backends: async (`axiom-email/src/axiom/email/providers/yandex/async_backend.py`), sync (`axiom-email/src/axiom/email/providers/yandex/sync_backend.py`)
  - Templating: Jinja2 (`axiom-email/src/axiom/email/templating/jinja2.py`)
  - Test backend: Mailpit via testcontainers (`axiom-email` dev)

**Object Storage (S3-compatible):**
- AWS S3 / MinIO / any S3-compatible store
  - SDK/Client: `aiobotocore>=2.15.0,<3` (async), `boto3>=1.35.0,<2` (sync)
  - Configuration: `S3Settings` (pydantic mixin) and `S3Config` in `axiom-objectstore/src/axiom/objectstore/s3/config.py`
  - Auth env vars: `S3_AWS_ACCESS_KEY_ID`, `S3_AWS_SECRET_ACCESS_KEY`
  - Other env vars: `S3_ENDPOINT_URL`, `S3_REGION_NAME`, `S3_SERVICE_NAME`, `S3_BUCKET_NAME`, `S3_KEY_PREFIX`, `S3_IS_PUBLIC`
  - Async client: `axiom-objectstore/src/axiom/objectstore/s3/async_.py`
  - Sync client: `axiom-objectstore/src/axiom/objectstore/s3/sync.py`
  - Local disk fallback: `axiom-objectstore/src/axiom/objectstore/local/` (via `aiofiles`)

## Data Storage

**Relational (OLTP):**
- PostgreSQL — primary relational database
  - ORM: `sqlalchemy[asyncio]>=2.0` (`oltp/axiom-sqlalchemy/pyproject.toml`)
  - Async drivers: `asyncpg>=0.29.0`, `psycopg[binary]>=3.0` (optional extra `[postgres]`)
  - Namespace: `axiom.oltp.sqlalchemy` → `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/`
- SQLite — lightweight/test relational database
  - Driver: `aiosqlite>=0.19.0` (optional extra `[sqlite]`)

**Document (OLTP):**
- MongoDB — document store
  - ODM: `beanie>=2.1.0` with `motor>=3.0` (async) and `pymongo>=4.0`
  - Namespace: `axiom.oltp.beanie` → `oltp/axiom-beanie/src/axiom/oltp/beanie/`
  - Test mock: `mongomock`, `mongomock-motor`

**Cache/In-Memory:**
- Redis — caching, streams, pub/sub, rate limiting
  - Client: `redis[asyncio,hiredis]>=5.0.0,<6` (`axiom-redis/pyproject.toml`)
  - Settings: `RedisSettings` in `axiom-redis/src/axiom/redis/settings.py`
  - Env vars: `REDIS_URL` (default `redis://localhost:6379`), `REDIS_USE_CLUSTER`, `REDIS_MAX_CONNECTIONS`, `REDIS_SOCKET_TIMEOUT`, `REDIS_DECODE_RESPONSES`
  - Async client: `axiom-redis/src/axiom/redis/async_client.py`
  - Sync client: `axiom-redis/src/axiom/redis/sync_client.py`
  - Cache abstraction layer: `axiom-cache/src/axiom/cache/` (in-memory + Redis backends)
  - Redis Streams queue backend: `axiom-queue/src/axiom/queue/redis_stream/`

**HTTP Rate Limiting:**
- `limits>=3.0,<4` — rate limiting algorithms and storage adapters for `axiom.fastapi.rate_limiter`
  - Algorithms: fixed window, elastic/sliding window, moving window
  - In-memory backend: `axiom-fastapi/src/axiom/fastapi/rate_limiter/backend/memory.py`
  - Redis backend: `axiom-fastapi/src/axiom/fastapi/rate_limiter/backend/redis.py`
  - Redis storage: `limits.storage.RedisStorage` plus `axiom-redis` `AsyncRedisClient` for health checks and cleanup
  - Dynamic policy sources: in-memory, Redis, Postgres repository protocol, cached wrapper

**Analytical (OLAP):**
- ClickHouse — analytical queries and data ingestion
  - Package: `axiom.olap.clickhouse` → `olap/axiom-clickhouse/src/`
  - Status: stub package (no external client dependency declared yet in `olap/axiom-clickhouse/pyproject.toml`)
- OpenSearch — full-text search and analytics
  - Package: `axiom.olap.opensearch` → `olap/axiom-opensearch/src/`
  - Status: stub package (no external client dependency declared yet in `olap/axiom-opensearch/pyproject.toml`)

**File Storage:**
- Local filesystem — via `aiofiles>=24.0.0,<25` (`axiom-objectstore/src/axiom/objectstore/local/`)
- S3-compatible object storage — see Object Storage section above

## Message Queuing

**RabbitMQ:**
- Backend: `axiom-queue/src/axiom/queue/rabbitmq/`
- Status: stub (no `aio_pika` dependency declared in `axiom-queue/pyproject.toml` yet)

**Apache Kafka:**
- Backend: `axiom-queue/src/axiom/queue/kafka/`
- Status: stub (no `aiokafka` dependency declared yet)

**Redis Streams:**
- Backend: `axiom-queue/src/axiom/queue/redis_stream/`
- Uses existing `axiom-redis` client

## Task Queues

**Celery:**
- Backend: `axiom-task/src/axiom/task/celery/`
- Status: stub (no `celery` dependency declared in `axiom-task/pyproject.toml` yet)

**ARQ:**
- Backend: `axiom-task/src/axiom/task/arq/`
- Status: stub (no `arq` dependency declared yet)

## Authentication & Identity

**Custom/Classic Auth:**
- HTTP Basic Authentication: `axiom-auth/src/axiom/auth/basic/`
- Classic (username/password) auth: `axiom-auth/src/axiom/auth/classic/`
- API Token auth: `axiom-auth/src/axiom/auth/token/`

**OAuth2:**
- Keycloak OAuth2 provider: `axiom-auth/src/axiom/auth/oauth2/keycloak/`
- Generic OAuth2: `axiom-auth/src/axiom/auth/oauth2/`
- Note: No JWT library (`PyJWT`, `python-jose`) declared in `axiom-auth/pyproject.toml` — integration is stub/interface level

**Authorization:**
- RBAC: `axiom-auth/src/axiom/auth/rbac/`
- ABAC: `axiom-auth/src/axiom/auth/abac/`

## Monitoring & Observability

**Error Tracking:**
- Not detected — no Sentry or similar SDK in any `pyproject.toml`

**Logs:**
- Structured JSON logging via `loguru` (core) and `structlog` (FastAPI middleware)
- Request logging middleware: `axiom-fastapi/src/axiom/fastapi/middleware/logging/middleware.py`
- Queue middleware logging: `axiom-queue/src/axiom/queue/middleware/logging/`
- Task middleware logging: `axiom-task/src/axiom/task/middleware/logging/`
- Email hooks logging: `axiom-email/src/axiom/email/hooks/logging.py`

**Tracing:**
- Tracing middleware present for queues: `axiom-queue/src/axiom/queue/middleware/tracing/`
- Tracing middleware present for tasks: `axiom-task/src/axiom/task/middleware/tracing/`
- No OpenTelemetry/Jaeger SDK declared in current package `pyproject.toml` files (likely future `axiom-tracing` package referenced in project memory)

## CI/CD & Deployment

**Hosting:**
- Not specified (library packages distributed as Python wheels)

**CI Pipeline:**
- GitHub Actions — `.github/workflows/cicd.yml`
- Pipeline: Lint (pre-commit) → Test (pytest per-package, matrix Python 3.13) → Auto-tag → Build wheel → GitHub Release
- Uses: `astral-sh/setup-uv@v5`, `actions/upload-artifact@v4`, `actions/download-artifact@v4`, `softprops/action-gh-release@v2`
- Releases published as GitHub Releases with SHA-256 checksums

## Environment Configuration

**Required env vars by integration:**

| Integration | Key Env Vars |
|-------------|-------------|
| App base | `APP_HOST`, `APP_PORT`, `APP_STAGE`, `APP_NAME`, `DEBUG` |
| Redis | `REDIS_URL`, `REDIS_USE_CLUSTER`, `REDIS_MAX_CONNECTIONS` |
| Rate limiting | `RATE_LIMIT_BACKEND`, `RATE_LIMIT_ENABLED`, `RATE_LIMIT_ENV`, `RATE_LIMIT_EXEMPT_PATHS`, `RATE_LIMIT_FAILURE_STRATEGY`, `RATE_LIMIT_KEY_PREFIX` |
| S3/ObjectStore | `S3_AWS_ACCESS_KEY_ID`, `S3_AWS_SECRET_ACCESS_KEY`, `S3_ENDPOINT_URL`, `S3_REGION_NAME`, `S3_BUCKET_NAME` |
| Email (Yandex) | `username`, `password` fields in `YandexSMTPConfig` dataclass |

**Secrets location:**
- Loaded from `.env` file at project root (not committed, not present in repo)
- `BaseAppSettings` in `axiom-core/src/axiom/core/settings/base.py` reads `.env` automatically via `pydantic-settings`

## Webhooks & Callbacks

**Incoming:** Not detected

**Outgoing:** Not detected

---

*Integration audit: 2026-04-09*
