# mypy: disable-error-code="misc"
"""axiom.fastapi.rate_limiter.policy_provider.exception — Exceptions for the policy_provider package."""

from axiom.fastapi.rate_limiter.exception import RateLimitError

__all__ = [
    "PolicyProviderError",
]


class PolicyProviderError(RateLimitError):
    """Raised when a policy provider fails to load or deserialize policies."""

    code = "policy_provider_error"
    status_code = 503
