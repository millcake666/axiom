#!/usr/bin/env python3
"""Run mypy on all workspace packages.

This script dynamically discovers all Python packages in the workspace
and runs mypy on each one separately to avoid duplicate module errors
with namespace packages.

Uses --namespace-packages and --explicit-package-bases flags for proper
namespace package support.

See: https://github.com/python/mypy/issues/8944
"""

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from mypy import api as mypy_api


def find_workspace_members(root: Path) -> list[Path]:
    """Find all workspace members by looking for pyproject.toml files."""
    members = []

    # Root-level packages: axiom-*/pyproject.toml
    for pyproject in root.glob("axiom-*/pyproject.toml"):
        members.append(pyproject.parent)

    # Nested packages: oltp/axiom-*/pyproject.toml, olap/axiom-*/pyproject.toml
    for prefix in ["oltp", "olap"]:
        prefix_path = root / prefix
        if prefix_path.exists():
            for pyproject in prefix_path.glob("axiom-*/pyproject.toml"):
                members.append(pyproject.parent)

    return sorted(members)


@contextmanager
def _mypypath(path: str) -> Generator[None, None, None]:
    """Temporarily set MYPYPATH to the given path."""
    old = os.environ.get("MYPYPATH")
    os.environ["MYPYPATH"] = path
    try:
        yield
    finally:
        if old is None:
            del os.environ["MYPYPATH"]
        else:
            os.environ["MYPYPATH"] = old


def run_mypy_on_package(pkg_path: Path) -> int:
    """Run mypy on a single package via the mypy Python API."""
    src_path = pkg_path / "src"

    if not src_path.exists():
        print(f"  Skipping {pkg_path.name}: no src directory")
        return 0

    print(f"  Checking {pkg_path.name}...")

    with _mypypath(str(src_path)):
        stdout, stderr, exit_status = mypy_api.run(
            [
                str(src_path),
                "--namespace-packages",
                "--explicit-package-bases",
            ],
        )

    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)

    return exit_status


def main() -> int:
    """Discover all workspace packages and run mypy on each one."""
    root = Path(__file__).parent.parent

    # Find all workspace members dynamically
    members = find_workspace_members(root)

    if not members:
        print("No workspace members found!")
        return 1

    print(f"Running mypy on {len(members)} packages...")

    failures = 0
    for member in members:
        ret = run_mypy_on_package(member)
        if ret != 0:
            failures += 1

    if failures:
        print(f"\n{failures} package(s) failed type checking")
        return 1
    else:
        print(f"\nAll {len(members)} packages passed type checking")
        return 0


if __name__ == "__main__":
    sys.exit(main())
