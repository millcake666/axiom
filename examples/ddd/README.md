# DDD Сценарий

Этот каталог описывает целевой паттерн `endpoint -> controller -> use case -> repository`.

## Когда Такой Подход Подходит

- насыщенная доменная логика;
- несколько агрегатов в одном сценарии;
- явное разделение application layer и persistence layer;
- long-running evolution сервиса, где важно не смешивать HTTP и доменную модель.

## Целевая Структура

```text
ddd/
├── app.py
├── config.py
├── api/controllers/
├── domain/entities/
├── domain/use_cases/
└── infrastructure/repositories/
```

## Текущий Статус

Этот README стоит воспринимать как архитектурное направление, а не как готовый пример на основе существующего кода.
