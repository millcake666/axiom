# Technology Stack

**Analysis Date:** 2026-04-09

## Languages

**Primary:**
- Python 3.13 — all source code across all workspace packages

## Runtime

**Environment:**
- CPython 3.13 (pinned via `.python-version`)

**Package Manager:**
- uv — workspace-level dependency management and script runner
- Lockfile: `uv.lock` present (revision 2, `requires-python = ">=3.13"`)

## Workspace Structure

UV monorepo. Root `pyproject.toml` defines workspace members:
```
members = ["axiom-*", "oltp/axiom-*", "olap/axiom-*"]
```

All packages use `requires-python = ">=3.13"`.

Build backend: `hatchling` (all packages share `[build-system] requires = ["hatchling"]`).

Each package sets `[tool.hatch.build.targets.wheel] packages = ["src/axiom"]` to publish the namespace.

## Frameworks

**Web:**
- `fastapi>=0.115.0,<1` — HTTP API framework (`axiom-fastapi/pyproject.toml`)
- `uvicorn>=0.29.0,<1` — ASGI server (default runner)
- `gunicorn>=21.0` + `uvicorn[standard]` — production multi-worker runner (optional extra in `axiom-fastapi`)
- `limits>=3.0,<4` — rate limiting algorithms/backends (optional `axiom-fastapi[rate-limiter]`)

**Data Validation:**
- `pydantic>=2.0` — model/schema validation throughout
- `pydantic-settings>=2.0` — environment-based configuration (`axiom-core`, `axiom-redis`)

**Logging:**
- `loguru>=0.7` — core structured logging (`axiom-core/pyproject.toml`)
- `structlog>=24.0,<26` — request/response structured logging in FastAPI middleware (`axiom-fastapi`, `axiom-sqlalchemy` FastAPI optional)

**Testing:**
- `pytest>=8.0.0,<9` — test runner (all packages)
- `pytest-asyncio>=0.23` — async test support; `asyncio_mode = "auto"` globally
- `pytest-cov>=4.0` — coverage reporting (most packages)
- `httpx>=0.27.0,<1` — HTTP test client for FastAPI (`axiom-fastapi` dev)
- `testcontainers[mailpit]>=4.0.0` — integration test container for SMTP (`axiom-email` dev)
- `testcontainers[redis]>=4.0.0` — integration Redis container for `axiom-fastapi` rate limiter tests
- `fakeredis>=2.0.0` — in-process Redis mock (`axiom-redis`, `axiom-cache`, `axiom-fastapi` dev)
- `mongomock>=4.0` + `mongomock-motor>=0.0.21` — MongoDB mock (`axiom-beanie` dev)

## Key Dependencies

**Critical (runtime):**
- `redis[asyncio,hiredis]>=5.0.0,<6` — Redis client with hiredis C parser (`axiom-redis/pyproject.toml`)
- `limits>=3.0,<4` — request quota algorithms and Redis/in-memory storage strategy (`axiom-fastapi[rate-limiter]`)
- `sqlalchemy[asyncio]>=2.0` — async ORM (`oltp/axiom-sqlalchemy/pyproject.toml`)
- `beanie>=2.1.0` + `motor>=3.0` + `pymongo>=4.0` — MongoDB async ODM (`oltp/axiom-beanie/pyproject.toml`)
- `aiobotocore>=2.15.0,<3` + `boto3>=1.35.0,<2` — async S3 / AWS (`axiom-objectstore/pyproject.toml`)
- `aiofiles>=24.0.0,<25` — async local filesystem I/O (`axiom-objectstore/pyproject.toml`)
- `aiosmtplib>=3.0` — async SMTP email sending (`axiom-email` optional/dev)
- `jinja2>=3.0` — email HTML templating (`axiom-email` optional/dev)
- `tomlkit>=0.12` — TOML parsing (project info from `pyproject.toml` at runtime in `axiom-core`, `axiom-fastapi`)

**Database drivers (optional extras):**
- `asyncpg>=0.29.0` + `psycopg[binary]>=3.0` — PostgreSQL async drivers (`axiom-sqlalchemy[postgres]`)
- `aiosqlite>=0.19.0` — SQLite async driver (`axiom-sqlalchemy[sqlite]`)

**Serialization (optional extras in `axiom-cache`):**
- `orjson>=3.9.0` — fast JSON serialization
- `msgpack>=1.0.0` — binary serialization
- `dill>=0.3.0` — extended pickle serialization

## Configuration

**Environment:**
- Settings loaded via `pydantic-settings` from `.env` file at root (per `BaseAppSettings` in `axiom-core/src/axiom/core/settings/base.py`)
- `env_file = ".env"`, `env_file_encoding = "utf-8"`, `extra = "ignore"`
- No `.env` file present in repository (not committed)
- Key env var names follow `APP_HOST`, `APP_PORT`, `APP_STAGE`, `APP_NAME`, `DEBUG` pattern
- Per-integration settings: `REDIS_URL`, `S3_AWS_ACCESS_KEY_ID`, `S3_AWS_SECRET_ACCESS_KEY`, `S3_ENDPOINT_URL`, `S3_BUCKET_NAME`, etc.

**Build:**
- `pyproject.toml` per package (14 packages total)
- Root `pyproject.toml` contains workspace definition and shared dev tooling config

## Code Quality Tools

**Linting/Formatting:**
- `ruff>=0.11.13` — formatter + linter (line-length 100, Google docstring convention)
- `mypy>=1.16.0,<2` — static type checking
- `pylint>=3.3.0,<4` — additional linting
- `vulture>=2.15` — dead code detection
- `bandit 1.9.4` — security scanning (via pre-commit)
- `pip-audit>=2.9.0` — dependency vulnerability audit (via pre-commit)

**Pre-commit hooks** (`.pre-commit-config.yaml`):
- `pre-commit-hooks` v6.0.0 — AST check, trailing whitespace, TOML/YAML check
- `add-trailing-comma` v4.0.0
- `bandit` 1.9.4 — security scan
- `pip-audit` v2.10.0
- `ruff format` → `ruff check --fix` → `ruff check` — format then lint
- `mypy` — type validation via `scripts/check_types.py`

## Platform Requirements

**Development:**
- Python 3.13, uv package manager
- Docker (for testcontainers in `axiom-email` Mailpit tests and `axiom-fastapi` Redis rate limiter tests)

**Production:**
- ASGI: uvicorn (default) or gunicorn+uvicorn (multi-worker)
- No deployment platform specified; packages are library-style (no application-specific deploy config)

---

*Stack analysis: 2026-04-09*
