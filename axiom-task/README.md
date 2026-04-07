# axiom-task

`axiom-task` задуман как пакет для background и scheduled tasks, но в текущем репозитории пока реализован только как skeleton.

## Текущий Статус

Сейчас в коде присутствуют только namespace-заготовки:

- `axiom.task.celery`
- `axiom.task.arq`
- `axiom.task.middleware`
- `axiom.task.middleware.logging`
- `axiom.task.middleware.tracing`

Рабочих task abstractions, adapters или scheduler utilities пока нет.

## Что Уже Реализовано

- структура подпакетов;
- docstring-и;
- empty exception packages.

## Чего Пока Нет

- стабильного public API;
- готовых Celery/ARQ integrations;
- task registration/decorator layer;
- примеров реального использования.

## Минимальный Пример

Публичный сценарий использования пока не стабилизирован.
На текущем этапе корректнее считать пакет placeholder-ом.

## Предполагаемая Зона Ответственности

По структуре видно намерение покрыть:

- Celery;
- ARQ;
- middleware для observability.

Но кодовой реализации этих сценариев сейчас нет.

## Связанный Код

- `src/axiom/task/`
- `tests/__init__.py`
