"""Shared pytest fixtures for axiom-objectstore tests."""

import os

import pytest

from axiom.objectstore.s3.config import S3Config


@pytest.fixture()
def s3_config() -> S3Config:
    """Return a minimal S3Config for testing."""
    return S3Config(
        aws_access_key_id=os.environ.get("TEST_S3_ACCESS_KEY_ID", "test-key"),
        aws_secret_access_key=os.environ.get("TEST_S3_SECRET_ACCESS_KEY", "test-secret"),
        endpoint_url="https://s3.example.com",
        region_name="us-east-1",
        bucket_name="test-bucket",
    )
