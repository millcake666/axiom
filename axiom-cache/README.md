# axiom-cache

`axiom-cache` — пакет с backend-agnostic cache abstractions, готовыми backends и decorator layer.

## Когда Использовать

Пакет подходит, если вам нужен:

- единый sync/async cache API;
- in-memory backend для тестов и локальной разработки;
- Redis backend для production;
- `@cached` и `@invalidate`;
- единая точка конфигурации через `CacheManager`.

## Что Уже Реализовано

| Группа | Сущности |
|---|---|
| ABC | `AsyncCacheBackend`, `SyncCacheBackend` |
| Backends | `AsyncInMemoryCache`, `SyncInMemoryCache`, `AsyncRedisCache`, `SyncRedisCache` |
| Decorators | `cached`, `invalidate` |
| Helpers | `CacheManager`, `TTL`, `FunctionKeyMaker`, `CacheInvalidateParams`, `ConvertParam` |
| Serialization | `SerializationStrategy`, `get_serializer`, `orjson`, `msgpack`, `dill`, `pydantic` strategies |

## Установка

```bash
uv add axiom-cache
```

Дополнительные serializer extras:

```bash
uv add axiom-cache[orjson]
uv add axiom-cache[msgpack]
uv add axiom-cache[dill]
uv add axiom-cache[pydantic]
```

## Минимальный Пример

```python
from axiom.cache import CacheManager
from axiom.cache.inmemory import AsyncInMemoryCache
from axiom.cache.schemas import CacheInvalidateParams

cache = AsyncInMemoryCache()
manager = CacheManager(cache, default_ttl=60)


@manager.cached()
async def get_user(user_id: int) -> dict[str, int]:
    return {"user_id": user_id}


@manager.invalidate(CacheInvalidateParams(functions=[get_user]))
async def update_user(user_id: int) -> None:
    pass
```

Прямое использование backend-а тоже поддерживается:

```python
from axiom.cache.inmemory import SyncInMemoryCache

cache = SyncInMemoryCache()
cache.set("health", {"ok": True}, ttl=30)
value = cache.get("health")
```

## Конфигурация

### Redis backend

Для Redis backend нужен `axiom-redis`:

```python
from axiom.cache.redis import AsyncRedisCache
from axiom.redis import RedisSettings, create_async_redis_client

settings = RedisSettings(REDIS_URL="redis://localhost:6379")
client = create_async_redis_client(settings)
cache = AsyncRedisCache(client)
```

### TTL helper

```python
from axiom.cache import TTL

ttl_seconds = TTL.time(minutes=5)
```

## Интеграция С Другими Пакетами

- `axiom-redis` используется как transport/client layer для Redis backend-а;
- `axiom-fastapi` можно использовать поверх этого пакета без каких-либо специальных адаптеров;
- `axiom-core` здесь нужен как общая основа workspace, но cache API от него почти не зависит семантически.

## Ограничения И Текущий Статус

- `FunctionKeyMaker` строит ключи из module/qualname/args и подходит для большинства сценариев, но для сложных доменных ключей лучше внедрять свой `KeyMaker`.
- `dill` serializer опасен для недоверенных данных и не должен использоваться там, где Redis/shared cache может быть загрязнен извне.
- In-memory backends подходят для одного процесса; это не distributed cache.

## Связанный Код

- `src/axiom/cache/decorators/`
- `src/axiom/cache/inmemory/`
- `src/axiom/cache/redis/`
- `src/axiom/cache/serialization/`
- `tests/test_cached_decorator.py`
- `tests/test_invalidate_decorator.py`
- `tests/test_redis_backend.py`
