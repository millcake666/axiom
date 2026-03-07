# DDD Example

Demonstrates the `endpoint → controller → use case → repository` pattern using Axiom packages.

## Stack

- `axiom-fastapi` — FastAPI application base
- `axiom-sqlalchemy` — Repository with SQLAlchemy
- `axiom-core` — Settings, logging, exceptions, domain entities
- `axiom-middleware` — CORS, logging, auth, tracing middleware
- `axiom-task` — Background tasks via ARQ
- `axiom-lock` — Distributed locking for aggregate consistency
- `axiom-audit` — User action audit trail

## Structure

```
ddd/
├── app.py               # FastAPI application entry point
├── config.py            # App settings (via axiom.core.settings)
├── domain/
│   ├── entities/        # AggregateRoot subclasses (dataclasses)
│   └── use_cases/       # Business logic orchestration
├── infrastructure/
│   ├── models/          # SQLAlchemy ORM models
│   └── repositories/    # Repository implementations
├── api/
│   └── controllers/     # Route handlers (thin, delegate to use cases)
└── pyproject.toml
```
