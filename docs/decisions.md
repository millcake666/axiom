# Архитектурные Решения Axiom

Этот файл фиксирует ключевые инженерные решения проекта: почему код устроен именно так, а не иначе.
Здесь нет wishlist-а и нет пересказа архитектуры — только те решения, которые уже приняты и влияют
на то, как добавляется новый код.

Формат каждой записи:

- **Status** — `accepted` (зафиксировано) / `deprecated` (устарело) / `under review` (обсуждается)
- **Confidence** — уровень уверенности, если решение неочевидно из кода
- **Context** — почему возник вопрос
- **Decision** — что было решено
- **Consequences** — что это влечёт
- **What not to do** — типичная ошибка в этом месте

---

## D-001 — Плагинность через отдельные installable packages, не runtime registry

**Status:** accepted

**Context:** Axiom задумывался как "набор совместимых библиотек", а не как фреймворк с централизованной
точкой расширения. Нужно было выбрать механизм плагинности.

**Decision:** Каждый плагин — это отдельный pip-пакет, устанавливаемый независимо. Нет
`register_plugin()`, нет `app.include(plugin)`, нет runtime discovery через entry points.
Плагинность достигается через общий namespace `axiom.*`, общие абстракции из ядра и явные импорты
в приложении потребителя.

**Consequences:**
- Consumer устанавливает только нужные пакеты — `uv add axiom-fastapi axiom-sqlalchemy`.
- Нет скрытой магии: какой backend используется — явно видно в DI и импортах.
- Нельзя "подключить плагин" во время работы процесса — это не является целью.

**What not to do:** не добавлять глобальный registry, plugin-manager или auto-discovery через
`importlib.metadata.entry_points`.

---

## D-002 — axiom-core не зависит ни от одного фреймворка

**Status:** accepted

**Context:** Ядро должно быть переиспользуемым независимо от выбранного стека. Если в core попадает
`fastapi` или `sqlalchemy`, потребитель тащит весь стек ради настроек.

**Decision:** В `axiom-core` нет импортов из `fastapi`, `starlette`, `sqlalchemy`, `redis`,
`beanie` или любой другой инфраструктурной библиотеки. Зависимости ядра: `loguru`, `pydantic`,
`pydantic-settings`, stdlib.

**Consequences:**
- `axiom-core` можно использовать в CLI-инструментах, скриптах, воркерах — не только в HTTP-сервисах.
- Остальные пакеты зависят от `axiom-core`, но не наоборот.
- Изменения в ядре потенциально затрагивают весь workspace.

**What not to do:** не добавлять `from fastapi import ...` или `from sqlalchemy import ...` в
`axiom-core/src/axiom/core/`.

---

## D-003 — PEP 420 implicit namespace packages для axiom.*

**Status:** accepted

**Context:** Несколько независимых пакетов должны разделять общий Python namespace `axiom.*`
без конфликтов при импорте.

**Decision:** На уровне `src/axiom/` нет `__init__.py`. Каждый пакет объявляет только своё
поддерево: `src/axiom/core/__init__.py`, `src/axiom/fastapi/__init__.py` и т.д. Путь `src/axiom/oltp/`
тоже без `__init__.py` — namespace package второго уровня.

**Consequences:**
- Все пакеты указывают `packages = ["src/axiom"]` в hatchling build targets.
- `from axiom.core import ...` и `from axiom.fastapi import ...` работают одновременно в одном env.
- Нельзя делать wildcard `from axiom import *`.

**What not to do:** не создавать `axiom/__init__.py` ни в одном из пакетов — это сломает namespace
для всех остальных.

---

## D-004 — src-layout во всех пакетах

**Status:** accepted

**Context:** Без `src/`-layout тесты могут импортировать пакет прямо из рабочей директории,
минуя установку, что скрывает packaging-ошибки.

**Decision:** Все пакеты используют `src/axiom/<name>/` как корень исходников.
Тесты лежат в `tests/` рядом с пакетом, а не в `src/`.

**Consequences:**
- Для запуска тестов пакет должен быть установлен (или workspace synced).
- `pyproject.toml` всегда содержит `[tool.hatch.build.targets.wheel] packages = ["src/axiom"]`.

**What not to do:** не класть код в `axiom_cache/` или `axiom/cache/` в корне пакета.

---

## D-005 — Трёхуровневая иерархия data access: abs/ → base/ → dialect/

**Status:** accepted

