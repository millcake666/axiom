# axiom-clickhouse

`axiom-clickhouse` задуман как OLAP-плагин для ClickHouse, но в текущем workspace это пока только package shell.

## Текущий Статус

Сейчас пакет содержит:

- `axiom.olap.clickhouse.__init__`
- `axiom.olap.clickhouse.exception`

Рабочего клиента, query layer, settings или ingestion utilities в коде нет.

## Что Уже Реализовано

- namespace пакета;
- docstring-и;
- место для будущих exceptions.

## Чего Пока Нет

- public API;
- конфигурации подключения;
- клиента для запросов;
- тестов поведения;
- реальных примеров использования.

## Минимальный Пример

Публичный сценарий использования пока отсутствует.
Документировать клиентский API сейчас было бы выдумкой.

## Предполагаемая Зона Ответственности

По структуре и названию пакета ожидается интеграция с ClickHouse для OLAP-задач, но это пока только намерение.

## Связанный Код

- `src/axiom/olap/clickhouse/`
- `tests/__init__.py`
