"""axiom.core.project.info — ProjectInfo: reads metadata from pyproject.toml."""

from pathlib import Path

import tomlkit


class ProjectInfo:
    """Read project metadata from a pyproject.toml file.

    Args:
        main_path: Path to the directory containing pyproject.toml, or the
            file itself.
    """

    def __init__(self, main_path: str | Path) -> None:
        """Initialize ProjectInfo and load pyproject.toml.

        Args:
            main_path: Directory or file path pointing to pyproject.toml.
        """
        path = Path(main_path)
        if path.is_dir():
            path = path / "pyproject.toml"
        with path.open("rb") as f:
            self._data = tomlkit.load(f)
        self._project = self._data.get("project", {})

    def get_name(self) -> str:
        """Return the project name from [project].name.

        Returns:
            Project name string, or empty string if not set.
        """
        return str(self._project.get("name", ""))

    def get_version(self) -> str:
        """Return the project version from [project].version.

        Returns:
            Project version string, or empty string if not set.
        """
        return str(self._project.get("version", ""))

    def get_description(self) -> str:
        """Return the project description from [project].description.

        Returns:
            Project description string, or empty string if not set.
        """
        return str(self._project.get("description", ""))
