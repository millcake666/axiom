# axiom-vault

HashiCorp Vault integration for secrets management, works as a backend for `axiom.core.settings`.

## Installation

```bash
uv add axiom-vault
```

## Usage

```python
from axiom.vault import VaultClient, VaultSettings
from axiom.vault import KVSecretEngine, AppRoleAuth, KubernetesAuth
```

## Features

- KV v1/v2 secrets engine support
- Multiple auth methods: AppRole, Kubernetes, Token
- Pluggable backend for `axiom.core.settings.BaseSettings`
- Dynamic secrets (database credentials, etc.)
- Secret caching with TTL-based renewal
