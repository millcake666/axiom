# axiom-redis

`axiom-redis` — низкоуровневый sync/async Redis client wrapper для Axiom.

## Когда Использовать

Берите пакет, если вам нужен:

- прямой доступ к Redis без decorator layer;
- единый thin wrapper над `redis` / `redis.asyncio`;
- Pydantic settings для Redis-конфига;
- базовый API, который уже использует `axiom-cache`.

## Что Уже Реализовано

- `AsyncRedisClient`
- `SyncRedisClient`
- `RedisSettings`
- `create_async_redis_client()`
- `create_sync_redis_client()`
- собственные exception classes для operation/config errors

Поддерживаемые операции:

- `get`
- `set`
- `delete`
- `exists`
- `expire`
- `ttl`
- `scan_iter`
- `flushall`
- `close`

## Установка

```bash
uv add axiom-redis
```

## Минимальный Пример

```python
from axiom.redis import RedisSettings, create_async_redis_client

settings = RedisSettings(REDIS_URL="redis://localhost:6379")
client = create_async_redis_client(settings)

await client.set("greeting", b"hello", ttl=60)
value = await client.get("greeting")
```

Sync-вариант:

```python
from axiom.redis import RedisSettings, create_sync_redis_client

settings = RedisSettings(REDIS_URL="redis://localhost:6379")
client = create_sync_redis_client(settings)
client.set("counter", b"1")
```

## Конфигурация

`RedisSettings` поддерживает:

- `REDIS_URL`
- `REDIS_USE_CLUSTER`
- `REDIS_MAX_CONNECTIONS`
- `REDIS_SOCKET_TIMEOUT`
- `REDIS_DECODE_RESPONSES`

## Интеграция С Другими Пакетами

- `axiom-cache` использует этот пакет как transport layer для Redis cache backend-а;
- прикладной код может использовать `raw` property, если нужен доступ к underlying client.

## Ограничения И Текущий Статус

- Пакет сознательно thin: он не скрывает Redis целиком и не заменяет возможности официального клиента.
- Higher-level patterns вроде cache invalidation, serialization и key strategy находятся не здесь, а в `axiom-cache`.

## Связанный Код

- `src/axiom/redis/async_client.py`
- `src/axiom/redis/sync_client.py`
- `src/axiom/redis/settings.py`
- `tests/test_async_client.py`
- `tests/test_sync_client.py`
- `tests/test_settings_and_factory.py`
