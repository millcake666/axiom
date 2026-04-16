# axiom-clickhouse

Production-grade ClickHouse repository layer для аналитических OLAP-задач.
Предоставляет типизированный API поверх `clickhouse-connect` (sync + async) с поддержкой
read/query, analytical aggregations, insert/write, versioned/append сценариев, schema/admin
операций и mutation observability.

---

## Installation

```bash
uv add axiom-clickhouse
# или
pip install axiom-clickhouse
```

Опциональные зависимости для DataFrame-вставки:

```bash
uv add axiom-clickhouse pandas      # pandas DataFrame support
uv add axiom-clickhouse polars      # polars DataFrame support
```

---

## Quick Start

```python
from axiom.olap.clickhouse import ClickHouseRepository, ClickHouseSettings

settings = ClickHouseSettings()  # читает из env vars

repo = ClickHouseRepository.from_settings(settings, table="events", database="analytics")

# Smoke-test
result = repo.raw("SELECT 1")
print(result.rows)  # [{"1": 1}]
```

Async-вариант:

```python
from axiom.olap.clickhouse import AsyncClickHouseRepository

repo = AsyncClickHouseRepository.from_settings(settings, table="events", database="analytics")

result = await repo.raw("SELECT 1")
```

---

## Configuration

`ClickHouseSettings` наследует `BaseAppSettings` (pydantic-settings, читает из env / `.env`):

| Переменная окружения              | По умолчанию  | Описание                        |
|-----------------------------------|---------------|---------------------------------|
| `CLICKHOUSE_HOST`                 | `localhost`   | Хост ClickHouse                 |
| `CLICKHOUSE_PORT`                 | `8123`        | HTTP-порт                       |
| `CLICKHOUSE_USER`                 | `default`     | Пользователь                    |
| `CLICKHOUSE_PASSWORD`             | `""`          | Пароль                          |
| `CLICKHOUSE_DATABASE`             | `default`     | База данных                     |
| `CLICKHOUSE_SECURE`               | `False`       | TLS/HTTPS                       |
| `CLICKHOUSE_CONNECT_TIMEOUT`      | `10`          | Таймаут подключения (сек)       |
| `CLICKHOUSE_SEND_RECEIVE_TIMEOUT` | `300`         | Таймаут запроса (сек)           |

```python
from axiom.olap.clickhouse import ClickHouseSettings

settings = ClickHouseSettings(
    CLICKHOUSE_HOST="ch.internal",
    CLICKHOUSE_DATABASE="analytics",
)
```

---

## Client Creation

```python
from axiom.olap.clickhouse import ClickHouseClientFactory, ClickHouseSettings

settings = ClickHouseSettings()
factory = ClickHouseClientFactory()

# Sync-клиент
sync_client = factory.create_sync_client(settings)

# Async-клиент
async_client = await factory.create_async_client(settings)

# Передача готового клиента репозиторию
from axiom.olap.clickhouse import ClickHouseRepository

repo = ClickHouseRepository.from_client(sync_client, table="events", database="analytics")
```

---

## Repository Types Overview

| Класс                              | Назначение                                               |
|------------------------------------|----------------------------------------------------------|
| `ClickHouseRepository`             | Facade: read + write + agg + raw escape hatch (sync)     |
| `AsyncClickHouseRepository`        | То же, async                                             |
| `TypedClickHouseRepository[T]`     | Typed facade с `row_factory` (sync)                      |
| `AsyncTypedClickHouseRepository[T]`| То же, async                                             |
| `ClickHouseReadRepository`         | Только read-операции (sync)                              |
| `AsyncClickHouseReadRepository`    | То же, async                                             |
| `TypedClickHouseReadRepository[T]` | Typed read с `row_factory` (sync)                        |
| `ClickHouseWriteRepository`        | Insert/write-операции (sync)                             |
| `AsyncClickHouseWriteRepository`   | То же, async                                             |
| `ClickHouseAggRepository`          | Analytical aggregations — GROUP BY, top-N, time_series   |
| `AsyncClickHouseAggRepository`     | То же, async                                             |
| `VersionedClickHouseRepository`    | Append/versioned сценарии, ReplacingMergeTree (sync)     |
| `AsyncVersionedClickHouseRepository`| То же, async                                            |
| `ClickHouseSchemaManager`          | DDL-операции: create/drop/truncate/describe (sync)       |
| `AsyncClickHouseSchemaManager`     | То же, async                                             |
| `ClickHouseMutationManager`        | Observability мутаций: list/wait/kill (sync)             |
| `AsyncClickHouseMutationManager`   | То же, async                                             |

