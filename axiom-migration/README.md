# axiom-migration

Database migration management via Alembic, integrated with `axiom-sqlalchemy` and `axiom-beanie`.

## Installation

```bash
uv add axiom-migration
```

## Usage

```python
from axiom.migration import MigrationRunner, run_migrations
```

## Features

- Alembic integration for SQLAlchemy migrations
- Auto-generation of migration scripts from model changes
- Multi-database migration support
- CLI commands for migration management