**Context:** SQLAlchemy-слой должен работать и для PostgreSQL, и для SQLite, но с разным поведением
в диалектно-специфичных операциях. При этом нужен общий контракт для тестирования и подмены.

**Decision:**

```
abs/      — ABC-контракт, не зависящий от конкретной СУБД
base/     — универсальная SQLAlchemy-реализация для любого диалекта
postgres/ — PostgreSQL-специфика (pg_insert, RoutingSession)
sqlite/   — SQLite-специфика (sqlite dialect insert)
```

Каждый уровень наследуется от предыдущего. Consumer инстанциирует только листовой класс:
`AsyncPostgresRepository`, `AsyncSQLiteRepository`.

**Consequences:**
- Изменение контракта в `abs/` требует обновления всех реализаций.
- В `base/` находится только то, что корректно работает на любом SQLAlchemy-диалекте.

**What not to do:** не добавлять в `abs/` или `base/` методы, которые требуют диалектного знания.
Если нельзя реализовать без dialect-специфики — метод не идёт в base, только в листовой класс.

---

## D-006 — Repository и Controller — разные ответственности

**Status:** accepted

**Context:** В ранних версиях transaction management смешивался с query building, что усложняло
тестирование и переиспользование.

**Decision:**

- **Repository** отвечает только за query building: построение запросов, фильтрацию,
  пагинацию, CRUD-операции. Не управляет транзакцией.
- **Controller** отвечает за transaction lifecycle: `commit`, `rollback`, `refresh`.
  Использует декоратор `@transactional`, делегирует в repository.
  Также формирует `PaginationResponse` и маппит ошибки.

**Consequences:**
- Repository можно тестировать с in-memory SQLite без mock-ов транзакций.
- Controller содержит `processing_transaction` — единственную точку управления сессией.

**What not to do:** не вызывать `session.commit()` напрямую в repository.
Не класть бизнес-логику в controller — только data-access оркестрация.

---

## D-007 — Диалектно-специфичные методы не выходят за пределы dialect/

**Status:** accepted

**Context:** `create_or_update_by` (upsert) имеет принципиально разную семантику для разных СУБД.
Наличие "заглушки" в `base/` с silent fallback или `NotImplementedError` создаёт ложный контракт.

**Decision:** `create_or_update_by` и другие dialect-specific методы объявляются и реализуются
только в `postgres/` и `sqlite/` — без соответствующего abstract-метода в `abs/` и без
fallback-заглушки в `base/`.

Правило: **если метод нельзя реализовать корректно без dialect-знания, он не существует в base.**

**Consequences:**
- `AsyncSQLAlchemyRepository` и `SyncSQLAlchemyRepository` не имеют `create_or_update_by`.
- Потребитель, которому нужен upsert, явно использует `AsyncPostgresRepository` или
  `AsyncSQLiteRepository` — выбор виден в коде.

**What not to do:** не добавлять в `abs/` или `base/` `NotImplementedError`-заглушки для
dialect-specific методов. Это создаёт ложное ощущение, что метод существует в контракте.

---

## D-008 — FilterRequest как единый DSL фильтрации

**Status:** accepted

**Context:** `axiom-sqlalchemy` и `axiom-beanie` работают с принципиально разными storage
backends, но должны предоставлять совместимый внешний API для фильтрации и пагинации.

**Decision:** `FilterParam`, `FilterGroup`, `FilterRequest` из `axiom-core` используются в обоих
адаптерах как единый язык описания фильтров. Поддерживаются:
- `&` / `|` для AND/OR цепочек
- 14 операторов (EQUALS, IN, CONTAINS, STARTS_WITH, и т.д.)
- dot-notation любой глубины (`user.profile.city`) для related fields

**Consequences:**
- Сервис, переходящий с SQLAlchemy на Beanie, сохраняет тот же filter-код.
- Реализация traversal dot-notation — ответственность каждого адаптера.

**What not to do:** не изобретать отдельный filter-язык в `axiom-sqlalchemy` или `axiom-beanie`.

---

## D-009 — Domain layer использует dataclasses, не Pydantic

**Status:** accepted

**Context:** Domain objects не должны зависеть от HTTP-валидации или ORM-маппинга.
Использование Pydantic для domain layer привязывает domain к HTTP-слою.

**Decision:** `BaseDomainDC` — это `@dataclass`, не `BaseModel`. Он не знает ни о FastAPI,
ни о SQLAlchemy. Поля: `id: UUID`, `created_at: datetime`, `updated_at: datetime`.
Методы: `to_dict()`, `from_dict()`, `__eq__` по `id`.

