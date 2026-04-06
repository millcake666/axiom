"""Tests for FunctionKeyMaker."""

from axiom.cache.key_maker.function_key_maker import FunctionKeyMaker


def sample_function(x: int, y: int) -> int:
    """Sample function for testing."""
    return x + y


class TestFunctionKeyMaker:
    """Tests for FunctionKeyMaker."""

    def test_make_key_no_args(self) -> None:
        """make_key with no args produces expected format."""
        km = FunctionKeyMaker(project_name="proj")
        key = km.make_key(sample_function)
        assert "sample_function" in key
        assert "proj" in key

    def test_make_key_with_positional_args(self) -> None:
        """make_key includes positional arg values."""
        km = FunctionKeyMaker()
        key = km.make_key(sample_function, 1, 2)
        assert "1" in key
        assert "2" in key

    def test_make_key_with_kwargs(self) -> None:
        """make_key includes keyword arg values."""
        km = FunctionKeyMaker()
        key = km.make_key(sample_function, x=10, y=20)
        assert "x=10" in key
        assert "y=20" in key

    def test_make_mask_key(self) -> None:
        """make_mask_key includes wildcard and function name."""
        km = FunctionKeyMaker(project_name="proj")
        mask = km.make_mask_key(sample_function)
        assert "(*)" in mask
        assert "sample_function" in mask
        assert "proj" in mask

    def test_make_function_param(self) -> None:
        """make_function_param formats name=value."""
        km = FunctionKeyMaker()
        result = km.make_function_param("user_id", 42)
        assert result == "user_id=42"

    def test_keys_differ_for_different_args(self) -> None:
        """Different arguments produce different keys."""
        km = FunctionKeyMaker()
        key1 = km.make_key(sample_function, 1, 2)
        key2 = km.make_key(sample_function, 3, 4)
        assert key1 != key2

    def test_key_includes_module(self) -> None:
        """make_key includes the function module."""
        km = FunctionKeyMaker()
        key = km.make_key(sample_function)
        assert "test_key_maker" in key
