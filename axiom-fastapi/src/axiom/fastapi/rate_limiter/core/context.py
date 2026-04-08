"""axiom.fastapi.rate_limiter.core.context — Request context for policy evaluation."""

from dataclasses import dataclass

__all__ = [
    "RequestContext",
]


@dataclass
class RequestContext:
    """Lightweight request context passed to PolicyProvider.get_policies().

    Deliberately decoupled from FastAPI / Starlette — can be built from any
    request type and extended without touching the provider interface.
    """

    path: str
    method: str
    client_ip: str
    user_id: str | None = None
    tenant_id: str | None = None