**Consequences:**
- Domain objects безопасно использовать в воркерах, CLI и других non-HTTP контекстах.
- Сериализация в HTTP-ответ требует явного маппинга через `BaseResponseSchema`.

**What not to do:** не наследовать domain-сущности от `BaseModel`. Не добавлять ORM-атрибуты
в `BaseDomainDC`.

---

## D-010 — Pydantic только для DTOs и HTTP boundary

**Status:** accepted

**Context:** Связано с D-009. Нужно разделить, где Pydantic уместен, а где нет.

**Decision:** Pydantic используется на HTTP boundary:
- `BaseRequestSchema` — валидация входящих данных
- `BaseResponseSchema` — сериализация ответов
- `AppConfig`, `BaseAppSettings` — конфигурация

Pydantic не используется для domain-сущностей и не проникает в repository/controller.

**Consequences:**
- `from_attributes=True` нужен только в `BaseResponseSchema` для ORM → Pydantic маппинга.
- Controller маппит ORM model → response schema в endpoint, не внутри себя.

---

## D-011 — Pydantic v2 ConfigDict везде, никогда не class Config

**Status:** accepted

**Context:** Pydantic v2 deprecировал `class Config` внутри модели в пользу `model_config`.

**Decision:** Все Pydantic-модели и settings используют `model_config = ConfigDict(...)` и
`model_config = SettingsConfigDict(...)` соответственно. `class Config` запрещён.

**Consequences:**
- Единый стиль конфигурации Pydantic-моделей во всём проекте.

**What not to do:**

```python
# Неправильно
class MySchema(BaseModel):
    class Config:
        from_attributes = True

# Правильно
class MySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
```

---

## D-012 — Settings через pydantic-settings и composable mixins

**Status:** accepted

**Context:** Сервисы имеют разные наборы настроек, но всегда нужен стандартный базовый набор.

**Decision:** `BaseAppSettings(BaseSettings)` — основа для всех конфигов сервиса.
Composable mixins для стандартных групп:
- `AppMixin` — `APP_HOST`, `APP_PORT`, `APP_STAGE`, `APP_NAME`
- `DebugMixin` — `DEBUG`

`env_prefix` задаётся в `model_config` наследника или через утилиту `make_env_prefix(APP_NAME)`.

**Consequences:**
- Сервис собирает конфиг из нужных миксинов без copy-paste.
- Все настройки читаются из env vars и `.env`-файла автоматически.

**What not to do:** не читать `os.environ` напрямую в коде. Не хардкодить конфигурацию.

---

## D-013 — ABC для внутренних расширений, Protocol для внешних

**Status:** accepted

**Context:** Axiom предоставляет точки расширения: cache backends, email backends, object store
backends, hooks. Нужно выбрать механизм контракта.

**Decision:**

- **ABC** (`abc.ABC` + `@abstractmethod`) — когда Axiom контролирует обе стороны: и абстракцию,
  и реализацию. Пример: `AsyncCacheBackend`, `AsyncBaseRepository`.
  Consumer обязан наследовать ABC, что даёт static analysis и runtime проверки.

- **Protocol** (`typing.Protocol` + `@runtime_checkable`) — когда consumer предоставляет
  реализацию и не должен зависеть от `axiom.*`. Пример: `AsyncMailBackend`, `TemplateRenderer`,
  `MailHook`. Consumer может использовать duck typing без наследования.

Правило: ABC если axiom контролирует обе стороны → Protocol если consumer реализует интерфейс.

**Consequences:**
- Consumer не обязан устанавливать axiom ради email backend — достаточно соответствовать Protocol.
- Внутренние реализации (InMemoryCache, RedisCache) наследуют ABC и проверяются статически.

---

## D-014 — Исключения в каждом пакете наследуются от BaseError

**Status:** accepted

**Context:** При использовании нескольких axiom-пакетов одновременно нужно понимать, какой пакет
бросил ошибку. plain `Exception` не даёт этой информации.

**Decision:** Каждый пакет имеет `exception/` sub-package как минимум с одной базовой ошибкой
для своего namespace. Она наследует от `axiom.core.exceptions.BaseError`.
Если плагину нужны детализированные ошибки — они наследуются от базовой ошибки плагина,
а не напрямую от `BaseError`. Если детализация не нужна — достаточно одной базовой.

