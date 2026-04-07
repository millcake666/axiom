# Coding Conventions

**Analysis Date:** 2026-04-07

## Naming Patterns

**Files:**
- Snake_case for all Python source files: `function_key_maker.py`, `async_.py`, `sync.py`
- Async variants use `async_.py` filename to avoid keyword collision
- Config classes live in `config.py`, abstract base in `__init__.py` or `base.py`
- `exception/` is always a sub-package (directory with `__init__.py`), never a flat `.py` file
- Test files prefixed with `test_`: `test_cached_decorator.py`, `test_async_repository.py`

**Classes:**
- PascalCase: `AsyncCacheBackend`, `FunctionKeyMaker`, `RequestLoggingMiddleware`
- Abstract base classes suffixed with the abstraction type: `AsyncCacheBackend` (ABC), `KeyMaker` (ABC)
- Async/Sync variants share same class name stem: `AsyncRedisCache` / `SyncRedisCache`, `AsyncMailClient` / `SyncMailClient`
- Pydantic config models: `AppConfig`, `BaseAppSettings`, `YandexSMTPConfig`
- Exception subclasses: `NotFoundError`, `ValidationError`, `ConflictError` (all `*Error`)

**Functions and Methods:**
- Snake_case: `make_key`, `create_app`, `register_domain_handler`
- Private helpers prefixed with `_`: `_fill_from_pyproject`, `_domain_handler`, `_resolve_docker_host`
- Factory functions use verb pattern: `create_app()`, `make_env_prefix()`
- Registration functions: `register_domain_handler(app)`, `register_all_handlers(app)`

**Variables:**
- Snake_case: `call_count`, `request_id`, `fake_async_redis`
- Module-level constants: `_ASYNC_URL`, `_SYNC_URL`, `_DEFAULT_REQUEST_ID_HEADER` (private screaming_snake with leading `_`)
- Public module-level logger: `logger = structlog.get_logger(__name__)`

**Settings:**
- Application environment variable names in SCREAMING_SNAKE_CASE: `APP_HOST`, `APP_PORT`, `APP_STAGE`, `DEBUG`

## Code Style

**Formatter:**
- Ruff format — run via `uv run ruff format`
- Line length: 100 characters (lint), 120 characters max (doc strings)
- Trailing commas enforced by `add-trailing-comma` pre-commit hook

**Linting:**
- Ruff with rule sets: E, W (pycodestyle), F (pyflakes), D (pydocstyle, Google convention), I (isort), TID (tidy imports), B (flake8-bugbear), S (bandit), UP (pyupgrade)
- pylint run against all `src/` and `tests/` directories
- vulture checks for dead code at 80% confidence
- bandit security checks in pre-commit (excludes tests/)
- Tests exempt from D (docstring) and S101 (assert) rules via `[tool.ruff.lint.per-file-ignores]`

**Type Checking:**
- mypy via `uv run python scripts/check_types.py`
- Full type annotations on all public functions and methods
- `TYPE_CHECKING` guard for imports only needed in type signatures
- `# type: ignore[arg-type]` used sparingly where third-party stubs are incomplete

## Module-Level Docstrings

Every source file has a module docstring with the format:
```python
"""axiom.{full.namespace}.{module} — Short description of what this module provides."""
```

Examples:
- `"""axiom.cache.decorators.cached — @cached decorator for function result caching."""`
- `"""axiom.fastapi.app.builder — create_app() factory function."""`
- `"""axiom.core.exceptions.base — Base exception and error detail schema."""`

## Import Organization

**Order (enforced by ruff isort):**
1. Standard library (`abc`, `inspect`, `functools`, `typing`)
2. Third-party packages (`pydantic`, `structlog`, `fastapi`, `sqlalchemy`)
3. First-party `axiom.*` imports

**Path Aliases:**
- No path aliases — all imports use full dotted package paths: `from axiom.cache.base import AsyncCacheBackend`
- `axiom` is declared `known-first-party` in ruff isort config

**Conditional Imports:**
- Heavy optional imports done inside functions to avoid import-time errors: `from axiom.fastapi.exception_handler import register_all_handlers` inside `create_app()`
- `TYPE_CHECKING` block for type-only imports

**`__all__` Lists:**
- Defined in `__init__.py` files when the module re-exports symbols from submodules
- Alphabetically sorted
- Example: `axiom-core/src/axiom/core/exceptions/__init__.py`

