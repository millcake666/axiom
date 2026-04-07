# Codebase Concerns

**Analysis Date:** 2026-04-07

---

## Tech Debt

### Stub-Only Packages With Zero Implementation

Several packages are declared in the workspace and have directory/exception structures but contain no actual logic — just docstring-only `__init__.py` files and empty `__version__ = "0.1.0"`.

**axiom-auth:**
- Files: `axiom-auth/src/axiom/auth/__init__.py`, all sub-packages (`abac/`, `rbac/`, `basic/`, `classic/`, `oauth2/`, `token/`)
- Impact: Authentication and authorization are completely non-functional. Any consumer importing from `axiom.auth` gets no usable classes.
- Fix approach: Implement each scheme: basic HTTP auth, JWT token, RBAC, ABAC, Keycloak OAuth2. See `todo.md` item 7.

**axiom-queue:**
- Files: `axiom-queue/src/axiom/queue/__init__.py`, all backends (`rabbitmq/`, `kafka/`, `redis_stream/`)
- Impact: Zero queue producer/consumer functionality. See `todo.md` item 9.
- Fix approach: Implement producer/consumer abstractions per backend.

**axiom-task:**
- Files: `axiom-task/src/axiom/task/__init__.py`, `celery/`, `arq/` sub-packages
- Impact: No task scheduling or background job functionality. See `todo.md` item 10.
- Fix approach: Implement Celery and ARQ integrations.

**olap/axiom-clickhouse:**
- Files: `olap/axiom-clickhouse/src/axiom/olap/clickhouse/__init__.py`
- Impact: ClickHouse integration is fully absent.
- Fix approach: Implement analytical query client.

**olap/axiom-opensearch:**
- Files: `olap/axiom-opensearch/src/axiom/olap/opensearch/__init__.py`
- Impact: OpenSearch full-text search integration is fully absent.

**Test coverage:** `axiom-queue/tests/__init__.py`, `axiom-task/tests/__init__.py`, `olap/axiom-clickhouse/tests/__init__.py`, `olap/axiom-opensearch/tests/__init__.py` — all empty `__init__.py` only.

---

### Missing `create_or_update(model)` in SQLAlchemy Repositories

- Issue: `todo.md` item 4 explicitly calls out `create_or_update(model)` as needed for all implementations. Tests exist for it in `oltp/axiom-beanie/tests/test_sync_repository.py` and `oltp/axiom-beanie/tests/test_async_repository.py`, but the SQLAlchemy repositories may be missing this.
- Files: `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/base/repository/async_.py`, `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/base/repository/sync.py`
- Impact: Consumers of `axiom-sqlalchemy` cannot perform upsert operations.
- Fix approach: Implement `create_or_update(model)` on base SQLAlchemy repository following the Beanie pattern.

---

### Planned Packages Not Yet Created

The following packages are mentioned in `todo.md` or project memory but do not exist as workspace directories:

- `axiom-grpc` — gRPC support
- `axiom-tracing` — OpenTelemetry + Jaeger (todo.md item 5)
- `axiom-vault` — HashiCorp Vault secrets
- `axiom-lock` — Distributed locking
- `axiom-metric` — Prometheus/StatsD metrics (todo.md item 6)
- `axiom-middleware` — CORS, logging, tracing middleware
- `axiom-migration` — Alembic migrations
- `axiom-serialization` — exists in `mypy.ini`'s `mypy_path` but directory is absent from the workspace

- Impact: `mypy.ini` references `axiom-serialization/src` in `mypy_path` which will cause mypy to silently skip that path.
- Fix approach: Either create the `axiom-serialization` package or remove it from `mypy.ini`.

---

### Pervasive File-Level mypy Suppression in ORM Packages

The entire ORM layer (Beanie and SQLAlchemy) relies on broad file-level `# mypy: disable-error-code=` directives covering critical error codes like `attr-defined`, `return-value`, `arg-type`, `assignment`, `call-overload`, and `unreachable`. This reflects compatibility issues between Python 3.13 generic syntax (`class Repo[T]`) and mypy's analysis of third-party ORM types.

- Files: `oltp/axiom-beanie/src/axiom/oltp/beanie/base/repository/async_.py`, `oltp/axiom-beanie/src/axiom/oltp/beanie/base/repository/sync.py`, `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/base/repository/async_.py`, `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/base/repository/sync.py`, and 20+ other files
- Impact: Type errors in the ORM layer are silently suppressed. Real bugs in return types, attribute access, and argument passing will not surface via mypy.
- Fix approach: Track upstream support for Python 3.13 generics in beanie/sqlalchemy stubs and reduce suppressions incrementally.

---

### Global mypy `disable_error_code` Is Too Broad

`mypy.ini` globally disables: `empty-body`, `no-any-return`, `attr-defined`, `return-value`, `call-arg`, `union-attr`, `unused-ignore`, `unreachable`, `no-untyped-def`.