```python
# Правильная структура (например, axiom-cache)
from axiom.core.exceptions import BaseError

class CacheError(BaseError):
    code = "cache_error"
    status_code = 500

# Детализация при необходимости:
class CacheBackendError(CacheError):
    code = "cache_backend_error"
```

**Consequences:**
- `except CacheError` ловит всё из `axiom-cache`.
- `except BaseError` ловит всё из всего axiom-стека.
- В коде видно, откуда пришла ошибка.

**What not to do:** не поднимать plain `Exception` или `ValueError` из кода пакета.
Не наследовать package-level ошибки напрямую от `Exception`.

> **Текущее состояние:** не все пакеты соблюдают это правило (`axiom-cache` использует
> plain `Exception`). Правило действует для нового кода; существующие нарушения
> исправляются итеративно.

---

## D-015 — Явный __all__ в каждом __init__.py

**Status:** accepted

**Context:** Без `__all__` любой внутренний символ становится частью публичного API пакета,
что создаёт неконтролируемые breaking changes.

**Decision:** Каждый публичный `__init__.py` содержит явный `__all__` с alphabetically-sorted
списком экспортируемых символов. Ничего лишнего не утекает наружу.

**Consequences:**
- IDE и type checkers видят только публичный API.
- Refactoring внутренностей не ломает потребителей (если символ не в `__all__`).

**What not to do:** не полагаться на "всё что не начинается с `_` — публично".

---

## D-016 — loguru — единственный канонический логгер

**Status:** accepted

**Context:** Исторически `axiom-fastapi` был написан на `structlog`. Это создаёт несогласованность
формата логов в приложении, использующем несколько axiom-пакетов.

**Decision:** Canonical логгер — `loguru` из `axiom.core.logger`. Все пакеты используют
`get_logger()` из `axiom.core.logger`. Настройка — через `configure_logger(LoggerSettings)`.

Использование `structlog` в `axiom-fastapi` — известная ошибка, подлежащая исправлению.

**Consequences:**
- Единый формат логов (text в dev, JSON в staging/prod) во всём приложении.

**What not to do:** не вводить `structlog`, `logging` (stdlib) или `print` в новый код пакетов.
Для логирования — только `axiom.core.logger.get_logger()`.

> **Текущее состояние:** `axiom-fastapi` и `axiom-sqlalchemy/exception_handler` используют
> `structlog`. Это будет исправлено, но не является образцом для нового кода.

---

## D-017 — Sync и async — две реальные реализации, не обёртки

**Status:** accepted

**Context:** Некоторые библиотеки предоставляют sync API как `asyncio.run(async_method())`.
Это создаёт event loop overhead и ограничения в threaded контекстах.

**Decision:** Если пакет поддерживает оба режима, это две независимые реализации с разными
бэкендами где возможно (например, `smtplib` vs `aiosmtplib`, `requests` vs `httpx`).
Именование: `Async{Name}` / `Sync{Name}`. Файлы: `async_.py` / `sync.py`.

**Consequences:**
- `AsyncRedisClient` использует `aioredis`, `SyncRedisClient` — `redis`.
- Нет event loop в sync-контексте.
- Объём кода выше, но поведение предсказуемо.

**What not to do:** не реализовывать sync как `asyncio.run(self.async_method(...))`.

---

## Инженерная Политика

Эти правила применяются к каждому изменению в репозитории. Они не являются ADR-записями,
но обязательны к соблюдению.

### Тесты

- Новый функционал всегда сопровождается тестами.
- Coverage ≥ 80% обязателен для каждого пакета. Проверяется через
  `uv run pytest --cov=src/axiom/<name> --cov-fail-under=80`.
- Unit tests обязательны. Integration tests — при взаимодействии с внешними системами
  (БД, Redis, S3, SMTP). Для integration tests предпочтителен testcontainers или
  приближённый к production подход (не mock-ование целых сервисов).
- Async тесты — через `pytest-asyncio` с `asyncio_mode = "auto"` (не нужны
  `@pytest.mark.asyncio` аннотации).

### Quality gates

После любого изменения кода должны проходить:

```bash
make test              # все тесты затронутых пакетов
make check-precommit   # ruff, mypy, pydocstyle, bandit
```

### Документация

При любом изменении функциональности проверить и при необходимости обновить:

