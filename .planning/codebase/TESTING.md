# Testing Patterns

**Analysis Date:** 2026-04-07

## Test Framework

**Runner:**
- pytest — configured in root `pyproject.toml` and per-package `pyproject.toml`
- Config: root `pyproject.toml` `[tool.pytest.ini_options]`

**Async Support:**
- pytest-asyncio `>=0.24.0` with `asyncio_mode = "auto"` — async test functions require no decorator

**Assertion Library:**
- pytest built-in `assert` statements

**Coverage:**
- pytest-cov available in some packages (e.g., `axiom-cache/pyproject.toml`)

**Run Commands:**
```bash
# Run all packages with summary (recommended)
make test

# Run a single package
cd axiom-cache && uv run pytest tests -v

# Run entire workspace (may have cross-package import conflicts — use make test instead)
uv run pytest
```

## Test File Organization

**Location:**
- Tests live in a top-level `tests/` directory inside each package directory (NOT co-located with source)
- Example: `axiom-cache/tests/`, `oltp/axiom-sqlalchemy/tests/`, `axiom-email/tests/`

**Naming:**
- Test files: `test_{feature}.py` — e.g., `test_cached_decorator.py`, `test_async_repository.py`
- Each `tests/` directory has an `__init__.py`

**Sub-directories:**
- `tests/unit/` — pure unit tests (e.g., `axiom-email/tests/unit/`)
- `tests/integration/` — integration tests requiring external services (e.g., `axiom-email/tests/integration/`)
- `tests/fixtures/` — shared model definitions and test data factories (e.g., `oltp/axiom-sqlalchemy/tests/fixtures/models.py`)

**Structure:**
```
axiom-{pkg}/
└── tests/
    ├── __init__.py
    ├── conftest.py          # package-level fixtures
    ├── fixtures/            # model definitions, factories
    │   ├── __init__.py
    │   └── models.py
    ├── unit/                # unit tests (axiom-email pattern)
    │   ├── __init__.py
    │   └── test_*.py
    └── integration/         # integration tests (axiom-email pattern)
        ├── conftest.py
        └── test_*.py
```

## Test Structure

**Suite Organization:**

Tests are grouped into classes when testing a coherent unit or behavior group. Functions are used for simpler, independent checks.

```python
# Class-based grouping (preferred for async+sync parity or feature groups)
class TestCachedDecoratorAsync:
    """Tests for @cached with async functions."""

    async def test_caches_result(self, async_inmemory: AsyncInMemoryCache) -> None:
        """Function result is cached on first call."""
        ...

class TestCachedDecoratorSync:
    """Tests for @cached with sync functions."""

    def test_caches_result(self, sync_inmemory: SyncInMemoryCache) -> None:
        """Function result is cached on first call."""
        ...


# Function-based (for isolated feature checks)
def test_create_app_defaults() -> None:
    config = AppConfig()
    app = create_app(config)
    assert isinstance(app, FastAPI)
```

**Patterns:**
- Each test method has a single-sentence docstring describing the expected behavior
- `setup_method` used for class-level initialization when conftest fixtures are not needed:
  ```python
  def setup_method(self):
      self.renderer = JinjaTemplateRenderer()
  ```
- No `teardown_method` — state is contained within the test scope using fixtures

## Fixtures

**Location:** `tests/conftest.py` per package; `tests/integration/conftest.py` for integration-specific setup.

**Pattern:**
```python
# conftest.py — axiom-cache
import fakeredis
import pytest
from axiom.cache.redis import AsyncRedisCache

@pytest.fixture
def fake_sync_redis() -> fakeredis.FakeRedis:
    """Return a FakeRedis sync client."""
    return fakeredis.FakeRedis()

@pytest.fixture
async def fake_async_redis() -> fakeredis.aioredis.FakeRedis:
    """Return a FakeRedis async client."""
    return fakeredis.aioredis.FakeRedis()

@pytest.fixture
async def async_redis_cache(fake_async_redis) -> AsyncRedisCache:
    """Return an AsyncRedisCache backed by fakeredis."""
    client = AsyncRedisClient(fake_async_redis)
    return AsyncRedisCache(client)
```

**Fixture Conventions:**
- Fixtures have one-line docstrings
- Async fixtures declared with `async def` — no additional markers needed (`asyncio_mode = "auto"`)
- Database fixtures use `yield` with teardown:
  ```python
  @pytest.fixture
  async def async_engine():
      engine = create_async_engine(_ASYNC_URL)
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.create_all)
      yield engine
      async with engine.begin() as conn:
          await conn.run_sync(Base.metadata.drop_all)
      await engine.dispose()
  ```
- Local fixtures defined inside test files when specific to that test module:
  ```python
  @pytest.fixture
  def repo(async_session):
      return AsyncSQLiteRepository(model=UserModel, db_session=async_session)
  ```

## Mocking

**Framework:** `unittest.mock` — `MagicMock`, `AsyncMock`, `patch`