- Files: `mypy.ini`
- Impact: Suppressing `no-any-return`, `return-value`, and `attr-defined` globally means mypy cannot catch an entire class of type errors across all packages.
- Fix approach: Replace global suppressions with targeted per-file or per-module overrides as ORM stub support improves.

---

### Dead Function: `_domain_handler` in `domain.py`

A private `_domain_handler` function exists at module scope in `axiom-fastapi/src/axiom/fastapi/exception_handler/domain.py` (lines 17–21) but is never used — the module-level `register_domain_handler` defines its own closure `handler` and registers that instead.

- Files: `axiom-fastapi/src/axiom/fastapi/exception_handler/domain.py`
- Impact: Dead code; creates confusion about which handler is actually registered.
- Fix approach: Remove `_domain_handler`.

---

### Mixed Logging Frameworks: loguru vs structlog

- `axiom-core` defines a `configure_logger` and `get_logger` built on `loguru`. Used by `axiom-objectstore` and `axiom-email`.
- `axiom-fastapi` uses `structlog` directly for all its exception handlers and middlewares (`middleware/error/middleware.py`, `middleware/logging/middleware.py`, `exception_handler/domain.py`, `exception_handler/unhandled.py`).
- `oltp/axiom-sqlalchemy` also uses `structlog` in its exception handler.
- Files: `axiom-fastapi/src/axiom/fastapi/exception_handler/domain.py`, `axiom-fastapi/src/axiom/fastapi/middleware/logging/middleware.py`, `axiom-objectstore/src/axiom/objectstore/s3/async_.py`, `axiom-core/src/axiom/core/logger/core.py`
- Impact: Inconsistent log output format across packages. Applications mixing packages from axiom-core and axiom-fastapi will emit logs in two different formats. No coordination between loguru and structlog configuration.
- Fix approach: Standardize on one framework. The canonical logger is in `axiom-core`; `axiom-fastapi` components should use `axiom.core.logger.get_logger` or provide an adapter.

---

## Security Considerations

### `dill.loads` Deserialization of Untrusted Data

- Risk: `dill.loads` can execute arbitrary Python code during deserialization. The `DillStrategy` is available as a cache serialization backend.
- Files: `axiom-cache/src/axiom/cache/serialization/dill_strategy.py`
- Current mitigation: `# nosec B301` and `# noqa: S301` suppress the bandit/ruff warnings. No input validation.
- Recommendations: Document clearly that `DillStrategy` must never be used with data from untrusted sources (e.g., public Redis instances). Add a docstring warning. Consider removing from default exports or gating behind an explicit opt-in.

### Default `APP_HOST = "0.0.0.0"` in Settings and Runners

- Risk: Default bind to all interfaces is a reasonable choice for containers but dangerous in development environments where it exposes the service to the local network.
- Files: `axiom-core/src/axiom/core/settings/base.py:22`, `axiom-fastapi/src/axiom/fastapi/runner/gunicorn.py:16`, `axiom-fastapi/src/axiom/fastapi/runner/uvicorn.py:15`
- Current mitigation: `# noqa: S104  # nosec B104` suppresses warnings on all three.
- Recommendations: Change default to `127.0.0.1` for development settings; override to `0.0.0.0` in production/container configurations.

---

## Performance Bottlenecks

### `AsyncS3ObjectStore` Creates a New Client Session Per Operation

Every method call in `axiom-objectstore/src/axiom/objectstore/s3/async_.py` opens a new `aiobotocore` session via `async with session.create_client(...)`. The same pattern is in the sync client.

- Files: `axiom-objectstore/src/axiom/objectstore/s3/async_.py`, `axiom-objectstore/src/axiom/objectstore/s3/sync.py`
- Cause: `_client()` is an `asynccontextmanager` that creates a new session for every call — upload, download, delete, head, presign all open/close their own connection.
- Impact: High latency overhead for any workload performing multiple consecutive S3 operations, due to repeated TLS handshakes.
- Improvement path: Add optional persistent client with a `startup()`/`shutdown()` lifecycle, or use a connection pool. Match the pattern used in `axiom-redis`.

### `botocore.exceptions.ClientError` Imported Inside Every Method

`from botocore.exceptions import ClientError` is repeated as a deferred import inside every individual S3 method body (5 times in `sync.py`, 6 times in `async_.py`).

- Files: `axiom-objectstore/src/axiom/objectstore/s3/sync.py`, `axiom-objectstore/src/axiom/objectstore/s3/async_.py`
- Cause: Workaround for the `type: ignore[import-untyped]` pattern to avoid top-level import errors.
- Impact: Minor import overhead per call; more importantly, creates code duplication and reduces readability.
- Improvement path: Move the import to module level with a single `# type: ignore[import-untyped]`.

---

## Fragile Areas

### `SyncSQLAlchemyMiddleware` Uses `BaseHTTPMiddleware` With Starlette Type Conflict