- `README.md` затронутого пакета
- `docs/architecture.md` — если меняется архитектурная картина
- `docs/plugins.md` — если меняется статус или API пакета
- `docs/quickstart.md` — если меняется базовый сценарий использования
- `docs/development.md` — если меняется процесс разработки
- Корневой `README.md` — если меняется список рабочих пакетов или quick start

**Правило:** README документирует только реально существующий и протестированный API.
Stub-пакеты явно помечены как skeleton. Aspirational promises запрещены.

---

## Когда Обновлять Этот Файл

Добавить новую запись когда:

- принято решение о новом паттерне, которое неочевидно из кода
- принято решение отклонить популярный альтернативный подход (тогда "what not to do" особенно важен)
- добавляется новый пакет с нестандартной структурой
- существующее правило меняется

Не нужно добавлять записи для:

- очевидных coding style решений (они в `.planning/codebase/CONVENTIONS.md`)
- решений, которые полностью следуют из существующих записей
- временных технических долгов (они в `.planning/codebase/CONCERNS.md`)

---

## D-018 — axiom-clickhouse: clickhouse-connect, FilterRequest из axiom-core, специализированные ABC

**Status:** accepted

**Context:** ClickHouse — аналитическая СУБД с принципиально иной природой операций (append,
мутации, ReplacingMergeTree). Нужно было решить: использовать ли общую базу с `axiom-opensearch`,
выбрать ли один монолитный класс или специализированные ABC, и как передавать фильтры.

**Decision:**

1. **`clickhouse-connect` как единственный клиент** — поддерживает sync (`get_client`) и async
   (`get_async_client`) с реальными клиентами, без fake-async обёрток. Native protocol
   (`clickhouse-driver`) не включён — HTTP достаточен для аналитических задач.

2. **Нет общей базы с `axiom-opensearch`** — оба пакета независимы. Попытка создать общий
   OLAP-базовый класс привела бы к ложным абстракциям: операции ClickHouse и OpenSearch
   семантически несовместимы.

3. **Специализированные ABC** вместо монолитного класса:
   `ClickHouseReadRepository`, `ClickHouseWriteRepository`, `ClickHouseAggRepository`,
   `ClickHouseSchemaManager`, `ClickHouseMutationManager`. `ClickHouseRepository` — facade,
   объединяющий их через composition/multiple inheritance.

4. **`FilterRequest`/`FilterParam`/`QueryOperator` из `axiom-core`** — единый DSL фильтрации
   (как в `axiom-sqlalchemy` и `axiom-beanie`). CH-специфичные объекты (`AggregateSpec`,
   `GroupBySpec`, `MetricSpec`, `PageSpec`) — новые типы в `axiom.olap.clickhouse.query`.

5. **`VersionedClickHouseRepository`** — отдельный класс для append/versioned сценариев
   (ReplacingMergeTree), не наследует от `ClickHouseWriteRepository`.

**Consequences:**
- Consumer использует один `ClickHouseRepository` для типовых сценариев или специализированные
  ABC для тонкой настройки.
- `update_by_filter`/`delete_by_filter` существуют, но с явными docstring-предупреждениями
  об async-природе мутаций ClickHouse.
- Typed API доступен через `TypedClickHouseRepository[T]` с `row_factory`.

**What not to do:** не добавлять общий OLAP-базовый класс для ClickHouse и OpenSearch.
Не реализовывать sync как обёртку над async (см. D-017).

---

## Открытые Вопросы / Отложенные Решения

### OQ-001 — Миграция structlog → loguru в axiom-fastapi

`axiom-fastapi` и `axiom-sqlalchemy/exception_handler` используют `structlog`. Миграция на
`axiom.core.logger.get_logger()` запланирована, но не выполнена. До завершения миграции
приложения с обоими пакетами будут иметь смешанный формат логов.

### OQ-002 — Versioning и CHANGELOG policy

Все 13 пакетов находятся на версии `0.1.0`. Нет инструментария для bumping и нет CHANGELOG.
Это осложняет отслеживание breaking changes между пакетами. Решение о versioning policy
(semver, calendar versioning, mono-version) не зафиксировано.

### OQ-003 — axiom-fastapi как hard dependency для exception_handler в axiom-sqlalchemy

`IntegrityErrorHandler` в `axiom-sqlalchemy` зависит от FastAPI. Это сделано через optional
dependency группу. Не решено окончательно: стоит ли держать FastAPI-зависимые части в
отдельном sub-package или optional deps достаточно.
