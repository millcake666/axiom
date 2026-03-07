# axiom-lock

Axiom distributed locking — distributed lock management

## Installation

```bash
uv add axiom-lock
```

## Usage

```python
from axiom.lock import ...
```

## Features

- Cascading lock support — parent lock acquisition automatically manages child locks
- Multiple lock backend support (Redis, database-based)

## Planned Components

- Distributed lock interfaces
- Redis-based lock implementation
- Cascading lock manager
