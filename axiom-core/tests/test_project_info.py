"""Tests for axiom.core.project.info — ProjectInfo."""

from pathlib import Path

import pytest

from axiom.core.project import ProjectInfo

SAMPLE_PYPROJECT = """\
[project]
name = "my-service"
version = "1.2.3"
description = "A sample service for testing."
"""

MINIMAL_PYPROJECT = """\
[project]
name = "minimal"
"""

EMPTY_PROJECT_SECTION = """\
[build-system]
requires = ["hatchling"]
"""


@pytest.fixture
def pyproject_dir(tmp_path: Path) -> Path:
    """Create a tmp dir with a pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text(SAMPLE_PYPROJECT)
    return tmp_path


@pytest.fixture
def pyproject_file(tmp_path: Path) -> Path:
    """Return path to pyproject.toml file directly."""
    f = tmp_path / "pyproject.toml"
    f.write_text(SAMPLE_PYPROJECT)
    return f


def test_get_name(pyproject_dir: Path) -> None:
    """get_name returns [project].name."""
    info = ProjectInfo(pyproject_dir)
    assert info.get_name() == "my-service"


def test_get_version(pyproject_dir: Path) -> None:
    """get_version returns [project].version."""
    info = ProjectInfo(pyproject_dir)
    assert info.get_version() == "1.2.3"


def test_get_description(pyproject_dir: Path) -> None:
    """get_description returns [project].description."""
    info = ProjectInfo(pyproject_dir)
    assert info.get_description() == "A sample service for testing."


def test_accepts_file_path(pyproject_file: Path) -> None:
    """ProjectInfo accepts a direct path to pyproject.toml file."""
    info = ProjectInfo(pyproject_file)
    assert info.get_name() == "my-service"
    assert info.get_version() == "1.2.3"


def test_accepts_string_path(pyproject_dir: Path) -> None:
    """ProjectInfo accepts string path."""
    info = ProjectInfo(str(pyproject_dir))
    assert info.get_name() == "my-service"


def test_missing_fields_return_empty_string(tmp_path: Path) -> None:
    """Missing version/description return empty string."""
    (tmp_path / "pyproject.toml").write_text(MINIMAL_PYPROJECT)
    info = ProjectInfo(tmp_path)
    assert info.get_name() == "minimal"
    assert info.get_version() == ""
    assert info.get_description() == ""


def test_no_project_section_returns_empty_strings(tmp_path: Path) -> None:
    """If [project] section absent, all getters return empty string."""
    (tmp_path / "pyproject.toml").write_text(EMPTY_PROJECT_SECTION)
    info = ProjectInfo(tmp_path)
    assert info.get_name() == ""
    assert info.get_version() == ""
    assert info.get_description() == ""


def test_real_axiom_core_pyproject() -> None:
    """ProjectInfo works on axiom-core's own pyproject.toml."""
    root = Path(__file__).parents[1]  # axiom-core/
    info = ProjectInfo(root)
    assert info.get_name() == "axiom-core"
    assert info.get_version() != ""
