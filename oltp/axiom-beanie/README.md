# axiom-beanie

`axiom-beanie` — MongoDB-адаптер Axiom с async веткой на Beanie и sync веткой на PyMongo.

## Когда Использовать

Пакет подходит, если вам нужен:

- repository/controller слой для MongoDB;
- async работа через Beanie;
- sync доступ через PyMongo + Pydantic models;
- тот же style of usage, что и у `axiom-sqlalchemy`;
- filter DSL и pagination responses из `axiom-core`.

## Что Уже Реализовано

### Async ветка

- `AsyncBeanieRepository`
- `AsyncBeanieController`

### Sync ветка

- `SyncMongoRepository`
- `SyncMongoController`
- `SyncDocument`

### Общие элементы

- `AsyncBaseRepository`, `SyncBaseRepository`
- `AsyncBaseController`, `SyncBaseController`
- `TimestampMixin`
- nested field utilities для Link-based paths

## Установка

```bash
uv add axiom-beanie
```

## Минимальный Пример

```python
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from axiom.oltp.beanie import AsyncBeanieController, AsyncBeanieRepository


class UserDocument(Document):
    name: str
    email: str
    age: int


client = AsyncIOMotorClient("mongodb://localhost:27017")
database = client.axiom_demo
await init_beanie(database=database, document_models=[UserDocument])

repo = AsyncBeanieRepository(UserDocument, db_session=None)
controller = AsyncBeanieController(UserDocument, repo, exclude_fields=["email"])

created = await controller.create(
    {"name": "Alice", "email": "alice@example.com", "age": 30},
)
```

Пример sync-модели:

```python
from axiom.oltp.beanie.base.document import SyncDocument


class UserModel(SyncDocument):
    name: str
    email: str
    age: int
```

## Public API

```python
from axiom.oltp.beanie import (
    AsyncBaseController,
    AsyncBaseRepository,
    AsyncBeanieController,
    AsyncBeanieRepository,
    CountResponse,
    PaginationResponse,
    SyncBaseController,
    SyncBaseRepository,
    SyncDocument,
    SyncMongoController,
    SyncMongoRepository,
    TimestampMixin,
)
```

## Интеграция С Другими Пакетами

- использует `axiom-core.filter` и `axiom-core.schema`;
- по стилю работы близок к `axiom-sqlalchemy`, поэтому удобно держать одинаковые service boundaries;
- не требует `axiom-fastapi`, но легко используется внутри FastAPI handlers.

## Ограничения И Текущий Статус

- Async-ветка действительно основана на Beanie; sync-ветка — это уже не Beanie, а свой слой поверх PyMongo и `SyncDocument`.
- `AsyncBeanieController` и `SyncMongoController` не добавляют полноценный transaction lifecycle сами по себе: `processing_transaction()` сейчас фактически pass-through.
- Nested field support есть и покрыт тестами, но для сложных MongoDB-specific сценариев все равно иногда придется опускаться ниже repository abstractions.

## Связанный Код

- `src/axiom/oltp/beanie/base/repository/`
- `src/axiom/oltp/beanie/base/controller/`
- `src/axiom/oltp/beanie/base/utils.py`
- `tests/test_repository.py`
- `tests/test_controller.py`
- `tests/test_sync_repository.py`
- `tests/test_nested_fields.py`
