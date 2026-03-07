забыл# axiom-grpc

Axiom gRPC integration — gRPC server and client support

## Installation

```bash
uv add axiom-grpc
```

## Usage

```python
from axiom.grpc import

...
```

## Use Cases

### gRPC Server

Host gRPC services within your Axiom-based application. Supports service discovery,
health checks, and interceptors for cross-cutting concerns.

### gRPC Client

Connect to external gRPC services (third-party or internal). Includes connection pooling,
retry logic, and deadline management.

## Planned Components

- gRPC server base classes and interceptors
- gRPC client factory and connection management
- Protobuf serialization utilities
- Health check implementation