---

## Usage Examples

### Sync Read

```python
from axiom.olap.clickhouse import ClickHouseRepository, ClickHouseSettings, CHQuerySpec, PageSpec

settings = ClickHouseSettings()
repo = ClickHouseRepository.from_settings(settings, table="events")

# Все строки
result = repo.fetch_all()
print(result.rows)        # list[dict]
print(result.row_count)   # int

# С фильтрацией и пагинацией
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator

filter_req = FilterRequest(
    chain=FilterParam(field="event_type", value="click", operator=QueryOperator.EQUALS)
)
spec = CHQuerySpec(filters=filter_req, page=PageSpec(offset=0, limit=100))
result = repo.fetch_all(spec)
```

### Async Read

```python
from axiom.olap.clickhouse import AsyncClickHouseRepository

repo = AsyncClickHouseRepository.from_settings(settings, table="events")

result = await repo.fetch_all()
row = await repo.fetch_one(filter_req)
count = await repo.count(filter_req)
exists = await repo.exists(filter_req)
```

### fetch_paged

```python
from axiom.olap.clickhouse import CHQuerySpec, PageSpec

spec = CHQuerySpec(page=PageSpec(offset=0, limit=50))
paged = repo.fetch_paged(spec)

print(paged.rows)      # list[dict] — текущая страница
print(paged.total)     # int — всего строк в таблице (без LIMIT)
print(paged.has_next)  # bool — есть ли следующая страница
print(paged.offset)    # 0
print(paged.limit)     # 50
```

### stream — итерация по большим выборкам

```python
# Sync streaming по чанкам
for chunk in repo.stream("SELECT * FROM events WHERE date > '2024-01-01'", chunk_size=5000):
    for row in chunk:
        process(row)  # list[dict] на чанк

# Async streaming
async for chunk in repo.stream("SELECT * FROM events", chunk_size=1000):
    await process_chunk(chunk)
```

### insert_many

```python
rows = [
    {"event_type": "click", "user_id": 1, "ts": "2024-01-01 00:00:00"},
    {"event_type": "view",  "user_id": 2, "ts": "2024-01-01 00:01:00"},
]
result = repo.insert_many(rows)
print(result.inserted)  # 2
print(result.success)   # True
```

### insert_chunked с partial failure handling

```python
rows = [{"id": i, "value": i * 10} for i in range(100_000)]

result = repo.insert_chunked(rows, chunk_size=10_000)
# При сбое одного чанка успешные НЕ откатываются
if not result.success:
    print(f"Failed: {result.failed} chunks")
    print(result.errors)  # list[str] — сообщения ошибок
print(f"Inserted: {result.inserted} rows")
```

### aggregate с AggregateSpec

```python
from axiom.olap.clickhouse import (
    AggregateSpec, GroupBySpec, MetricSpec, AggFunction, PageSpec
)

spec = AggregateSpec(
    metrics=[
        MetricSpec(function=AggFunction.COUNT, field="id", alias="total"),
        MetricSpec(function=AggFunction.SUM, field="revenue", alias="total_revenue"),
    ],
    group_by=GroupBySpec(fields=["event_type", "country"]),
    page=PageSpec(limit=20),
)

result = repo.aggregate(spec)
for row in result.rows:
    print(row)  # {"event_type": "click", "country": "RU", "total": 100, "total_revenue": 5000}
```

### top_n

