# axiom-sqlalchemy

`axiom-sqlalchemy` — relational OLTP-адаптер Axiom на базе SQLAlchemy.

Пакет строится вокруг связки `repository + controller + filter DSL`.

## Когда Использовать

Подходит, если вам нужен:

- CRUD/repository слой поверх SQLAlchemy;
- общий async и sync API;
- пагинация и count responses в одном стиле;
- nested field filters через dot notation;
- dialect-specific upsert для SQLite и PostgreSQL;
- middleware для request-scoped session context в FastAPI.

## Что Уже Реализовано

### Модели и utilities

- `Base`
- `TimestampMixin`
- `AsDictMixin`
- `to_snake`

### Репозитории

- `AsyncBaseRepository`, `SyncBaseRepository`
- `AsyncSQLAlchemyRepository`, `SyncSQLAlchemyRepository`
- `AsyncSQLiteRepository`, `SyncSQLiteRepository`
- `AsyncPostgresRepository`, `SyncPostgresRepository`

### Контроллеры

- `AsyncBaseController`, `SyncBaseController`
- `AsyncSQLAlchemyController`, `SyncSQLAlchemyController`
- `AsyncSQLiteController`, `SyncSQLiteController`
- `AsyncPostgresController`, `SyncPostgresController`

### Интеграция с FastAPI

- `AsyncSQLAlchemyMiddleware`
- `SyncSQLAlchemyMiddleware`
- `register_integrity_handler()`

### Query model

- поддержка `FilterRequest`
- `QueryOperator`
- nested fields вида `post.user.email`

## Установка

```bash
uv add axiom-sqlalchemy
uv add axiom-sqlalchemy[sqlite]
uv add axiom-sqlalchemy[postgres]
uv add axiom-sqlalchemy[fastapi]
```

## Минимальный Пример

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import Mapped, mapped_column

from axiom.oltp.sqlalchemy import Base, TimestampMixin
from axiom.oltp.sqlalchemy.sqlite import AsyncSQLiteController, AsyncSQLiteRepository


class UserModel(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


engine = create_async_engine("sqlite+aiosqlite:///:memory:")
Session = async_sessionmaker(engine, expire_on_commit=False)

async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

async with Session() as session:
    repo = AsyncSQLiteRepository(UserModel, session)
    controller = AsyncSQLiteController(UserModel, repo, exclude_fields=["email"])

    created = await controller.create({"name": "Alice", "email": "alice@example.com"})
    page = await controller.get_all()
```

Пример фильтрации:

```python
from axiom.core.filter import FilterParam, FilterRequest, QueryOperator

request = FilterRequest(
    chain=FilterParam(field="name", value="Alice", operator=QueryOperator.EQUALS),
)
result = await controller.get_by_filters(filter_request=request)
```

## Public API

Импорты верхнего уровня:

```python
from axiom.oltp.sqlalchemy import (
    AsyncBaseController,
    AsyncBaseRepository,
    AsyncSQLAlchemyController,
    AsyncSQLAlchemyRepository,
    AsDictMixin,
    Base,
    CountResponse,
    PaginationResponse,
    SyncBaseController,
    SyncBaseRepository,
    SyncSQLAlchemyController,
    SyncSQLAlchemyRepository,
    TimestampMixin,
    to_snake,
)
```

Concrete backends импортируются отдельно:

```python
from axiom.oltp.sqlalchemy.sqlite import AsyncSQLiteController, AsyncSQLiteRepository
from axiom.oltp.sqlalchemy.postgres import AsyncPostgresController, AsyncPostgresRepository
```

## Интеграция С Другими Пакетами

- использует `axiom-core.filter` и `axiom-core.schema`;
- с `axiom-fastapi` можно комбинировать middleware и integrity handler;
- потребитель сам создает engine, sessionmaker и lifecycle вокруг них.

## Ограничения И Текущий Статус

- Базовые `AsyncSQLAlchemyRepository` и `SyncSQLAlchemyRepository` не дают полноценный dialect-specific upsert. Для `create_or_update*` в реальном проекте лучше использовать `sqlite` или `postgres` репозитории.
- Пакет богатый по API, но требует явной инфраструктурной сборки со стороны приложения: engine/session creation здесь не инкапсулированы.
- В typing-слое есть заметное количество suppressions из-за ORM/generics взаимодействия; API рабочий, но типовая строгость не везде одинакова.

## Связанный Код

- `src/axiom/oltp/sqlalchemy/base/`
- `src/axiom/oltp/sqlalchemy/sqlite/`
- `src/axiom/oltp/sqlalchemy/postgres/`
- `src/axiom/oltp/sqlalchemy/middleware/`
- `tests/test_async_repository.py`
- `tests/test_async_controller.py`
- `tests/test_nested_fields.py`
- `tests/test_middleware.py`
