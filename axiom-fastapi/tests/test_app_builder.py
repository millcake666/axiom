"""Tests for create_app() and AppConfig."""

from fastapi import FastAPI

from axiom.fastapi.app import AppConfig, create_app


def test_create_app_defaults() -> None:
    config = AppConfig()
    app = create_app(config)
    assert isinstance(app, FastAPI)
    assert app.title == "Axiom API"


def test_create_app_with_title() -> None:
    config = AppConfig(title="My App", version="1.0.0", description="test")
    app = create_app(config)
    assert app.title == "My App"
    assert app.version == "1.0.0"


def test_create_app_no_default_handlers() -> None:
    config = AppConfig(register_default_handlers=False)
    app = create_app(config)
    assert isinstance(app, FastAPI)


def test_create_app_with_pyproject(tmp_path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test-svc"\nversion = "2.0.0"\ndescription = "Test"\n',
    )
    config = AppConfig(pyproject_path=tmp_path)
    assert config.title == "test-svc"
    assert config.version == "2.0.0"
