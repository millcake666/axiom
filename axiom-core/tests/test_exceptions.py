"""Tests for axiom.core.exceptions module."""

import pytest

from axiom.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    BaseError,
    ConflictError,
    ErrorDetail,
    InternalError,
    NotFoundError,
    UnprocessableError,
    ValidationError,
)


def test_base_error_fields():
    """BaseError has correct fields."""
    err = BaseError("something failed", code="custom_error", details={"key": "val"})
    assert err.message == "something failed"
    assert err.code == "custom_error"
    assert err.details == {"key": "val"}
    assert err.status_code == 500


def test_each_error_class_defaults():
    """Each error class has correct default code and status_code."""
    cases = [
        (NotFoundError, "not_found", 404),
        (ValidationError, "validation_error", 422),
        (ConflictError, "conflict", 409),
        (AuthenticationError, "authentication_error", 401),
        (AuthorizationError, "authorization_error", 403),
        (BadRequestError, "bad_request", 400),
        (UnprocessableError, "unprocessable", 422),
        (InternalError, "internal_error", 500),
    ]
    for cls, code, status in cases:
        err = cls("test")
        assert err.code == code, f"{cls.__name__} code mismatch"
        assert err.status_code == status, f"{cls.__name__} status mismatch"


def test_error_detail_serialization():
    """ErrorDetail serializes to dict correctly."""
    err = NotFoundError("user not found", details={"id": 1})
    detail = ErrorDetail.from_error(err)
    data = detail.model_dump()
    assert data["code"] == "not_found"
    assert data["message"] == "user not found"
    assert data["details"] == {"id": 1}


def test_status_codes():
    """All errors have expected HTTP status codes."""
    assert NotFoundError("x").status_code == 404
    assert ValidationError("x").status_code == 422
    assert ConflictError("x").status_code == 409
    assert AuthenticationError("x").status_code == 401
    assert AuthorizationError("x").status_code == 403
    assert BadRequestError("x").status_code == 400
    assert UnprocessableError("x").status_code == 422
    assert InternalError("x").status_code == 500


def test_base_error_is_exception():
    """BaseError is an Exception subclass."""
    with pytest.raises(BaseError):
        raise BaseError("test error")
