# axiom-auth

Axiom authentication and authorization — multi-scheme auth support

## Installation

```bash
uv add axiom-auth
```

## Usage

```python
from axiom.auth import ...
```

## Supported Authentication Schemes

- `basic` — HTTP Basic authentication
- `email` — Email + password authentication
- `token` — API token authentication
- `oauth2` — OAuth2 / OpenID Connect
- `abac` — Attribute-Based Access Control
- `rbac` — Role-Based Access Control

## Planned Components

- `basic` — HTTP Basic auth handler
- `email` — Email/password auth handler
- `token` — API token auth handler
- `oauth2` — OAuth2 flow implementation
- `abac` — ABAC policy engine
- `rbac` — RBAC role management
