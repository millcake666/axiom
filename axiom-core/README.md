# axiom-core

`axiom-core` — ядро Axiom. Это единственный пакет, на который опираются почти все остальные `axiom.*` модули.

## Когда Использовать

Берите `axiom-core`, если вам нужны:

- базовые settings-классы на `pydantic-settings`;
- единая иерархия ошибок;
- общие response schemas;
- context propagation через `ContextVar`;
- filter DSL, который потом понимают `axiom-sqlalchemy` и `axiom-beanie`;
- базовое логирование на `loguru`.

## Что Уже Реализовано

| Модуль | Основные сущности | Зона ответственности |
|---|---|---|
| `axiom.core.settings` | `BaseAppSettings`, `AppMixin`, `DebugMixin` | базовые настройки приложения |
| `axiom.core.exceptions` | `BaseError`, `NotFoundError`, `ValidationError`, `ErrorDetail` | единый error model |
| `axiom.core.context` | `TypedContextVar`, `RequestContext`, `REQUEST_CONTEXT` | request-scoped context |
| `axiom.core.filter` | `FilterParam`, `FilterGroup`, `FilterRequest`, `QueryOperator` | общий DSL для фильтрации |
| `axiom.core.logger` | `LoggerSettings`, `configure_logger`, `get_logger` | JSON/text logging |
| `axiom.core.schema` | `PaginationResponse`, `CountResponse` | общие response wrappers |
| `axiom.core.entities` | `BaseDomainDC`, `BaseSchema`, `BaseRequestSchema`, `BaseResponseSchema`, `PaginatedResponse` | dataclass/entity и Pydantic base types |
| `axiom.core.project` | `ProjectInfo` | чтение metadata из `pyproject.toml` |

## Установка

```bash
uv add axiom-core
```

## Минимальный Пример

```python
from axiom.core.filter import FilterParam, FilterRequest, QueryOperator
from axiom.core.logger import LoggerSettings, configure_logger, get_logger
from axiom.core.settings import AppMixin, BaseAppSettings, DebugMixin


class Settings(BaseAppSettings, AppMixin, DebugMixin):
    pass


settings = Settings()
configure_logger(LoggerSettings(LOG_FORMAT="auto", APP_STAGE=settings.APP_STAGE))

log = get_logger("demo")
log.info("service starting")

filters = FilterRequest(
    chain=FilterParam(
        field="email",
        value="alice@example.com",
        operator=QueryOperator.EQUALS,
    ),
)
```

## Public API

Самые важные импорты:

```python
from axiom.core.context import REQUEST_CONTEXT, RequestContext, set_request_context
from axiom.core.entities import BaseDomainDC, BaseRequestSchema, BaseResponseSchema, BaseSchema
from axiom.core.exceptions import BaseError, ErrorDetail, NotFoundError, ValidationError
from axiom.core.filter import FilterGroup, FilterParam, FilterRequest, QueryOperator
from axiom.core.logger import LoggerSettings, configure_logger, get_logger
from axiom.core.schema import CountResponse, PaginationResponse
from axiom.core.settings import AppMixin, BaseAppSettings, DebugMixin, make_env_prefix
```

## Интеграция С Другими Пакетами

- `axiom-fastapi` использует ошибки, `ProjectInfo` и request context.
- `axiom-sqlalchemy` и `axiom-beanie` используют filter DSL и response schemas.
- `axiom-email` и `axiom-objectstore` используют общий logger и exceptions base.

## Ограничения И Текущий Статус

- `axiom-core` уже пригоден как самостоятельный utility package.
- Логирование здесь строится на `loguru`, тогда как `axiom-fastapi` использует `structlog`; это важно учитывать в единой logging strategy.
- `PaginatedResponse` из `entities` и `PaginationResponse` из `schema` решают похожие, но не идентичные задачи. В прикладном коде лучше выбирать один стиль осознанно.

## Связанный Код

- `src/axiom/core/settings/`
- `src/axiom/core/exceptions/`
- `src/axiom/core/filter/`
- `tests/test_settings.py`
- `tests/test_exceptions.py`
- `tests/test_entities.py`