## Error Handling

**Hierarchy:**
- All domain errors extend `BaseError` from `axiom.core.exceptions.base`
- `BaseError` carries: `message: str`, `code: str`, `status_code: int`, `details: dict`
- HTTP subclasses in `axiom.core.exceptions.http`: `NotFoundError`, `ValidationError`, `ConflictError`, `AuthenticationError`, `AuthorizationError`, `BadRequestError`, `UnprocessableError`, `InternalError`
- `code` and `status_code` are class attributes — instances can override via constructor arg

**Raising Exceptions:**
- Raise typed domain exceptions, not raw `Exception` or `ValueError`: `raise BadRequestError("field not found")`
- Backends that wrap external libraries catch specific exceptions and return structured result objects (`SendResult(success=False, error=str(exc))`) rather than re-raising

**Exception Packages:**
- Every sub-package has an `exception/` sub-package containing package-specific exceptions
- Docstring convention: `"""axiom.{ns}.exception — Exceptions for the axiom.{ns} package."""`

**FastAPI Exception Handlers:**
- `BaseError` → `_domain_handler` returns `JSONResponse` with `ErrorDetail.model_dump()`
- `HTTPException` → normalized to same `ErrorDetail` shape with code `http_{status}`
- Unhandled exceptions → `500` with `code = "internal_error"`
- Validation errors → `422` with `code = "validation_error"`

## Logging

**Framework:** structlog

**Pattern:**
```python
import structlog
logger = structlog.get_logger(__name__)

# Structured key=value pairs, not f-strings
logger.info("request.incoming", method=method, path=path, request_id=request_id)
logger.exception("domain_error", exc_info=exc)
logger.warning("send_failed", ...)
```

**Conventions:**
- Logger is module-level constant named `logger`
- Event name uses dot notation: `"request.incoming"`, `"request.outgoing"`, `"domain_error"`
- Contextual data passed as keyword arguments, never interpolated into the event string
- 5xx errors are logged at `exception` level; 4xx are not logged by default

## Async/Sync Parity

Every service with I/O provides both async and sync variants:
- `AsyncRedisClient` / `SyncRedisClient`
- `AsyncCacheBackend` / `SyncCacheBackend`
- `AsyncMailClient` / `SyncMailClient`
- `AsyncSQLiteRepository` / `SyncSQLiteRepository`

Async files named `async_.py`, sync files named `sync.py` within the same sub-package.

## Comments

**When to Comment:**
- Inline comments explain non-obvious logic, not trivial code
- `# Resolve client IP` style used for multi-step logic blocks
- `# noqa: D100, D101, D102, D103` placed at file top for test files where docstrings are omitted

**JSDoc/Google Docstrings:**
- All public classes and functions have Google-style docstrings
- Args/Returns/Raises sections used when the signature is not self-explanatory
- Abstract methods document contract via docstring only (no implementation)

## Pydantic Usage

- Settings: `BaseAppSettings(BaseSettings)` from `pydantic_settings`, env vars auto-loaded from `.env`
- Config objects: `AppConfig(BaseModel)` with validators via `@model_validator(mode="after")`
- `model_config = {"arbitrary_types_allowed": True}` when non-Pydantic types are used as fields
- `ErrorDetail(BaseModel)` for serializing exceptions to API response body

## Function Design

**Size:** Functions are kept small and single-purpose. Largest source files cap at ~666 lines (abstract controller).

**Parameters:** Keyword-only parameters enforced with `*` for non-positional config params:
```python
def __init__(self, app: Any, *, request_id_header: str = _DEFAULT_REQUEST_ID_HEADER) -> None:
```

**Return Values:** Explicit return type annotations on all functions. `None` return type stated explicitly where applicable.

## Module Design

**Exports:**
- Sub-package `__init__.py` re-exports the public API of that sub-package
- Implementation details kept in named submodules (`function_key_maker.py`, `middleware.py`)
- `__all__` defined wherever `__init__.py` consolidates exports

**Barrel Files:**
- Used at sub-package level (e.g., `axiom/cache/base/__init__.py` exports `AsyncCacheBackend`, `SyncCacheBackend`)
- Not used at top-level package to avoid heavy import chains; consumers import specific submodules

---

*Convention analysis: 2026-04-07*
