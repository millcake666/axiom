# axiom-objectstore

`axiom-objectstore` — пакет для работы с object/file storage через единый abstract API.

## Когда Использовать

Подходит, если вам нужен:

- общий интерфейс для local disk и S3-compatible storage;
- sync и async варианты;
- простая работа с bytes payload;
- presigned URLs для S3 backend-а.

## Что Уже Реализовано

| Группа | Сущности |
|---|---|
| ABC | `AbstractAsyncObjectStore`, `AbstractSyncObjectStore` |
| Local backend | `AsyncLocalDiskObjectStore`, `SyncLocalDiskObjectStore`, `LocalDiskConfig` |
| S3 backend | `AsyncS3ObjectStore`, `SyncS3ObjectStore`, `S3Config`, `S3Settings` |
| Exceptions | `ObjectStoreError`, `ObjectNotFoundError`, `ObjectStoreInternalError` |

Базовый контракт object store:

- `upload`
- `get`
- `delete`
- `exists`
- `get_url`

S3 backends дополнительно дают:

- `get_presigned_url`

## Установка

```bash
uv add axiom-objectstore
```

## Минимальный Пример

### Local disk

```python
from pathlib import Path

from axiom.objectstore.local import AsyncLocalDiskObjectStore, LocalDiskConfig

store = AsyncLocalDiskObjectStore(
    LocalDiskConfig(base_dir=Path("/tmp/axiom-store")),
)

key = await store.upload(b"hello", name="greeting.txt")
data = await store.get(key)
url = await store.get_url(key)
```

### S3-compatible backend

```python
from axiom.objectstore.s3 import AsyncS3ObjectStore, S3Config

store = AsyncS3ObjectStore(
    S3Config(
        aws_access_key_id="key",
        aws_secret_access_key="secret",
        endpoint_url="https://s3.example.com",
        region_name="us-east-1",
        bucket_name="uploads",
        key_prefix="public/",
    ),
)
```

## Конфигурация

### Local

`LocalDiskConfig`:

- `base_dir`
- `base_url`

### S3

`S3Config`:

- `aws_access_key_id`
- `aws_secret_access_key`
- `endpoint_url`
- `region_name`
- `service_name`
- `bucket_name`
- `key_prefix`
- `is_public`

`S3Settings` нужен как mixin/bridge для env-backed конфигурации.

## Интеграция С Другими Пакетами

- `axiom-core` используется для exception hierarchy;
- пакет можно использовать независимо от `axiom-fastapi` и ORM-адаптеров;
- удобно подходит как storage layer для email attachments, uploads и экспортов.

## Ограничения И Текущий Статус

- Local backend игнорирует `content_type` и `content_disposition` и хранит только bytes.
- S3 backends создают новый client/session на каждую операцию; это упрощает lifecycle, но создает дополнительный overhead.
- `get_presigned_url` есть только на S3 concrete classes, не на abstract interface.

## Связанный Код

- `src/axiom/objectstore/abs/`
- `src/axiom/objectstore/local/`
- `src/axiom/objectstore/s3/`
- `tests/test_local_async.py`
- `tests/test_local_sync.py`
- `tests/test_s3_async.py`
- `tests/test_s3_sync.py`