```python
from axiom.olap.clickhouse import MetricSpec, AggFunction

top = repo.top_n(
    field="page_url",
    n=10,
    metric=MetricSpec(function=AggFunction.COUNT, field="id", alias="visits"),
)
# Топ-10 страниц по количеству посещений
```

### time_series

```python
result = repo.time_series(
    time_field="ts",
    interval="1h",          # "1h", "1d", "1w", "30m" и т.д.
    metrics=[
        MetricSpec(function=AggFunction.COUNT, field="id", alias="events"),
        MetricSpec(function=AggFunction.UNIQ, field="user_id", alias="unique_users"),
    ],
)
```

### update_by_filter + caveat о мутациях

```python
from axiom.core.filter.expr import FilterParam, FilterRequest
from axiom.core.filter.type import QueryOperator

filter_req = FilterRequest(
    chain=FilterParam(field="status", value="pending", operator=QueryOperator.EQUALS)
)

# ВНИМАНИЕ: это асинхронная мутация ClickHouse (ALTER TABLE UPDATE).
# Операция НЕ является дешёвым row-level update.
# Для отслеживания статуса используй MutationManager.
count = repo.update_by_filter(filter_req, values={"status": "processed"})
```

### Versioned/Append сценарий с VersionedClickHouseRepository

```python
from axiom.olap.clickhouse import VersionedClickHouseRepository

repo = VersionedClickHouseRepository.from_settings(
    settings,
    table="products",
    database="catalog",
    version_column="version",
    is_deleted_column="is_deleted",
)

# Append новой версии записи
result = repo.append_version(
    row={"product_id": 42, "price": 999.0, "status": "active"},
    version=1,
)

# Получить последнюю версию по ID
latest = repo.get_latest(
    filters=FilterRequest(
        chain=FilterParam(field="product_id", value=42, operator=QueryOperator.EQUALS)
    ),
    id_column="product_id",
)

# Получить с FINAL (сильная консистентность, медленно)
# Используй только для критичных к консистентности путей
result = repo.get_latest_with_final(filter_req)

# Soft delete — вставляет новую версию с is_deleted=1
repo.soft_delete(id_column="product_id", id_value=42, version=2)

# Читать только активные записи
active = repo.read_active(filters=None, page=PageSpec(limit=100))
```

### raw escape hatch

```python
# Raw SELECT с полным контролем
result = repo.raw("SELECT toDate(ts) as day, count() FROM events GROUP BY day LIMIT 30")
for row in result.rows:
    print(row["day"], row["count()"])

# Raw DDL/DML без результата
written = repo.raw_command("ALTER TABLE events DELETE WHERE ts < '2020-01-01'")
```

### SchemaManager.describe_table

```python
from axiom.olap.clickhouse import ClickHouseSchemaManager

schema = ClickHouseSchemaManager.from_settings(settings, database="analytics")

# Проверить существование таблицы
if not schema.table_exists("events", database="analytics"):
    schema.create_table("""
        CREATE TABLE analytics.events (
            id       UInt64,
            ts       DateTime,
            event_type String,
            user_id  UInt64
        ) ENGINE = MergeTree()
        ORDER BY (ts, id)
    """)

# Introspection
info = schema.describe_table("events", database="analytics")
print(info.engine)          # "MergeTree"
for col in info.columns:
    print(col.name, col.type)

# Список таблиц
tables = schema.list_tables(database="analytics")

# Optimize (тяжёлая операция — не вызывать на hot path)
schema.optimize_table("events", database="analytics", final=True, deduplicate=True)
```

### MutationManager.wait_for_mutation

```python
from axiom.olap.clickhouse import ClickHouseMutationManager

mutations = ClickHouseMutationManager.from_settings(settings)

# Список активных мутаций
active = mutations.list_mutations(table="events", database="analytics", active_only=True)

# Дождаться завершения мутации
status = mutations.wait_for_mutation(
    mutation_id="0000000001",
    poll_interval=2.0,
    timeout=120.0,
)
print(status.is_done)   # True
print(status.error)     # None если успешно

# Список застрявших мутаций (>30 мин)
stuck = mutations.list_stuck_mutations("events", database="analytics", threshold_minutes=30)

# Убить мутацию (использовать осторожно!)
mutations.kill_mutation("0000000001")
```

