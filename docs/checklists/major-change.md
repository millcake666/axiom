# Major Change Checklist

Checklist для агентов и разработчиков после крупного изменения в репозитории.

---

## Что считается major change

| Тип изменения | Примеры                                            |
|---|----------------------------------------------------|
| Новый пакет | `axiom-validator`, `oltp/axiom-beanie`             |
| Новый backend к плагину | `axiom-cache/redis/`, `axiom-queue/kafka/`         |
| Изменение базового класса / ABC | `BaseController`, `AsyncCacheBackend`, `BaseError` |
| Новый паттерн, принятый проектно | новый Factory-паттерн, новый DI-подход             |
| Переименование/перемещение пакета | `axiom-metrics` → `axiom-metric`                   |
| Новый внешний сервис-интеграция | ClickHouse, Vault, OpenSearch                      |
| Изменение namespace | структура `src/axiom/`                             |
| Изменение правил тестирования | новый testcontainer, отказ от мока                 |

---

## Checklist по группам

### 1. Codebase map (`.planning/codebase/`)

| Файл | Когда обновлять | Что меняется |
|---|---|---|
| `ARCHITECTURE.md` | новый пакет, новый слой, изменение иерархии | плагин в списке слоёв, ключевые абстракции |
| `STRUCTURE.md` | новая директория, переименование, перемещение | дерево рабочего пространства, namespace-конвенции |
| `CONVENTIONS.md` | новое правило именования, новый code pattern | именование классов/файлов, docstring-шаблоны |
| `INTEGRATIONS.md` | новый внешний сервис / удалён старый | запись в таблице сервисов, статус (implemented/stub) |
| `STACK.md` | новая библиотека в зависимостях, смена версии Python | список ключевых зависимостей |
| `TESTING.md` | новый тестовый подход, новая инфраструктура | testcontainer, новые fixtures, fakes |
| `CONCERNS.md` | новый tech debt / устранён старый | stub-only статус, security concerns |

### 2. Docs (`docs/`)

| Файл | Когда обновлять | Что меняется |
|---|---|---|
| `README.md` | новый пакет в feature-листе, изменение install | список фич, команды установки |
| `docs/architecture.md` | структурное изменение в системе плагинов | описание слоёв, dependency graph |
| `docs/plugins.md` | новый плагин, изменение API плагина | запись о пакете, его публичный API |
| `docs/quickstart.md` | новый quickstart-пример, устаревший паттерн | пример кода, импорты |
| `docs/development.md` | новый `make`-таргет, новый workflow шаг | команды разработки, pre-commit |
| `{package}/README.md` | изменение публичного API пакета | usage-примеры, API-таблица |

### 3. Agent context

| Файл | Когда обновлять | Что меняется |
|---|---|---|
| `docs/patterns.md` | новый паттерн или изменение существующего | код-пример, правило, когда применять |
| `docs/decisions.md` | принято архитектурное решение (ADR) | новая запись D-NNN |
| `examples/README.md` | добавлен/удалён пример | строка в таблице примеров |
| `examples/plugin/README.md` | изменился процесс создания плагина | структура, checklist, шаблоны |
| `examples/crud/README.md` | изменился CRUD-паттерн | код контроллера, router, тесты |
| `examples/ddd/README.md` | изменился DDD-паттерн | use case, domain entity, тесты |

---

## Release-quality checklist

```
[ ] Тесты написаны / обновлены для изменённого кода
[ ] Unit-тесты для domain logic (без DB, без I/O)
[ ] Integration-тесты с testcontainers, если добавлен реальный сервис
[ ] Edge cases: None-значения, пустые списки, неверные типы
[ ] make test — проходит без ошибок
[ ] make check-precommit — проходит (ruff, mypy, pre-commit hooks)
[ ] Все затронутые .planning/codebase/* обновлены
[ ] Все затронутые docs/* обновлены
[ ] module README обновлён, если изменился публичный API
[ ] docs/decisions.md — добавлена запись, если принято новое архитектурное решение
[ ] docs/patterns.md — обновлён/добавлен паттерн, если принята новая практика
[ ] examples/ обновлены, если изменился рекомендуемый паттерн
```

---

## Пример использования

**Задача**: добавлен новый пакет `axiom-vault` — HashiCorp Vault secrets backend.

После реализации пробегись по checklist:

| Группа | Действие |
|---|---|
| `ARCHITECTURE.md` | добавить `axiom-vault` в список слоёв / плагинов |
| `STRUCTURE.md` | добавить `axiom-vault/` в дерево workspace |
| `INTEGRATIONS.md` | добавить запись: Vault / HashiCorp / `hvac` / implemented |
| `STACK.md` | добавить `hvac` в ключевые зависимости |
| `CONCERNS.md` | если реализация неполная — добавить stub-only запись |
| `docs/plugins.md` | добавить раздел `axiom-vault` с API |
| `README.md` | добавить в feature-list |
| `docs/decisions.md` | добавить ADR, почему Vault (а не, например, AWS Secrets Manager) |
| `examples/plugin/README.md` | обновить checklist если изменился процесс |
| Tests | unit (mock client) + integration (testcontainers/vault) |
| `make test` | ✓ |
| `make check-precommit` | ✓ |
