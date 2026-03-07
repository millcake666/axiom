# Axiom Examples

Reference applications demonstrating two primary architectural patterns supported by the Axiom ecosystem.

## Patterns

### 1. CRUD — Simple Repository Pattern

```
endpoint → controller → repository
```

Best for: straightforward CRUD operations, admin panels, simple APIs.

See [`crud/`](./crud/) for a complete example.

### 2. DDD — Domain-Driven Design with Use Cases

```
endpoint → controller → use case → repository
```

Best for: complex business logic, domain-rich services, multi-aggregate operations.

See [`ddd/`](./ddd/) for a complete example.

## Running Examples

```bash
# CRUD example
cd examples/crud
uv run uvicorn app:app --reload

# DDD example
cd examples/ddd
uv run uvicorn app:app --reload
```
