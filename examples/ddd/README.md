# DDD — Golden Path

Паттерн `endpoint → controller → use case → repository` для сервисов с насыщенной доменной логикой.

**Canonical references:**
- `docs/patterns.md` — полный справочник всех правил
- `axiom-core/src/axiom/core/entities/domain.py` — `BaseDomainDC`
- `axiom-core/src/axiom/core/entities/schema.py` — `BaseRequestSchema`, `BaseResponseSchema`

---

## Когда использовать

- бизнес-правила требуют координации нескольких агрегатов в одном сценарии
- нужна явная граница между application layer и persistence layer
- сервис развивается долго и важно не смешивать HTTP-контракт с доменной моделью

Если логика умещается в один CRUD-вызов — используй [CRUD-паттерн](../crud/README.md).

---

## 1. Domain Entity (dataclass, не Pydantic)

```python
# domain/entities/order.py
from dataclasses import dataclass, field
from uuid import UUID

from axiom.core.entities.domain import BaseDomainDC


@dataclass
class Order(BaseDomainDC):
    user_id: UUID
    status: str = "draft"
    total: float = 0.0
    items: list["OrderItem"] = field(default_factory=list)

    def submit(self) -> None:
        if not self.items:
            raise ValueError("Cannot submit empty order")
        self.status = "submitted"

    def cancel(self) -> None:
        if self.status == "submitted":
            raise ValueError("Cannot cancel submitted order")
        self.status = "cancelled"
```

- `BaseDomainDC` даёт: `id: UUID`, `created_at`, `updated_at`, `to_dict()`, `from_dict()`
- Доменная логика (`submit`, `cancel`) живёт здесь — не в контроллере и не в use case
- Не зависит от FastAPI, SQLAlchemy, Pydantic

---

## 2. ORM Model (отдельно от domain entity)

```python
# infrastructure/models/order.py
from uuid import UUID
from sqlalchemy import VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from axiom.oltp.sqlalchemy.base.declarative import Base
from axiom.oltp.sqlalchemy.base.mixin.as_dict import AsDictMixin
from axiom.oltp.sqlalchemy.base.mixin.timestamp import TimestampMixin


class OrderModel(AsDictMixin, TimestampMixin, Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(VARCHAR(64), nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    total: Mapped[float] = mapped_column(default=0.0)
```

ORM-модель — это инфраструктурная деталь, не доменный объект. Они существуют параллельно.

---

## 3. Repository

```python
# infrastructure/repositories/order.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from axiom.oltp.sqlalchemy.postgres.repository.async_ import AsyncPostgresRepository

from infrastructure.models.order import OrderModel


class OrderRepository(AsyncPostgresRepository[OrderModel, AsyncSession, Select]):
    pass
```

---

## 4. Pydantic Schemas (только на HTTP-границе)

```python
# api/schemas/order.py
from uuid import UUID
from pydantic import Field
from axiom.core.entities.schema import BaseRequestSchema, BaseResponseSchema


class SubmitOrderRequest(BaseRequestSchema):
    order_id: UUID


class OrderResponse(BaseResponseSchema):
    id: UUID
    status: str
    user_id: UUID | None
    total: float
```

---

## 5. Use Case (application layer)

```python
# domain/use_cases/submit_order.py
from uuid import UUID

from axiom.core.exceptions.http import ForbiddenError, NotFoundError

from domain.entities.order import Order
from infrastructure.repositories.order import OrderRepository


class SubmitOrderUseCase:
    """Coordinate submitting an order: validate ownership, apply domain logic, persist."""

    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    async def execute(self, order_id: UUID, requesting_user_id: UUID) -> OrderModel:
        model = await self._order_repository.get_by(
            field="id", value=order_id, unique=True
        )
        if model is None:
            raise NotFoundError(f"Order {order_id} not found")

        # маппим ORM → domain entity для применения бизнес-логики
        order = Order.from_dict(model.as_dict())
        if order.user_id != requesting_user_id:
            raise ForbiddenError("Not your order")

        order.submit()  # доменная логика живёт в entity

        return await self._order_repository.update(model, {"status": order.status})
```

Use case:
- координирует репозитории и domain entities
- не знает про FastAPI, сессии, транзакции — это ответственность контроллера
- не содержит persistence-логики — только оркестрацию

---

## 6. Controller

