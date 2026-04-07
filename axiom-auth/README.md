# axiom-auth

`axiom-auth` задуман как пакет для authentication и authorization внутри Axiom, но в текущем репозитории это пока только каркас.

## Текущий Статус

Сейчас в коде есть только package skeleton:

- `axiom.auth.basic`
- `axiom.auth.classic`
- `axiom.auth.token`
- `axiom.auth.oauth2`
- `axiom.auth.oauth2.keycloak`
- `axiom.auth.rbac`
- `axiom.auth.abac`

Рабочих handlers, DTO, policy engine, middleware или интеграционных адаптеров в этих модулях пока нет.

## Что Уже Реализовано

- namespace пакета и подпакетов;
- описательные docstring-и;
- папки `exception/` для будущего расширения.

## Чего Пока Нет

- стабильного public API;
- рабочих auth схем;
- тестов на функциональное поведение;
- примеров использования, которые имели бы практический смысл.

## Минимальный Пример

Публичный сценарий использования пока не стабилизирован.
На практике сейчас можно только импортировать модули как namespace-заготовки:

```python
import axiom.auth
import axiom.auth.basic
import axiom.auth.rbac
```

Это не дает готовой auth-логики и не должно рассматриваться как production usage.

## Предполагаемая Зона Ответственности

По структуре пакета видно такой замысел:

- базовая auth (`basic`, `classic`, `token`);
- OAuth2 / Keycloak;
- RBAC;
- ABAC.

Но это именно архитектурный замысел, а не реализованный функционал.

## Как Будет Документироваться Дальше

Когда в пакете появится рабочий код, README стоит расширить секциями:

- public API;
- конфигурация;
- интеграция с `axiom-fastapi`;
- минимальные auth flows;
- ограничения безопасности.

## Связанный Код

- `src/axiom/auth/`
- `tests/__init__.py`
