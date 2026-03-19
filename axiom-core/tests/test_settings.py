"""Tests for axiom.core.settings module."""

from axiom.core.settings import AppMixin, BaseAppSettings, DebugMixin, make_env_prefix


def test_base_settings_from_env(monkeypatch):
    """BaseAppSettings reads from environment."""
    monkeypatch.setenv("APP_NAME", "test-app")

    class MySettings(BaseAppSettings, AppMixin):
        pass

    s = MySettings()
    assert s.APP_NAME == "test-app"


def test_app_mixin():
    """AppMixin provides correct defaults."""

    class MySettings(BaseAppSettings, AppMixin):
        pass

    s = MySettings()
    assert s.APP_HOST == "0.0.0.0"  # noqa: S104  # nosec B104
    assert s.APP_PORT == 8000
    assert s.APP_STAGE == "dev"
    assert s.APP_NAME == "app"


def test_debug_mixin():
    """DebugMixin provides DEBUG=False by default."""

    class MySettings(BaseAppSettings, DebugMixin):
        pass

    s = MySettings()
    assert s.DEBUG is False


def test_env_prefix_utility():
    """make_env_prefix converts name to uppercase prefix."""
    assert make_env_prefix("my-service") == "MY_SERVICE_"
    assert make_env_prefix("app") == "APP_"
    assert make_env_prefix("My Service") == "MY_SERVICE_"


def test_settings_composition(monkeypatch):
    """Settings can compose multiple mixins."""
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_PORT", "9000")

    class MySettings(BaseAppSettings, AppMixin, DebugMixin):
        pass

    s = MySettings()
    assert s.DEBUG is True
    assert s.APP_PORT == 9000