`SyncSQLAlchemyMiddleware` subclasses `BaseHTTPMiddleware` but its `dispatch` signature requires `# type: ignore[override]` because `call_next` lacks a type annotation.

- Files: `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/middleware/sync_.py:15`
- Why fragile: `BaseHTTPMiddleware` has known performance implications in Starlette (buffering the request body). The type ignore hides a signature mismatch.
- Safe modification: Add proper `CallNext` type annotation. Consider migrating to pure ASGI middleware as done in `AsyncSQLAlchemyMiddleware`.
- Test coverage: `oltp/axiom-sqlalchemy/tests/test_middleware.py` has `# type: ignore[arg-type]` on registration, suggesting the test itself works around the same issue.

### `GunicornApplication` Silently Unavailable at Runtime

`run_gunicorn` in `axiom-fastapi/src/axiom/fastapi/runner/gunicorn.py` references `GunicornApplication` which is only defined inside a `try: ... except ImportError: pass` block. If `gunicorn` is not installed, calling `run_gunicorn` raises `NameError: name 'GunicornApplication' is not defined` with a `# type: ignore[name-defined]` silencing the static error.

- Files: `axiom-fastapi/src/axiom/fastapi/runner/gunicorn.py:93`
- Why fragile: The failure mode is a confusing `NameError` at runtime rather than a clear `ImportError` with install instructions.
- Safe modification: Add an explicit guard at the top of `run_gunicorn` that raises `ImportError` with a helpful message if `gunicorn` is not installed.

### Beanie `base/repository` Suppresses Nearly Every mypy Error

`oltp/axiom-beanie/src/axiom/oltp/beanie/base/repository/async_.py` and `sync.py` both carry `# ruff: noqa: W505, E501, D100, D101, D102, D103, D105, D107, S110` plus `# mypy: disable-error-code` for 11 separate error codes. Any change to these files carries zero static safety net.

- Files: `oltp/axiom-beanie/src/axiom/oltp/beanie/base/repository/async_.py`, `oltp/axiom-beanie/src/axiom/oltp/beanie/base/repository/sync.py`
- Why fragile: Broad suppression means refactoring these 500+ line files will not surface type regressions until runtime.
- Safe modification: Maintain full test coverage; run tests via `cd oltp/axiom-beanie && uv run pytest tests` before and after changes.

---

## Test Coverage Gaps

### No Tests for axiom-auth, axiom-queue, axiom-task, axiom-clickhouse, axiom-opensearch

These packages have only empty `tests/__init__.py` files:

- `axiom-auth/tests/__init__.py`
- `axiom-queue/tests/__init__.py`
- `axiom-task/tests/__init__.py`
- `olap/axiom-clickhouse/tests/__init__.py`
- `olap/axiom-opensearch/tests/__init__.py`

- Risk: No regression protection when implementations are added.
- Priority: High (must be written alongside implementations).

### No Coverage Configuration for axiom-fastapi, axiom-auth, axiom-queue, axiom-task

These packages have no `pytest-cov` in their dev dependencies and no `[tool.coverage.run]` section.

- Files: `axiom-fastapi/pyproject.toml`, `axiom-auth/pyproject.toml`, `axiom-queue/pyproject.toml`, `axiom-task/pyproject.toml`
- Risk: Test runs produce no coverage data; gaps in exception handlers and middleware are not visible.
- Priority: Medium.

### No Integration/E2E Tests for Gunicorn or Uvicorn Runners

`axiom-fastapi/tests/test_runner_gunicorn.py` and `test_runner_uvicorn.py` exist but likely test only configuration, not actual process startup.

- Files: `axiom-fastapi/tests/test_runner_gunicorn.py`, `axiom-fastapi/tests/test_runner_uvicorn.py`
- Risk: Process startup failures (wrong worker class, port conflicts) go undetected until deployment.
- Priority: Low.

---

## Dependencies at Risk

### `axiom-serialization` Referenced in mypy.ini But Package Does Not Exist

- Risk: `mypy.ini` includes `axiom-serialization/src` in `mypy_path` but no such directory exists in the workspace.
- Impact: mypy will log a warning or silently skip; more importantly it reflects a planned package that was never created.
- Migration plan: Create the package at `axiom-serialization/` or remove the entry from `mypy.ini`.

### All Packages Pinned at `version = "0.1.0"` with No Changelog

Every package — 13 total — is at `0.1.0`. The CI auto-tagger only creates tags when a version has not been tagged yet; once tagged, bumping requires manual `pyproject.toml` edits with no tooling to enforce semver discipline.

- Files: All `*/pyproject.toml`
- Impact: No traceability for breaking changes between packages. Consumers cannot pin stable versions.
- Improvement path: Adopt a versioning convention (e.g., `bump2version` or `uv version`) and a CHANGELOG per package.

---

*Concerns audit: 2026-04-07*
