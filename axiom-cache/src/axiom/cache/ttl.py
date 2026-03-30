"""axiom.cache.ttl — TTL utilities for cache expiration."""


class TTL:
    """Helper for computing TTL values in seconds."""

    @staticmethod
    def time(hours: int = 0, minutes: int = 0, seconds: int = 0) -> int:
        """Return total TTL in seconds from the given time components."""
        return hours * 3600 + minutes * 60 + seconds
