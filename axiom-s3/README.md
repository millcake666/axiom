# axiom-s3

S3-compatible object storage integration using `aiobotocore` for async operations.

## Installation

```bash
uv add axiom-s3
```

## Usage

```python
from axiom.s3 import S3Client, create_s3_client
from axiom.s3 import S3Object, BucketConfig
```

## Features

- Async S3 client via `aiobotocore`
- Compatible with AWS S3, MinIO, and other S3-compatible storage
- Upload, download, delete, list objects
- Presigned URL generation
- Multipart upload support
