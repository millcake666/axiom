# CRUD Example

Demonstrates the simple `endpoint → controller → repository` pattern using Axiom packages.

## Stack

- `axiom-fastapi` — FastAPI application base
- `axiom-sqlalchemy` — Repository with SQLAlchemy
- `axiom-core` — Settings, logging, exceptions
- `axiom-middleware` — CORS, logging, auth middleware

## Structure

```
crud/
├── app.py               # FastAPI application entry point
├── config.py            # App settings (via axiom.core.settings)
├── models/              # SQLAlchemy ORM models
├── repositories/        # Data access layer
├── controllers/         # Route handlers
└── pyproject.toml
```
