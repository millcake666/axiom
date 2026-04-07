# axiom-opensearch

`axiom-opensearch` задуман как search/analytics-плагин для OpenSearch, но в текущем коде это пока только package shell.

## Текущий Статус

Сейчас в пакете есть только:

- `axiom.olap.opensearch.__init__`
- `axiom.olap.opensearch.exception`

Рабочего клиента, index management слоя и search abstractions нет.

## Что Уже Реализовано

- namespace пакета;
- docstring-и;
- папка для будущих exceptions.

## Чего Пока Нет

- public API;
- конфигурации;
- query/search utilities;
- integration tests;
- примеров использования.

## Минимальный Пример

Публичный сценарий использования пока не стабилизирован.
На текущем этапе корректнее считать пакет placeholder-ом.

## Предполагаемая Зона Ответственности

По названию и месту в дереве проекта пакет должен покрывать OpenSearch integration для поиска и аналитики, но этот слой пока не реализован.

## Связанный Код

- `src/axiom/olap/opensearch/`
- `tests/__init__.py`
