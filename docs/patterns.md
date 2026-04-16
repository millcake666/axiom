# Patterns

Это инженерный справочник повторяющихся паттернов кодовой базы.
Не дублирует [`ARCHITECTURE.md`](architecture.md) (что есть) и [`CONVENTIONS.md`](../.planning/codebase/CONVENTIONS.md) (как называть).
Отвечает на вопрос **«как это пишется у нас»**.

---

## Новый пакет / плагин

```
axiom-{name}/
├── pyproject.toml                  # hatchling, packages=["src/axiom"]
└── src/axiom/{name}/
    ├── __init__.py                 # __version__, re-exports, __all__
    └── exception/
        └── __init__.py             # пакет-специфичные исключения
```

**Checklist:**

1. Добавить `"axiom-{name}"` в `[tool.uv.workspace] members` в корневом `pyproject.toml`.
2. `src/axiom/` и `src/axiom/oltp/` / `src/axiom/olap/` — namespace packages без `__init__.py`.
3. `src/axiom/{name}/__init__.py` обязательно содержит `__version__ = "0.1.0"`.
4. Каждый sub-package получает свой `exception/` sub-package (см. раздел [Exceptions](#exceptions)).
5. Создать `axiom-{name}/tests/` с `__init__.py` и `conftest.py`.
6. Для пакетов с I/O — реализовать и async-, и sync-варианты (см. [Async/sync parity](#asyncsync-parity)).

**Canonical example:** `axiom-cache/` — полный, зрелый пакет с ABCs, реализациями, декораторами, тестами.

---

## Public API пакета

`__init__.py` пакета — единственная точка публичного API. Всё, что нужно потребителю, реэкспортируется здесь с явным `__all__`.

```python
"""axiom.cache — Caching abstractions with in-memory and Redis backends."""

__version__ = "0.1.0"

from axiom.cache.base import AsyncCacheBackend, SyncCacheBackend
from axiom.cache.decorators.cached import cached
from axiom.cache.exception import CacheError, CacheConnectionError

__all__ = [
    "AsyncCacheBackend",
    "CacheConnectionError",
    "CacheError",
    "SyncCacheBackend",
    "cached",
]
```

**Правила:**
- `__all__` сортируется алфавитно.
- Внутренние хелперы с `_` prefix в `__all__` не попадают.
- Не экспортируй всё подряд — только то, что является явным контрактом пакета.
- Barrel imports (`from axiom.cache import *`) допустимы только в самом пакете, не в приложениях.

---

## Settings

```python
# В пакете — настройки конкретной интеграции
class RedisSettings(BaseAppSettings):
    REDIS_URL: str = "redis://localhost:6379/0"

# В сервисе — compose через множественное наследование
class AppSettings(BaseAppSettings, AppMixin, DebugMixin):
    pass

settings = AppSettings()
```

- Все settings наследуются от `BaseAppSettings` из `axiom.core.settings`.
- `AppMixin` даёт: `APP_HOST`, `APP_PORT`, `APP_STAGE`, `APP_NAME`.
- `DebugMixin` даёт: `DEBUG`.
- `make_env_prefix("my-service")` → `"MY_SERVICE_"` — используй для изоляции env vars интеграции.
- `{Name}Settings` — для env-based конфигурации (Pydantic Settings).
- `{Name}Config` — для структурированной конфигурации объекта (plain Pydantic Model), не завязанной на `.env`.

**Reference:** `axiom-core/src/axiom/core/settings/base.py`, `axiom-redis/src/axiom/redis/settings.py`

---

## Domain layer

### Доменная сущность

```python
@dataclass
class Order(BaseDomainDC):
    user_id: UUID
    status: str = "draft"
    items: list[OrderItem] = field(default_factory=list)
```

- `BaseDomainDC` даёт: `id: UUID`, `created_at`, `updated_at`, `to_dict()`, `from_dict()`, equality/hash по `id`.
- Используй только для чистых доменных объектов, не для ORM-моделей.
- ORM-модели наследуют `Base`, `TimestampMixin`, `AsDictMixin` — это другой слой.

### Pydantic schemas (DTO)

```python
# Запрос — без ORM mode
class CreateOrderRequest(BaseRequestSchema):
    user_id: UUID = Field(..., examples=["..."])
    items: list[OrderItemRequest]

# Ответ — с ORM mode (from_attributes=True)
class OrderResponse(BaseResponseSchema):
    id: UUID
    status: str
    created_at: datetime

# Если нужен alias в ответе
response.model_response()  # → dict с alias-ключами
```

- `BaseRequestSchema` — входящий payload (нет `from_attributes`).
- `BaseResponseSchema` — исходящий ответ (есть `from_attributes=True`).
- `BaseSchema` — когда нужен ORM mode, но не явный ответ API.
- `model_config` всегда объявляется первым в теле класса.
- Для статусных полей — `StrEnum`, не `@field_validator`.
- `PaginatedResponse[T]` — стандартная обёртка для paginated списков.

**Reference:** `axiom-core/src/axiom/core/entities/schema.py`, `axiom-core/src/axiom/core/entities/domain.py`

---

## ORM Model (SQLAlchemy)

```python
class Order(Base, TimestampMixin, AsDictMixin):
    # __tablename__ не указывается — автогенерируется через to_snake()
    # Order → "order", OrderItem → "order_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)

    # Все relationships — lazy="selectin" для избежания N+1
    items: Mapped[list["OrderItem"]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
    )
```

- `Base` из `axiom.oltp.sqlalchemy` — declarative base с `to_snake()`.
- `TimestampMixin` — `created_at`, `updated_at` (UTC, server_default).
- `AsDictMixin` — `as_dict(exclude_none=False)`.
- `ondelete=CASCADE` для дочерних записей, `SET NULL` для опциональных связей, `RESTRICT` для защиты.
- Тип `VARCHAR(n)` предпочтительнее `String(n)` — явная длина.

**Reference:** `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/base/mixin/`

---

## Repository layer

```python
# Простой случай — никакого тела
class OrderRepository(AsyncPostgresRepository[Order, AsyncSession, Select]):
    pass

# Кастомный метод — только если базового API недостаточно
class OrderRepository(AsyncPostgresRepository[Order, AsyncSession, Select]):
    async def get_recent_by_user(self, user_id: UUID, limit: int = 10) -> list[Order]:
        query = self._query().where(Order.user_id == user_id).limit(limit)
        return await self._all(query)
```

**Правило:** репозиторий — это только persistence. Никакой бизнес-логики, никаких исключений типа `NotFoundError`. Базовый API покрывает 90% случаев:

| Задача | Метод |
|---|---|
| Получить по полю | `get_by(field="user_id", value=uid)` |
| Получить один | `get_by(..., unique=True)` |
| Фильтрация | `get_by_filters(filter_request=...)` |
| Список с пагинацией | `get_all(skip=0, limit=20, sort_by="created_at")` |
| Создать | `create({"field": value})` |
| Обновить | `update(model, {"field": value})` |
| Upsert | `create_or_update_by(attributes, update_fields=[...])` |
| Кол-во | `count(filter_request=...)` |

**FilterRequest:**
```python
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator

# Простой
filter_request = FilterRequest(
    chain=FilterParam(field="status", value="active", operator=QueryOperator.EQUALS)
)

# Составной через операторы &/|
filter_request = FilterRequest(
    chain=FilterParam(field="status", value="active", operator=QueryOperator.EQUALS)
        & FilterParam(field="user_id", value=uid, operator=QueryOperator.EQUALS)
)
```

**Трёхслойная иерархия репозиториев:**
```
abs/repository/async_.py     ← AsyncBaseRepository (контракт)
base/repository/async_.py    ← AsyncSQLAlchemyRepository (реализация)
postgres/repository/async_.py← AsyncPostgresRepository (диалект)
```
Наследуй всегда от самого конкретного: `AsyncPostgresRepository` для Postgres, `AsyncSQLiteRepository` для SQLite.

**Reference:** `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/repository/async_.py`

---

## Controller / Service layer

```python
class OrderController(AsyncPostgresController[Order]):
    def __init__(
        self,
        order_repository: OrderRepository,
        exclude_fields: list[str],
    ) -> None:
        super().__init__(
            model=Order,
            repository=order_repository,
            exclude_fields=exclude_fields,
        )
        self.order_repository = order_repository
```

Базовый контроллер уже реализует: `create`, `create_many`, `get_by_id`, `get_by_uuid`, `get_all`, `get_by`, `get_by_filters`, `update`, `update_by_id`, `update_by_uuid`, `delete`, `delete_by_id`, `delete_by_uuid`, `count`.

**Не переопределяй базовые методы без нужды.** Вызывай напрямую из эндпоинта:
```python
return await order_controller.create(attributes.model_dump())
return await order_controller.update_by_id(id_=order_id, attributes=request.model_dump(exclude_unset=True))
return await order_controller.delete_by_id(order_id)
```

**Кастомная логика** — только когда бизнес-сценарий выходит за пределы одного CRUD:
```python
@AsyncPostgresController.transactional
async def submit_order(self, order_id: int, user_id: UUID) -> Order:
    order = await self.get_by_id(order_id)
    if order.user_id != user_id:
        raise ForbiddenError("Not your order")
    return await self.order_repository.update(order, {"status": "submitted"})
```

- `@transactional` оборачивает метод в `processing_transaction()` — всегда используй для мутирующих методов с кастомной логикой.
- `extract_attributes_from_schema(schema, excludes={...})` → `dict` — конвертация Pydantic → dict при необходимости исключить поля.

**Мультирепозиторный контроллер** (когда нужен доступ к нескольким агрегатам):
```python
class OrderController(AsyncPostgresController[Order]):
    def __init__(self, order_repo, product_repo, exclude_fields):
        super().__init__(model=Order, repository=order_repo, exclude_fields=exclude_fields)
        self.product_repository = product_repo  # дополнительный репозиторий
```

**Reference:** `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/controller/async_.py`, `merrai/api/src/app/controller/portfolio.py`

---

## Factory (DI-контейнер)

Factory — стандартный способ сборки контроллеров в приложении на базе axiom.

```python
class Factory:
    """Dependency injection container."""

    # Repositories — partial с привязкой модели
    order_repository = partial(OrderRepository, model=Order)
    product_repository = partial(ProductRepository, model=Product)

    def get_order_controller(
        self,
        session: AsyncSession = Depends(PostgresSession(db_session=db_session)),
    ) -> OrderController:
        return OrderController(
            order_repository=self.order_repository(db_session=session),
            exclude_fields=settings.EXCLUDE_FIELDS,
        )
```

- Репозитории объявляются как `partial(Repository, model=Model)` — class-level атрибуты.
- Каждый `get_{entity}_controller` принимает сессию через `Depends` и собирает граф зависимостей.
- Если контроллер зависит от другого — вызывай внутри factory: `self.get_product_controller(session)`.
- Imports контроллеров внутри функций (отложенный импорт) — стандартная практика для разрыва циклических зависимостей.

**Reference:** `merrai/api/src/app/factory/factory.py`, `pushok-backend-user/src/app/factory/factory.py`

---

## HTTP Endpoints (FastAPI)

```python
from loguru import logger
from fastapi import APIRouter, Depends
from axiom.core.schema.response import PaginationResponse

router = APIRouter(tags=["Order"])

@router.post("/", response_model=OrderResponse)
async def create_order(
    attributes: CreateOrderRequest,
    order_controller: OrderController = Depends(Factory().get_order_controller),
) -> Order:
    """Создать заказ."""
    logger.info("Create order user_id={user_id}", user_id=attributes.user_id)
    return await order_controller.create(attributes.model_dump())

@router.get("/", response_model=PaginationResponse[OrderResponse])
async def get_orders(
    pagination: PaginationParams = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    order_controller: OrderController = Depends(Factory().get_order_controller),
) -> PaginationResponse:
    """Получить список заказов."""
    logger.info("Get orders list")
    return await order_controller.get_all(
        skip=pagination.skip,
        limit=pagination.limit,
        sort_by=sort.sort_by,
        sort_type=sort.sort_type,
    )

@router.patch("/{order_id}/", response_model=OrderResponse)
async def update_order(
    order_id: int,
    attributes: UpdateOrderRequest,
    order_controller: OrderController = Depends(Factory().get_order_controller),
) -> Order:
    """Обновить заказ."""
    logger.info("Update order order_id={order_id}", order_id=order_id)
    return await order_controller.update_by_id(
        id_=order_id,
        attributes=attributes.model_dump(exclude_unset=True),
    )
```

**Правила:**
- `status_code` в декораторе не указывается явно (только когда нужен не 200, например `201`).
- Функция возвращает ORM-модель; FastAPI маппит через `response_model`.
- `attributes.model_dump(exclude_unset=True)` — всегда для PATCH.
- `logger.info(...)` — в каждом эндпоинте, structured kwargs, не f-строки.
- Auth без данных пользователя: `dependencies=[Depends(Auth().require_auth)]`.
- Auth с данными пользователя: inject как параметр функции.

---

## FastAPI infra sub-system: lifespan + app.state

Для инфраструктурных компонентов уровня приложения, которым нужен lifecycle и доступ из middleware/dependency, используем отдельный service + typed accessor к `app.state`.

```python
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from axiom.fastapi.rate_limiter import (
    IPPolicy,
    RateLimitConfig,
    rate_limit,
    rate_limiter_lifespan,
)

config = RateLimitConfig(policies=[IPPolicy(limit="100/minute")])


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with rate_limiter_lifespan(app, config):
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/items", dependencies=[Depends(rate_limit("10/minute"))])
async def list_items() -> dict[str, list[object]]:
    return {"items": []}
```

**Правила:**
- Инициализируй backend/service один раз на app lifespan, а не на каждый запрос.
- Храни long-lived service в `app.state` через `AppStateManager`, а не через разрозненные `getattr(...)` по коду.
- Middleware и dependencies должны разделять один и тот же service instance.
- `Settings` используются для env-based wiring, `Config` — для программной сборки объекта.

**Reference:** `axiom-fastapi/src/axiom/fastapi/app/state.py`, `axiom-fastapi/src/axiom/fastapi/rate_limiter/service.py`, `axiom-fastapi/src/axiom/fastapi/rate_limiter/dependency.py`

---

## Exceptions

### Иерархия

```
Exception
└── BaseError (axiom.core.exceptions.base)
    ├── NotFoundError (404)
    ├── BadRequestError (400)
    ├── ValidationError (422)
    ├── ConflictError (409)
    ├── AuthenticationError (401)
    ├── AuthorizationError (403)
    ├── UnprocessableError (422)
    └── InternalError (500)
```

### Пакет-специфичные исключения

Каждый пакет и каждый sub-package имеет `exception/` sub-package. Ошибки наследуются от `BaseError`:

```python
# axiom-{name}/src/axiom/{name}/exception/__init__.py
"""axiom.{name}.exception — Exceptions for the axiom.{name} package."""

from axiom.core.exceptions.base import BaseError


class AxiomCacheError(BaseError):
    """Base exception for axiom.cache."""
    code = "cache_error"
    status_code = 500


class CacheConnectionError(AxiomCacheError):
    """Raised when a connection to the cache backend fails."""
    code = "cache_connection_error"
    status_code = 503
```

**Правила:**
- Всегда наследуй от `BaseError`, не от голого `Exception`.
- `code` и `status_code` — class-level атрибуты, не параметры конструктора.
- Не ре-рейзи исключения сторонних библиотек наружу — оборачивай в свои.
- Backend-уровень возвращает `SendResult(success=False, error=str(exc))` вместо броска исключения когда это semantically корректно (как в `axiom-email`).
- `NotFoundError`, `BadRequestError` и другие HTTP-типы из `axiom.core.exceptions.http` — используй напрямую в контроллере.

**Reference:** `axiom-core/src/axiom/core/exceptions/base.py`, `axiom-cache/src/axiom/cache/exception/__init__.py`

---

## Plugin extensibility: ABC vs Protocol

**ABC** — когда реализация разделяет общий lifecycle и state:
```python
# Наследник ОБЯЗАН реализовать все @abstractmethod
class AsyncCacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any | None: ...
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...
```
Используй для: cache backends, object store backends, репозиториев.

**Protocol** — когда важна structural subtyping без наследования (duck typing):
```python
@runtime_checkable
class AsyncMailBackend(Protocol):
    async def send(self, message: EmailMessage) -> SendResult: ...
    async def startup(self) -> None: ...
    async def shutdown(self) -> None: ...
```
Используй для: email backends, template renderers, hooks — любой случай, когда реализация может прийти извне без зависимости от axiom.

**Правило выбора:** если потребитель плагина — внутренний код axiom, используй ABC. Если потребитель может быть внешним и не хочет наследоваться от axiom — Protocol.

**Reference:** `axiom-cache/src/axiom/cache/base/__init__.py` (ABC), `axiom-email/src/axiom/email/interfaces.py` (Protocol)

---

## Async/sync parity

Каждый сервис с I/O реализует обе версии:

```
axiom-cache/src/axiom/cache/
├── base/
│   └── __init__.py          # AsyncCacheBackend, SyncCacheBackend
├── redis/
│   ├── async_backend.py     # AsyncRedisCache
│   └── sync_backend.py      # SyncRedisCache
└── inmemory/
    ├── async_backend.py     # AsyncInMemoryCache
    └── sync_backend.py      # SyncInMemoryCache
```

- Async файлы: `async_.py` (не `async.py` — keyword collision).
- Sync файлы: `sync.py`.
- Классы: `Async{Name}` / `Sync{Name}`.
- Async и sync варианты имеют идентичный публичный API.

---

## Logging

**Канонический способ — только loguru:**
```python
from axiom.core.logger import get_logger

logger = get_logger("axiom.cache.redis")  # в пакетах axiom
```
```python
from loguru import logger  # в приложениях (endpoints, controllers)
```

**Формат event:**
```python
# Структурированные kwargs — не f-строки
logger.info("Create order user_id={user_id}", user_id=user_id)
logger.info("request.incoming", method=method, path=path, request_id=request_id)
logger.exception("cache.miss", key=key, exc_info=exc)
logger.warning("send_failed", backend=backend_name, error=str(exc))
```

**Уровни:**
- `info` — нормальные операции, входящие запросы.
- `warning` — degrade без падения (retry, fallback).
- `error` — ожидаемые ошибки операций (4xx).
- `exception` — неожиданные ошибки с traceback (5xx).

**Важно:** `axiom-fastapi` в текущем коде использует `structlog` — это известное несоответствие (см. `CONCERNS.md`). Все новые пакеты и приложения используют `loguru` через `axiom.core.logger`.

---

## Tests

### Структура

```
axiom-{name}/
└── tests/
    ├── __init__.py
    ├── conftest.py           # сессия, engine, базовые fixtures
    ├── fixtures/
    │   └── models.py         # тестовые ORM-модели (не production-модели)
    ├── unit/                 # тесты без внешних сервисов
    │   └── test_*.py
    └── integration/          # тесты с реальными сервисами
        ├── conftest.py
        └── test_*.py
```

### Матрица fakes

| Backend | Fake |
|---|---|
| Redis | `fakeredis` / `fakeredis.aioredis` |
| PostgreSQL / SQLite | in-memory SQLite (`sqlite+aiosqlite:///:memory:`) |
| MongoDB / Beanie | `mongomock` + `mongomock_motor.AsyncMongoMockClient` |
| Email | `axiom.email.testing.AsyncInMemoryMailBackend` |
| SMTP (real) | `testcontainers[mailpit]` — `MailpitContainer` |

**Не мокай клиентские библиотеки** — используй fakes. Мокай только внешние сетевые вызовы (`aiosmtplib.send`) или logger-методы при проверке что событие было залогировано.

### Паттерны

```python
# asyncio_mode = "auto" — @pytest.mark.asyncio не нужен
async def test_create(self, repo: OrderRepository) -> None:
    """Order is persisted and returned with id."""
    order = await repo.create({"user_id": uuid4(), "status": "draft"})
    await repo.session.flush()
    assert order.id is not None

# Test data factory — helper-функция с defaults
def _make_order(**kwargs: Any) -> dict[str, Any]:
    defaults = {"user_id": uuid4(), "status": "draft"}
    defaults.update(kwargs)
    return defaults

# Error path
async def test_not_found_raises(self, controller: OrderController) -> None:
    with pytest.raises(NotFoundError):
        await controller.get_by_id(99999)

# Docker-based интеграция — module scope
@pytest.fixture(scope="module")
def mailpit():
    with MailpitContainer(image="axllent/mailpit:v1.21") as container:
        yield container
```

**Классовая группировка** предпочтительна когда тестируется async+sync parity или связный feature group.

**Reference:** `axiom-cache/tests/`, `axiom-email/tests/`, `oltp/axiom-sqlalchemy/tests/`

---

## When adding new functionality

1. **Покрой тестами** — минимум unit tests; integration tests если компонент взаимодействует с внешним сервисом.
2. **Выбери правильный fake** по матрице выше, не мокай клиента.
3. **Покрой error paths** — `NotFoundError`, невалидные данные, сетевые сбои.
4. **Запусти `make test`** — все пакеты должны проходить.
5. **Запусти `make check-precommit`** — ruff, mypy, bandit, vulture.
6. **Обнови README** — пакетный README + модульные README + `/docs/*.md` если паттерн изменился.
7. **Обнови `__all__`** в `__init__.py` при добавлении новых публичных символов.

---

## Good patterns

| Pattern | Пример |
|---|---|
| `pass`-репозиторий — наследуй базовый без тела | `class OrderRepo(AsyncPostgresRepository[Order, ...]): pass` |
| Factory как DI-контейнер | `Factory().get_order_controller` в `Depends` |
| `@transactional` для мутирующей кастомной логики | `@AsyncPostgresController.transactional` |
| `exclude_unset=True` для PATCH | `request.model_dump(exclude_unset=True)` |
| Structured logging kwargs | `logger.info("verb entity {f}", f=v)` |
| `AsyncInMemoryMailBackend` в тестах email | без реального SMTP |
| Protocol для внешних расширений | `AsyncMailBackend`, `MailHook` |
| ABC для внутренних расширений | `AsyncCacheBackend` |
| Lifespan + `AppStateManager` для app-wide infra | `RateLimiterService` в `app.state` |
| `exception/` sub-package в каждом пакете | extends `BaseError` |
| `lazy="selectin"` для relationships | избегает N+1 |

## Anti-patterns

| Anti-pattern | Почему плохо |
|---|---|
| Бизнес-логика в репозитории | Нарушает SRP; логика выпадает из транзакции контроллера |
| `raise Exception(...)` или `raise ValueError(...)` | Не ловится `register_all_handlers`; нет машиночитаемого `code` |
| Пакет-специфичные исключения без `BaseError` | Не интегрируются с FastAPI exception handlers |
| Мок Redis-клиента в тестах | `fakeredis` точнее; мок не воспроизводит TTL и паттерн-поиск |
| `model_dump()` без `exclude_unset=True` для PATCH | Перезаписывает поля, которые не менялись |
| `from axiom.cache.redis.async_backend import AsyncRedisCache` | Импортируй из `axiom.cache`, не из внутренних модулей |
| `structlog` в новых пакетах | Canonical logger — `loguru` через `axiom.core.logger` |
| Создавать backend/service внутри dependency на каждый запрос | Ломает lifecycle и дублирует stateful infra |
| Добавлять поля в `exclude_fields` глобально в settings | Лучше передавать явно в `super().__init__(..., exclude_fields=list)` |

---

## ClickHouse Repository

`axiom-clickhouse` предоставляет OLAP-репозиторий поверх ClickHouse (через `clickhouse-connect`).
Полная документация: [`olap/axiom-clickhouse/README.md`](../olap/axiom-clickhouse/README.md).

### Быстрый пример

```python
from axiom.olap.clickhouse import ClickHouseRepository, ClickHouseSettings

settings = ClickHouseSettings()  # читает из env vars
repo = ClickHouseRepository.from_settings(settings, table="events", database="analytics")

# Read
result = repo.fetch_all()              # QueryResult[dict]
paged = repo.fetch_paged(spec)         # PagedResult[dict]

# Write
repo.insert_many(rows)                 # BulkInsertResult
repo.insert_chunked(rows, 10_000)      # partial failure tolerant

# Aggregation
from axiom.olap.clickhouse import AggregateSpec, GroupBySpec, MetricSpec, AggFunction

result = repo.aggregate(AggregateSpec(
    metrics=[MetricSpec(function=AggFunction.COUNT, field="id", alias="n")],
    group_by=GroupBySpec(fields=["event_type"]),
))

# Raw escape hatch
result = repo.raw("SELECT toDate(ts) day, count() FROM events GROUP BY day")
```

### Versioned/append сценарий

```python
from axiom.olap.clickhouse import VersionedClickHouseRepository

repo = VersionedClickHouseRepository.from_settings(
    settings, table="products", version_column="version", is_deleted_column="is_deleted"
)
repo.append_version(row={"product_id": 1, "price": 999}, version=1)
repo.soft_delete(id_column="product_id", id_value=1, version=2)
active = repo.read_active()
```

**Когда НЕ использовать `update_by_filter` / `delete_by_filter`:**
ClickHouse-мутации (`ALTER TABLE UPDATE/DELETE`) переписывают целые parts на диск и выполняются
асинхронно. Для частых изменений используй `VersionedClickHouseRepository` + `ReplacingMergeTree`.

---

## Canonical reference locations

| Что ищешь | Файл |
|---|---|
| Новый плагин (структура) | `axiom-cache/` — полный эталонный пакет |
| Public API / `__init__.py` | `axiom-cache/src/axiom/cache/__init__.py` |
| BaseError + ErrorDetail | `axiom-core/src/axiom/core/exceptions/base.py` |
| HTTP exception types | `axiom-core/src/axiom/core/exceptions/http.py` |
| Settings + mixins | `axiom-core/src/axiom/core/settings/base.py` |
| Domain entity | `axiom-core/src/axiom/core/entities/domain.py` |
| Request/Response schemas | `axiom-core/src/axiom/core/entities/schema.py` |
| FilterRequest DSL | `axiom-core/src/axiom/core/filter/expr.py` |
| ABC backend (cache) | `axiom-cache/src/axiom/cache/base/__init__.py` |
| Protocol backend (email) | `axiom-email/src/axiom/email/interfaces.py` |
| App-wide state accessor | `axiom-fastapi/src/axiom/fastapi/app/state.py` |
| Rate limiter lifecycle wiring | `axiom-fastapi/src/axiom/fastapi/rate_limiter/service.py` |
| AsyncMailClient (client с hooks) | `axiom-email/src/axiom/email/client.py` |
| AsyncBaseRepository | `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/repository/async_.py` |
| AsyncBaseController | `oltp/axiom-sqlalchemy/src/axiom/oltp/sqlalchemy/abs/controller/async_.py` |
| Factory pattern | `merrai/api/src/app/factory/factory.py` |
| Endpoint pattern | `tender-perm-2026/api/AGENTS.md` → "API Router Patterns" |
| Test fixtures (DB) | `oltp/axiom-sqlalchemy/tests/conftest.py` |
| Test fixtures (email) | `axiom-email/tests/unit/`, `axiom-email/tests/integration/` |
