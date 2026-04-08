# CRUD — Golden Path

Паттерн `endpoint → controller → repository` для сервисов, где доменной логики нет или она тривиальна.

**Canonical references:**
- `docs/patterns.md` — полный справочник всех правил
- `oltp/axiom-sqlalchemy/tests/` — тестовые паттерны (conftest, fixtures, tests)

---

## Когда использовать

- административные API и internal tools
- простые CRUD-сервисы без бизнес-правил
- сервисы, где в контроллере нет кастомной логики или она минимальна

Если появляется логика, которая затрагивает несколько агрегатов или требует явного application layer — переходи к [DDD-паттерну](../ddd/README.md).

---

## 1. ORM Model

```python
# app/models/order.py
from sqlalchemy import VARCHAR, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from axiom.oltp.sqlalchemy.base.declarative import Base
from axiom.oltp.sqlalchemy.base.mixin.as_dict import AsDictMixin
from axiom.oltp.sqlalchemy.base.mixin.timestamp import TimestampMixin


class Order(AsDictMixin, TimestampMixin, Base):
    # __tablename__ генерируется автоматически: Order → "order"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    items: Mapped[list["OrderItem"]] = relationship(lazy="selectin", cascade="all, delete-orphan")
```

Правила:
- `__tablename__` не указывать — `to_snake()` генерирует автоматически
- `lazy="selectin"` для всех relationships — избегает N+1
- `AsDictMixin` даёт `as_dict()`, `TimestampMixin` даёт `created_at`, `updated_at`

---

## 2. Repository

```python
# app/repositories/order.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from axiom.oltp.sqlalchemy.postgres.repository.async_ import AsyncPostgresRepository

from app.models.order import Order


class OrderRepository(AsyncPostgresRepository[Order, AsyncSession, Select]):
    pass  # базовый API покрывает 90% случаев
```

Кастомный метод — только если базового API недостаточно:

```python
class OrderRepository(AsyncPostgresRepository[Order, AsyncSession, Select]):
    async def get_recent_by_user(self, user_id: int, limit: int = 10) -> list[Order]:
        query = self._query().where(Order.user_id == user_id).order_by(Order.created_at.desc()).limit(limit)
        return await self._all(query)
```

- Репозиторий — только persistence. Никакой бизнес-логики, никаких `NotFoundError`.
- Для PostgreSQL: `AsyncPostgresRepository`. Для тестов с SQLite: `AsyncSQLiteRepository`.

---

## 3. Pydantic Schemas

```python
# app/schemas/order.py
from uuid import UUID
from pydantic import Field
from axiom.core.entities.schema import BaseRequestSchema, BaseResponseSchema


class CreateOrderRequest(BaseRequestSchema):
    user_id: int = Field(..., examples=[42])
    status: str = Field(default="draft")


class UpdateOrderRequest(BaseRequestSchema):
    status: str | None = None


class OrderResponse(BaseResponseSchema):
    id: int
    status: str
    user_id: int | None
```

- `BaseRequestSchema` — входящий payload (нет `from_attributes`)
- `BaseResponseSchema` — исходящий ответ (есть `from_attributes=True`)
- `model_config = ConfigDict(...)` всегда первым в теле класса

---

## 4. Controller

```python
# app/controllers/order.py
from axiom.oltp.sqlalchemy.postgres.controller.async_ import AsyncPostgresController

from app.models.order import Order
from app.repositories.order import OrderRepository


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

Базовый контроллер уже реализует: `create`, `create_many`, `get_by_id`, `get_all`, `get_by`, `get_by_filters`, `update`, `update_by_id`, `delete`, `delete_by_id`, `count`.

Кастомная бизнес-логика — только когда сценарий выходит за пределы одного CRUD:

```python
    @AsyncPostgresController.transactional
    async def submit_order(self, order_id: int, user_id: int) -> Order:
        order = await self.get_by_id(order_id)
        if order.user_id != user_id:
            raise ForbiddenError("Not your order")
        return await self.order_repository.update(order, {"status": "submitted"})
```

- `@transactional` — для любого мутирующего метода с кастомной логикой
- Не переопределяй базовые методы без нужды

---

## 5. Factory (DI-контейнер)

```python
# app/factory.py
from functools import partial

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.oltp.sqlalchemy.postgres.session import PostgresSession

from app.controllers.order import OrderController
from app.models.order import Order
from app.repositories.order import OrderRepository
from app.settings import settings

db_session = PostgresSession(url=settings.DATABASE_URL)


class Factory:
    """Dependency injection container."""

    order_repository = partial(OrderRepository, model=Order)

    def get_order_controller(
        self,
        session: AsyncSession = Depends(db_session),
    ) -> OrderController:
        return OrderController(
            order_repository=self.order_repository(db_session=session),
            exclude_fields=settings.EXCLUDE_FIELDS,
        )
