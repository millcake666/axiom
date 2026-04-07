# Разработка Axiom

## Workspace И Инструменты

Текущее состояние репозитория:

- package manager: `uv`
- Python: `3.13+`
- build system: `hatchling`
- issue tracking: `bd` / beads
- namespace model: PEP 420 (`axiom.*`)

Workspace members задаются в корневом `pyproject.toml`:

- `axiom-*`
- `oltp/axiom-*`
- `olap/axiom-*`

## Основные Команды

```bash
uv sync
make lint
make format
make check-types
make test
make check-precommit
```

Полезные команды по beads:

```bash
bd ready
bd show <id>
bd update <id> --status in_progress
bd close <id>
bd sync
```

## Как Устроен Пакет

Нормальный пакет в Axiom обычно содержит:

```text
axiom-some-package/
├── pyproject.toml
├── README.md
├── src/axiom/some_package/...
└── tests/...
```

Ожидаемые свойства:

- пакет публикуется отдельно;
- README описывает только реальный API;
- тесты лежат рядом с пакетом;
- общие абстракции по возможности переиспользуют `axiom-core`.

## Соглашения По Архитектуре

### Namespace packages

- на уровне `src/axiom/` нет общего `__init__.py`;
- импортный путь формируется по namespace, а не по имени дистрибутива;
- пример: пакет `axiom-core` импортируется как `axiom.core`.

### Документация

При любом изменении функциональности нужно обновлять:

- README затронутого пакета;
- при необходимости корневой `README.md`;
- общие docs в `docs/`, если меняется архитектурная картина или quickstart.

### Тесты

Текущий стиль репозитория:

- pytest в каждом пакете отдельно;
- async tests идут через `pytest-asyncio`;
- для Redis используется `fakeredis`;
- для MongoDB — `mongomock` / `mongomock-motor`;
- для email integration tests используется `testcontainers`.

## Как Добавлять Новый Плагин

Рекомендуемый порядок:

1. Создать новый workspace package с отдельным `pyproject.toml`.
2. Выбрать корректный namespace-путь в `src/axiom/...`.
3. Явно определить public API в `__init__.py`.
4. Добавить README с честным статусом и минимальными примерами.
5. Добавить тесты внутри пакета.
6. Проверить `make test` и `make check-precommit`.

## На Что Обратить Внимание В Текущем Коде

- `axiom-fastapi` и `axiom-core` пока используют разные logging stacks (`structlog` и `loguru`).
- `examples/` пока не содержат запускаемого example-кода.
- `axiom-sqlalchemy` и `axiom-beanie` — самые насыщенные пакеты, но и самые чувствительные к documentation drift.
- несколько пакетов пока существуют как skeleton-only; не стоит документировать им API "на вырост".

## Локальная Проверка Документации

Отдельного генератора docs в репозитории нет, поэтому базовая проверка практическая:

- markdown-файлы должны быть читаемы сами по себе;
- примеры должны использовать реальные import paths;
- README пакета не должен обещать несуществующий функционал;
- если модуль сырой, это должно быть явно сказано.