**Patterns:**
```python
# Patching module-level callables
from unittest.mock import AsyncMock, patch

async def test_send_calls_aiosmtplib(self):
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        backend = YandexAsyncSMTPBackend(_make_config())
        result = await backend.send(_make_message())
    assert result.success is True
    mock_send.assert_awaited_once()

# Patching object methods
from unittest.mock import patch
with patch.object(hook._logger, "info") as mock_log:
    hook.before_send(msg)
    mock_log.assert_called_once()

# Full mock object
from unittest.mock import AsyncMock, MagicMock
backend = AsyncMock()
backend.send = AsyncMock(return_value=SendResult(success=True))
```

**What to Mock:**
- External network calls (`aiosmtplib.send`, SMTP connections)
- Logger methods when verifying that specific log events are emitted
- Backend dependencies when testing client/wrapper layers in isolation

**What NOT to Mock:**
- In-memory data structures — use `fakeredis` instead of mocking Redis clients
- SQLAlchemy sessions — use in-memory SQLite (`sqlite:///:memory:`) via real engine/session fixtures
- MongoDB — use `mongomock` / `mongomock-motor` instead of mocking Beanie

## Fakes and Test Doubles

**Redis:** `fakeredis` (sync) and `fakeredis.aioredis` (async) — used in `axiom-redis` and `axiom-cache`

**MongoDB/Beanie:** `mongomock` + `mongomock_motor.AsyncMongoMockClient` — used in `oltp/axiom-beanie`

**SQLAlchemy:** In-memory SQLite engine (`sqlite:///:memory:` and `sqlite+aiosqlite:///:memory:`)

**Email:** `axiom.email.testing.AsyncInMemoryMailBackend` / `AsyncFakeMailBackend` — built-in test helpers

**Docker/Real services:** `testcontainers` library — used in `axiom-email/tests/integration/` with `MailpitContainer`

## Test Data Factories

**Pattern — helper functions with defaults:**
```python
def _make_config(**kwargs):
    defaults = {"username": "user@yandex.ru", "password": "secret"}
    defaults.update(kwargs)
    return YandexSMTPConfig(**defaults)

def _make_message(**kwargs):
    defaults = {"to": ["dst@example.com"], "subject": "Test", "text": "body"}
    defaults.update(kwargs)
    return EmailMessage(**defaults)
```

**SQLAlchemy test models:** Defined in `tests/fixtures/models.py` using `Base` from production code, registered as tables via `conftest.py` import side-effect.

## Coverage

**Requirements:** No enforced coverage threshold detected.

**View Coverage:**
```bash
cd axiom-cache && uv run pytest tests --cov=src/axiom/cache --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Scope: single class/function/module in isolation
- Uses fakes (fakeredis, mongomock) and unittest.mock
- Examples: `axiom-cache/tests/test_cached_decorator.py`, `axiom-email/tests/unit/`

**Integration Tests:**
- Scope: full stack within a package using in-memory databases or test containers
- Examples: `oltp/axiom-sqlalchemy/tests/test_async_repository.py` (SQLite in-memory), `axiom-email/tests/integration/test_mailpit_smtp.py` (Docker container)
- Integration tests requiring Docker placed in `tests/integration/` subdirectory

**E2E Tests:**
- Not present — no cross-package or full-application end-to-end test suite detected

## Common Patterns

**Async Testing (asyncio_mode = "auto"):**
```python
# No @pytest.mark.asyncio needed — async def is sufficient
async def test_create(self, repo):
    user = await repo.create({"name": "Alice", "email": "alice@test.com", "age": 30})
    await repo.session.flush()
    assert user.name == "Alice"
```

**Error Testing:**
```python
# Using pytest.raises as context manager
async def test_update_wrong_type(self, repo):
    user = await repo.create({"name": "OWT", "email": "owt@test.com", "age": 20})
    await repo.session.flush()
    with pytest.raises(ValidationError):
        await repo.update(user, {"name": 123})

# Testing exception message content
async def test_smtp_exception_returns_failure(self):
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = aiosmtplib.SMTPException("Auth failed")
        result = await backend.send(_make_message())
    assert result.success is False
    assert "Auth failed" in result.error
```

**HTTP/ASGI Testing:**
```python
from starlette.testclient import TestClient

def test_domain_handler() -> None:
    client = TestClient(make_app(), raise_server_exceptions=False)
    resp = client.get("/domain")
    assert resp.status_code == 400
    assert resp.json()["code"] == "test_error"
```

**Docker Integration Tests:**
```python
# module-scoped container — started once per test module
@pytest.fixture(scope="module")
def mailpit():
    _resolve_docker_host()
    with MailpitContainer(image="axllent/mailpit:v1.21") as container:
        yield container
```

**Ruff noqa Suppression in Tests:**
```python
# At file top — suppress docstring and other rules for test files
# ruff: noqa: D100, D101, D102, D103, E501
```

## Per-Package Test Isolation

Tests are run per-package to avoid cross-package import conflicts:
```bash
# Makefile iterates packages:
for pkg in axiom-* oltp/axiom-* olap/axiom-*; do
    cd "$pkg" && uv run pytest tests -v
done
```

Each package's `pyproject.toml` declares its own `[dependency-groups] dev` with test dependencies, ensuring each package is tested against the correct dependency versions.

---

*Testing analysis: 2026-04-07*