```

- Репозитории — `partial(Repository, model=Model)` как class-level атрибуты
- Каждый `get_{entity}_controller` принимает сессию через `Depends` и собирает граф
- Отложенные импорты внутри функций — стандартная практика для разрыва циклических зависимостей

---

## 6. FastAPI Router

```python
# app/api/order.py
from loguru import logger
from fastapi import APIRouter, Depends

from axiom.core.entities.schema import PaginatedResponse

from app.factory import Factory
from app.schemas.order import CreateOrderRequest, OrderResponse, UpdateOrderRequest

router = APIRouter(prefix="/orders", tags=["Order"])


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order(
    attributes: CreateOrderRequest,
    controller: OrderController = Depends(Factory().get_order_controller),
) -> Order:
    """Создать заказ."""
    logger.info("order.create user_id={user_id}", user_id=attributes.user_id)
    return await controller.create(attributes.model_dump())


@router.get("/", response_model=PaginatedResponse[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 20,
    controller: OrderController = Depends(Factory().get_order_controller),
) -> PaginatedResponse:
    """Список заказов."""
    logger.info("order.list skip={skip} limit={limit}", skip=skip, limit=limit)
    return await controller.get_all(skip=skip, limit=limit, sort_by="created_at")


@router.get("/{order_id}/", response_model=OrderResponse)
async def get_order(
    order_id: int,
    controller: OrderController = Depends(Factory().get_order_controller),
) -> Order:
    """Получить заказ по ID."""
    logger.info("order.get order_id={order_id}", order_id=order_id)
    return await controller.get_by_id(order_id)


@router.patch("/{order_id}/", response_model=OrderResponse)
async def update_order(
    order_id: int,
    attributes: UpdateOrderRequest,
    controller: OrderController = Depends(Factory().get_order_controller),
) -> Order:
    """Обновить заказ."""
    logger.info("order.update order_id={order_id}", order_id=order_id)
    return await controller.update_by_id(
        id_=order_id,
        attributes=attributes.model_dump(exclude_unset=True),  # ← ВСЕГДА для PATCH
    )


@router.delete("/{order_id}/", status_code=204)
async def delete_order(
    order_id: int,
    controller: OrderController = Depends(Factory().get_order_controller),
) -> None:
    """Удалить заказ."""
    logger.info("order.delete order_id={order_id}", order_id=order_id)
    await controller.delete_by_id(order_id)
```

Правила:
- `status_code` указывается только когда нужен не 200 (`201` для POST, `204` для DELETE)
- Функция возвращает ORM-модель; FastAPI маппит через `response_model`
- `exclude_unset=True` — **обязательно** для PATCH
- Логирование через `loguru`, structured kwargs, не f-строки

---

## 7. Тесты

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from axiom.oltp.sqlalchemy.base.declarative import Base
from app.models.order import Order  # noqa: F401 — register tables


@pytest.fixture
async def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(async_engine):
    factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest.fixture
def controller(session):
    from axiom.oltp.sqlalchemy.sqlite.controller.async_ import AsyncSQLiteController
    from app.repositories.order import OrderRepository

    repo = OrderRepository(model=Order, db_session=session)
    return AsyncSQLiteController(model=Order, repository=repo, exclude_fields=[])
```

```python
# tests/test_order_controller.py
import pytest
from axiom.core.exceptions.http import NotFoundError


def _order(**kwargs):
    return {"status": "draft", "user_id": 1, **kwargs}


class TestOrderController:
    async def test_create(self, controller):
        order = await controller.create(_order())
        assert order.id is not None
        assert order.status == "draft"

    async def test_get_by_id_not_found(self, controller):
        with pytest.raises(NotFoundError):
            await controller.get_by_id(99999)

    async def test_update(self, controller):
        order = await controller.create(_order())
        updated = await controller.update_by_id(order.id, {"status": "submitted"})
        assert updated.status == "submitted"

    async def test_delete(self, controller):
        order = await controller.create(_order())
        await controller.delete_by_id(order.id)
        with pytest.raises(NotFoundError):
            await controller.get_by_id(order.id)
```

- `asyncio_mode = "auto"` в `pytest.ini_options` — `@pytest.mark.asyncio` не нужен
- In-memory SQLite для unit/integration тестов без внешних сервисов
- `_order(**kwargs)` — helper с defaults для тестовых данных, не fixture

---

## Итоговая структура

```
app/
├── api/
│   └── order.py          ← router
├── controllers/
│   └── order.py          ← OrderController
├── models/
│   └── order.py          ← ORM model
├── repositories/
│   └── order.py          ← OrderRepository
├── schemas/
│   └── order.py          ← Request/Response schemas
├── factory.py            ← DI container
└── settings.py           ← AppSettings
```
