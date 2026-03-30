"""Tests for axiom.cache.ttl.TTL."""

from axiom.cache.ttl import TTL


class TestTTL:
    """Tests for TTL.time() helper."""

    def test_hours_only(self) -> None:
        """Hours convert to seconds correctly."""
        assert TTL.time(hours=1) == 3600

    def test_minutes_only(self) -> None:
        """Minutes convert to seconds correctly."""
        assert TTL.time(minutes=5) == 300

    def test_seconds_only(self) -> None:
        """Seconds are returned as-is."""
        assert TTL.time(seconds=45) == 45

    def test_combined(self) -> None:
        """Combined hours, minutes, seconds sum correctly."""
        assert TTL.time(hours=1, minutes=30, seconds=15) == 3600 + 1800 + 15

    def test_zero(self) -> None:
        """No arguments returns zero."""
        assert TTL.time() == 0
