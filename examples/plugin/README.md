# Новый плагин — Golden Path

Пошаговый шаблон создания нового axiom-пакета с нуля.
**Копируй структуру, подставляй своё имя.**

Canonical reference: `axiom-cache/` — самый полный и зрелый пример.

---

## Когда создавать новый плагин

Новый пакет оправдан, если:
- интеграция независима от остальных (например, `axiom-vault` не зависит от `axiom-fastapi`)
- потребитель должен устанавливать только нужное: `uv add axiom-cache`, а не тянуть весь стек
- пакет может использоваться в нескольких сервисах как библиотека

Не создавай пакет ради одной утилиты внутри сервиса.

---

## 1. Структура (обязательный минимум)

```
axiom-{name}/
├── pyproject.toml
├── README.md
└── src/
    └── axiom/
        └── {name}/
            ├── __init__.py        ← публичный API
            └── exception/
                └── __init__.py    ← пакет-специфичные исключения
```

Для пакетов с реальными бэкендами (I/O, внешние сервисы):

```
axiom-{name}/
├── pyproject.toml
├── README.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_*.py
└── src/
    └── axiom/
        └── {name}/
            ├── __init__.py
            ├── base/
            │   └── __init__.py    ← ABC контракт
            ├── {backend}/
            │   ├── async_.py      ← Async{Name}
            │   └── sync.py        ← Sync{Name}
            └── exception/
                └── __init__.py
```

---

## 2. pyproject.toml

```toml
[project]
name = "axiom-{name}"
version = "0.1.0"
description = "Axiom {name} — one-line description"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "axiom-core",
    # добавь реальные зависимости
]

[dependency-groups]
dev = [
    "mypy>=1.16.0,<2",
    "pytest>=8.0.0,<9",
    "pytest-asyncio>=0.24.0,<1",
    "pytest-cov>=4.0.0",
    "ruff>=0.11.13,<1",
    # добавь fake-библиотеки для тестов (fakeredis, aiosqlite и т.д.)
]

[tool.uv.sources]
axiom-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/axiom"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

После создания — добавь `"axiom-{name}"` в `[tool.uv.workspace] members` корневого `pyproject.toml`.

---

## 3. src/axiom/{name}/__init__.py

```python
"""axiom.{name} — One-line package description."""

__version__ = "0.1.0"

from axiom.{name}.base import Async{Name}Backend, Sync{Name}Backend
from axiom.{name}.exception import Axiom{Name}Error

__all__ = [
    "Async{Name}Backend",
    "Axiom{Name}Error",
    "Sync{Name}Backend",
]
```

Правила:
- `__all__` сортируется алфавитно
- только контракт (ABC или Protocol) и исключения в публичном API
- конкретные реализации (`Redis{Name}`, `InMemory{Name}`) добавляются явно

---

## 4. exception/__init__.py

```python
"""axiom.{name}.exception — Exceptions for the axiom.{name} package."""

from axiom.core.exceptions.base import BaseError


class Axiom{Name}Error(BaseError):
    """Base exception for axiom.{name}."""

    code = "{name}_error"
    status_code = 500


__all__ = ["Axiom{Name}Error"]
```

Правила:
- всегда наследуй от `BaseError`, не от `Exception`
- `code` и `status_code` — class-level атрибуты
- если нужна детализация — наследуй от `Axiom{Name}Error`, не от `BaseError`

---

## 5. ABC контракт (если пакет — backend)

```python
"""axiom.{name}.base — Abstract backend interface."""

from abc import ABC, abstractmethod


class Async{Name}Backend(ABC):
    """Abstract base for async {name} backends."""

    @abstractmethod
    async def operation(self, ...) -> ...:
        """Docstring — что делает операция."""

    @abstractmethod
    async def startup(self) -> None:
        """Initialize resources."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Release resources."""


class Sync{Name}Backend(ABC):
    """Abstract base for synchronous {name} backends."""

    @abstractmethod
    def operation(self, ...) -> ...:
        """Docstring."""


__all__ = ["Async{Name}Backend", "Sync{Name}Backend"]
```

Используй ABC когда axiom контролирует обе стороны (и контракт, и реализацию).
Используй `Protocol` когда consumer реализует интерфейс без зависимости от axiom.
Подробнее: `axiom-email/src/axiom/email/interfaces.py` (Protocol).

---

## 6. Реализация бэкенда

```python
"""axiom.{name}.{backend}.async_ — Async {backend} backend."""

from axiom.{name}.base import Async{Name}Backend
from axiom.{name}.exception import Axiom{Name}Error


class Async{Backend}{Name}(Async{Name}Backend):
    """Async {backend}-backed {name} backend."""

    def __init__(self, client: ...) -> None:
        self._client = client

    async def operation(self, ...) -> ...:
        try:
            return await self._client.do_something(...)
        except SomeExternalError as exc:
            raise Axiom{Name}Error(str(exc)) from exc
```

- Не пробрасывай исключения сторонних библиотек наружу — оборачивай в `Axiom{Name}Error`.
- Логируй через `axiom.core.logger.get_logger("axiom.{name}.{backend}")`.

---

## 7. Тесты

```python
# tests/conftest.py
import pytest
from axiom.{name}.{backend}.async_ import Async{Backend}{Name}

@pytest.fixture
async def backend():
    # используй fake (fakeredis, in-memory), не мокай клиентский класс
    ...
    yield backend


# tests/test_async_backend.py
class TestAsync{Backend}{Name}:
    async def test_operation_success(self, backend):
        result = await backend.operation(...)
        assert result == expected

    async def test_operation_error(self, backend):
        with pytest.raises(Axiom{Name}Error):
            await backend.operation(invalid_input)
```

---

## Чеклист нового плагина

- [ ] Добавлен в `[tool.uv.workspace] members` корневого `pyproject.toml`
- [ ] `src/axiom/` и `src/axiom/{namespace}/` — без `__init__.py` (namespace packages)
- [ ] `src/axiom/{name}/__init__.py` содержит `__version__ = "0.1.0"` и `__all__`
- [ ] `exception/__init__.py` наследует от `BaseError`
- [ ] Async и sync варианты оба реализованы (если есть I/O)
- [ ] Тесты в `tests/` с `conftest.py`
- [ ] `make test` проходит
- [ ] `make check-precommit` проходит
- [ ] `README.md` описывает только реальный API
