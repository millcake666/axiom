"""Unit tests for axiom.fastapi.rate_limiter.core.result."""

from datetime import datetime, timezone

from axiom.fastapi.rate_limiter.core.result import RateLimitResult


def _make_result(**kwargs: object) -> RateLimitResult:
    defaults: dict[str, object] = {
        "allowed": True,
        "key": "rl:ip:127.0.0.1",
        "limit": 100,
        "policy_name": "test",
        "remaining": 99,
        "reset_at": datetime.now(tz=timezone.utc),
    }
    defaults.update(kwargs)
    return RateLimitResult(**defaults)  # type: ignore[arg-type]


def test_result_allowed_true_when_remaining_positive() -> None:
    result = _make_result(allowed=True, remaining=5)
    assert result.allowed is True
    assert result.remaining == 5


def test_result_allowed_false_when_remaining_zero() -> None:
    result = _make_result(allowed=False, remaining=0)
    assert result.allowed is False
    assert result.remaining == 0


def test_result_fields_accessible() -> None:
    now = datetime.now(tz=timezone.utc)
    result = _make_result(
        allowed=True,
        key="rl:ip:1.2.3.4",
        limit=10,
        policy_name="my-policy",
        remaining=7,
        reset_at=now,
    )
    assert result.key == "rl:ip:1.2.3.4"
    assert result.limit == 10
    assert result.policy_name == "my-policy"
    assert result.reset_at == now
