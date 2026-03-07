# axiom-objectstore

Object and file storage integrations for the Axiom framework.

## Packages

| Package | Description |
|---|---|
| `axiom.objectstore.base` | Base classes (config, client factory) |
| `axiom.objectstore.abs` | Abstract repository interfaces |
| `axiom.objectstore.s3` | S3-compatible storage via `aiobotocore` |
| `axiom.objectstore.local` | Local disk storage |

## Usage

```python
from axiom.objectstore.s3 import S3ObjectStore
from axiom.objectstore.local import LocalObjectStore
```
