"""Placeholder sanity test."""


def test_import():
    """Verify axiom.core is importable and has correct version."""
    import axiom.core  # noqa: F401

    assert axiom.core.__version__ == "0.1.0"
