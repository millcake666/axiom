# axiom-tracing

Distributed tracing via OpenTelemetry with Jaeger export, integrated with `axiom-fastapi` and `axiom-middleware`.

## Installation

```bash
uv add axiom-tracing
```

## Usage

```python
from axiom.tracing import setup_tracing, get_tracer
from axiom.tracing import JaegerExporter
```

## Features

- OpenTelemetry SDK setup and configuration
- Jaeger exporter integration
- Automatic span propagation via `axiom.core.context`
- FastAPI middleware for trace context injection
- Correlation with `request_id`, `trace_id` from `axiom.core.context`