```python
# api/controllers/order.py
from uuid import UUID

from axiom.oltp.sqlalchemy.postgres.controller.async_ import AsyncPostgresController

from domain.use_cases.submit_order import SubmitOrderUseCase
from infrastructure.models.order import OrderModel
from infrastructure.repositories.order import OrderRepository


class OrderController(AsyncPostgresController[OrderModel]):
    def __init__(
        self,
        order_repository: OrderRepository,
        submit_order_use_case: SubmitOrderUseCase,
        exclude_fields: list[str],
    ) -> None:
        super().__init__(
            model=OrderModel,
            repository=order_repository,
            exclude_fields=exclude_fields,
        )
        self._submit_order = submit_order_use_case

    @AsyncPostgresController.transactional
    async def submit_order(self, order_id: UUID, user_id: UUID) -> OrderModel:
        return await self._submit_order.execute(order_id, user_id)
```

- `@transactional` — контроллер управляет транзакцией, use case — нет
- тонкий контроллер: делегирует в use case, не дублирует логику

---

## 7. Factory (DI-контейнер)

```python
# factory.py
from functools import partial
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.oltp.sqlalchemy.postgres.session import PostgresSession

from api.controllers.order import OrderController
from domain.use_cases.submit_order import SubmitOrderUseCase
from infrastructure.models.order import OrderModel
from infrastructure.repositories.order import OrderRepository
from settings import settings

db_session = PostgresSession(url=settings.DATABASE_URL)


class Factory:
    """Dependency injection container."""

    order_repository = partial(OrderRepository, model=OrderModel)

    def get_order_controller(
        self,
        session: AsyncSession = Depends(db_session),
    ) -> OrderController:
        repo = self.order_repository(db_session=session)
        use_case = SubmitOrderUseCase(order_repository=repo)
        return OrderController(
            order_repository=repo,
            submit_order_use_case=use_case,
            exclude_fields=settings.EXCLUDE_FIELDS,
        )
```

---

## 8. FastAPI Router

```python
# api/routers/order.py
from uuid import UUID

from loguru import logger
from fastapi import APIRouter, Depends

from api.controllers.order import OrderController
from api.schemas.order import OrderResponse, SubmitOrderRequest
from factory import Factory

router = APIRouter(prefix="/orders", tags=["Order"])


@router.post("/{order_id}/submit/", response_model=OrderResponse)
async def submit_order(
    order_id: UUID,
    body: SubmitOrderRequest,
    controller: OrderController = Depends(Factory().get_order_controller),
) -> OrderModel:
    """Подтвердить заказ."""
    logger.info("order.submit order_id={order_id}", order_id=order_id)
    return await controller.submit_order(
        order_id=order_id,
        user_id=body.user_id,
    )
```

---

## 9. Тесты

```python
# tests/test_submit_order.py
from uuid import uuid4

import pytest
from axiom.core.exceptions.http import ForbiddenError, NotFoundError

from domain.entities.order import Order


class TestOrderEntity:
    """Pure unit tests — no DB."""

    def test_submit_success(self):
        order = Order(user_id=uuid4(), status="draft")
        order.items = [object()]  # не пустой
        order.submit()
        assert order.status == "submitted"

    def test_submit_empty_raises(self):
        order = Order(user_id=uuid4(), status="draft")
        with pytest.raises(ValueError, match="empty"):
            order.submit()


class TestSubmitOrderUseCase:
    """Integration tests — real DB via SQLite in-memory."""

    async def test_submit_wrong_user_raises(self, use_case, persisted_order):
        with pytest.raises(ForbiddenError):
            await use_case.execute(persisted_order.id, requesting_user_id=uuid4())

    async def test_submit_not_found_raises(self, use_case):
        with pytest.raises(NotFoundError):
            await use_case.execute(uuid4(), requesting_user_id=uuid4())
```

Стратегия:
- domain entity — чистые unit-тесты, без фикстур
- use case — integration тест с in-memory SQLite
- controller/router — тест транзакционности через `TestClient` или `AsyncClient`

---

## Итоговая структура

```
app/
├── api/
│   ├── controllers/
│   │   └── order.py          ← тонкий, делегирует в use case
│   ├── routers/
│   │   └── order.py          ← FastAPI endpoints
│   └── schemas/
│       └── order.py          ← Request/Response (Pydantic, только HTTP boundary)
├── domain/
│   ├── entities/
│   │   └── order.py          ← dataclass, бизнес-логика
│   └── use_cases/
│       └── submit_order.py   ← оркестрация сценария
├── infrastructure/
│   ├── models/
│   │   └── order.py          ← ORM model (SQLAlchemy)
│   └── repositories/
│       └── order.py          ← OrderRepository
├── factory.py                ← DI container
└── settings.py               ← AppSettings
```

---

## Разница CRUD vs DDD

| | CRUD | DDD |
|---|---|---|
| Логика | в контроллере (минимальная) | в domain entity + use case |
| Domain entity | нет | `@dataclass(BaseDomainDC)` |
| Use case | нет | отдельный класс |
| ORM model | = рабочая модель | отдельно от domain entity |
| Когда | простые CRUD, admin API | сложные бизнес-сценарии |
