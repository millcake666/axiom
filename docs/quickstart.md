# Быстрый Старт

## Когда Этот Документ Полезен

Используйте этот quickstart, если нужно быстро понять рабочий минимум по текущему репозиторию без чтения всего monorepo.

## 1. Установка

Для внешнего проекта обычно достаточно поставить только нужные пакеты.

Примеры:

```bash
uv add axiom-core
uv add axiom-fastapi
uv add axiom-sqlalchemy[sqlite]
uv add axiom-cache
uv add axiom-email[jinja2,aiosmtplib]
```

Внутри самой монорепы:

```bash
uv sync
```

## 2. Базовый `axiom-core`

```python
from axiom.core.logger import LoggerSettings, configure_logger, get_logger
from axiom.core.settings import AppMixin, BaseAppSettings, DebugMixin


class Settings(BaseAppSettings, AppMixin, DebugMixin):
    pass


settings = Settings()
configure_logger(LoggerSettings(LOG_FORMAT="auto", APP_STAGE=settings.APP_STAGE))

log = get_logger("example")
log.info("service starting")
```

Что это дает:

- чтение настроек из `.env`;
- единый logger;
- базу для остальных пакетов.

## 3. Минимальный HTTP-сервис

```python
from axiom.fastapi.app import AppConfig, create_app
from axiom.fastapi.middleware.logging import RequestLoggingMiddleware

app = create_app(
    AppConfig(
        title="Users API",
        version="0.1.0",
        description="Пример сервиса на Axiom",
    ),
)
app.add_middleware(RequestLoggingMiddleware)
```

Это уже дает:

- FastAPI app factory;
- стандартные handlers для `BaseError`, validation и unhandled exceptions;
- middleware для request logging.

## 4. Кэширование

### In-memory backend

```python
from axiom.cache import CacheManager
from axiom.cache.inmemory import AsyncInMemoryCache

cache = AsyncInMemoryCache()
manager = CacheManager(cache, default_ttl=60)


@manager.cached()
async def get_user(user_id: int) -> dict[str, int]:
    return {"user_id": user_id}
```

### Redis backend

```python
from axiom.cache.redis import AsyncRedisCache
from axiom.redis import RedisSettings, create_async_redis_client

settings = RedisSettings(REDIS_URL="redis://localhost:6379")
redis_client = create_async_redis_client(settings)
cache = AsyncRedisCache(redis_client)
```

## 5. SQLAlchemy + SQLite

Это минимальный рабочий сценарий на текущем API.

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

Важно:

- engine и session factory вы создаете сами, пакет их не прячет;
- если нужен рабочий upsert, используйте `AsyncSQLiteRepository` или `AsyncPostgresRepository`, а не базовый `AsyncSQLAlchemyRepository`.

## 6. MongoDB + Beanie

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
created = await controller.create({"name": "Alice", "email": "alice@example.com", "age": 30})
```

## 7. Email В Тестах

```python
from axiom.email import AsyncMailClient
from axiom.email.testing import AsyncInMemoryMailBackend

backend = AsyncInMemoryMailBackend()
client = AsyncMailClient(backend)
result = await client.send(
    to=["user@example.com"],
    subject="Hello",
    html="<b>Hello</b>",
)
```

## Что Дальше Читать

- [`docs/architecture.md`](./architecture.md) — если нужен архитектурный контекст
- [`docs/plugins.md`](./plugins.md) — если нужно быстро выбрать пакет
- README конкретного пакета — если нужен точный API по модулю
