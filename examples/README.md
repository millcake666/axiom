# Canonical Examples

Папка `examples/` содержит **golden path** примеры — конкретные шаблоны кода,
которые агент или разработчик должен использовать как образец при добавлении нового кода.

Примеры **не являются runnable-приложениями**. Их цель — показать правильную структуру
и код, который можно копировать. Все паттерны основаны на реальном коде в репозитории.

Полный справочник правил: [`docs/patterns.md`](../docs/patterns.md)
Зафиксированные решения: [`docs/decisions.md`](../docs/decisions.md)

---

## Canonical Examples

| Example | Паттерн | Когда использовать |
|---|---|---|
| [`plugin/`](./plugin/README.md) | Создание нового axiom-пакета | Новая независимая интеграция (cache, email, vault, ...) |
| [`crud/`](./crud/README.md) | `endpoint → controller → repository` | Простые CRUD-сервисы, admin API, internal tools |
| [`ddd/`](./ddd/README.md) | `endpoint → controller → use case → repository` | Насыщенная доменная логика, несколько агрегатов |

---

## Что откуда копировать

### `plugin/` — новый плагин

- **pyproject.toml** — структура зависимостей, hatchling build target
- **`__init__.py`** — как объявить `__version__` и `__all__`
- **`exception/__init__.py`** — как наследовать от `BaseError`
- **ABC контракт** — шаблон `AsyncBackend` / `SyncBackend`
- **Чеклист** — что проверить перед первым коммитом

### `crud/` — CRUD сервис

- **ORM model** — `Base`, `TimestampMixin`, `AsDictMixin`, `lazy="selectin"`
- **Repository** — `pass`-тело для базового API; кастомный метод только при необходимости
- **Controller** — `super().__init__(...)`, `@transactional` для кастомной логики
- **Factory** — `partial(Repository, model=Model)`, сборка в `Depends`
- **Router** — `exclude_unset=True` для PATCH, structured logging, `response_model`
- **Тесты** — in-memory SQLite conftest, `_make_entity(**kwargs)` helper

### `ddd/` — DDD сервис

- **Domain entity** — `@dataclass(BaseDomainDC)`, бизнес-методы в entity, не в use case
- **Use case** — оркестрация без транзакций, без HTTP-деталей
- **Controller** — тонкий, делегирует в use case, управляет транзакцией через `@transactional`
- **Factory** — инъекция use case через constructor, не через `Depends`
- **Стратегия тестов** — domain entity unit-тесты отдельно от use case integration-тестов

---

## Canonical Reference Files (в репозитории)

| Что ищешь | Файл |
|---|---|
| Эталонный плагин (полный) | `axiom-cache/` |
| ABC backend | `axiom-cache/src/axiom/cache/base/__init__.py` |
| Protocol backend | `axiom-email/src/axiom/email/interfaces.py` |
| BaseError | `axiom-core/src/axiom/core/exceptions/base.py` |
| Domain entity | `axiom-core/src/axiom/core/entities/domain.py` |
| Test conftest (DB) | `oltp/axiom-sqlalchemy/tests/conftest.py` |
| Test fixtures (models) | `oltp/axiom-sqlalchemy/tests/fixtures/models.py` |
