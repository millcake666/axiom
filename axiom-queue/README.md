# axiom-queue

`axiom-queue` задуман как пакет для очередей, stream/backends и queue middleware, но в текущем workspace это пока только skeleton.

## Текущий Статус

Сейчас в коде есть только namespace-заготовки:

- `axiom.queue.rabbitmq`
- `axiom.queue.redis_stream`
- `axiom.queue.kafka`
- `axiom.queue.middleware`
- `axiom.queue.middleware.logging`
- `axiom.queue.middleware.tracing`

Рабочих producer/consumer abstractions, DTO и transport integrations пока нет.

## Что Уже Реализовано

- структура подпакетов;
- docstring-и;
- пустые `exception/` подпакеты.

## Чего Пока Нет

- public API;
- backend implementations;
- middleware contract;
- functional tests и реальные examples.

## Минимальный Пример

Публичный сценарий использования пока отсутствует.
Текущий пакет имеет смысл рассматривать как заготовку под будущую реализацию.

## Предполагаемая Зона Ответственности

По структуре пакета предполагаются:

- RabbitMQ backend;
- Redis Streams backend;
- Kafka backend;
- logging/tracing middleware.

Но это пока архитектурный каркас, а не готовая функциональность.

## Связанный Код

- `src/axiom/queue/`
- `tests/__init__.py`