### Typed Repository с row_factory

```python
from dataclasses import dataclass
from axiom.olap.clickhouse import TypedClickHouseRepository

@dataclass
class Event:
    id: int
    event_type: str
    user_id: int

def event_factory(row: dict) -> Event:
    return Event(
        id=row["id"],
        event_type=row["event_type"],
        user_id=row["user_id"],
    )

repo = TypedClickHouseRepository.from_client(
    client=sync_client,
    table="events",
    database="analytics",
    row_factory=event_factory,
)

result = repo.fetch_all()
events: list[Event] = result.rows  # Typed!
```

---

## ClickHouse vs OLTP — Trade-offs

### Почему `update_by_filter` / `delete_by_filter` дорогие

ClickHouse — это аналитическая СУБД, оптимизированная для массового чтения и append-вставок.
`update_by_filter` и `delete_by_filter` создают **асинхронные мутации** (`ALTER TABLE UPDATE / DELETE`).

- Мутация переписывает целые **части** (parts) таблицы на диск, а не отдельные строки.
- Мутация выполняется **в фоне** — данные не изменятся мгновенно.
- Пока мутация не завершена, нет гарантий консистентности для запросов.
- Частые мутации деградируют производительность и пространство на диске.

**Когда допустимо:** редкие batch-корректировки (< 1 раз в час на таблицу).
**Когда недопустимо:** row-level updates в real-time, OLTP-паттерны с частыми изменениями.

### Когда использовать `VersionedClickHouseRepository`

Если данные по природе append-only (история событий, аудит, версионирование сущностей):

- Вместо UPDATE — вставляй новую версию с инкрементным `version` или свежим `updated_at`.
- `ReplacingMergeTree` в фоне дедуплицирует версии, оставляя только последнюю.
- `get_latest` через `argMax` или `FINAL` — для чтения актуального состояния.
- Soft delete — специальная версия с флагом `is_deleted=1`.

Это **быстро** (append = O(1)), консистентно со временем, и не создаёт мутаций.

### Когда использовать raw SQL

Используй `repo.raw(...)` / `repo.execute_analytical(...)` когда:

- Нужны ClickHouse-специфичные функции (`arrayJoin`, `dictGet`, `quantileTDigest`, window functions).
- Запрос сложнее чем то, что покрывает `AggregateSpec`.
- Нужен оконный анализ или сложные подзапросы.
- Тестируешь новый запрос перед добавлением метода в репозиторий.

**Правило:** не злоупотребляй `raw` — он обходит типизацию и валидацию параметров.
Выносить `raw`-запросы в именованные методы репозитория — хорошая практика.

---

## Exception Hierarchy

```
ClickHouseError (BaseError, status_code=500)
├── ClickHouseConnectionError   (status_code=503) — сбой подключения
├── ClickHouseQueryError        (status_code=500) — ошибка выполнения запроса / timeout
├── ClickHouseRowMappingError   (status_code=500) — сбой row_factory
├── ClickHouseBulkInsertError   (status_code=500) — частичный сбой bulk insert
├── ClickHouseMutationError     (status_code=500) — мутация завершилась с ошибкой
├── ClickHouseSchemaError       (status_code=500) — ошибка DDL-операции
├── ClickHouseConfigError       (status_code=500) — неверная конфигурация репозитория
└── ClickHouseImportError       (status_code=500) — отсутствует опциональная зависимость
```

Все исключения `clickhouse-connect` оборачиваются в эту иерархию на boundary — наружу
никогда не проходят raw исключения библиотеки.

---

## Related Code

- `src/axiom/olap/clickhouse/` — исходный код пакета
- `tests/unit/` — unit-тесты (без Docker)
- `tests/integration/` — integration-тесты через `testcontainers` (требуется Docker)
