#!/usr/bin/env python3
"""Run mypy on all workspace packages.

This script dynamically discovers all Python packages in the workspace
and runs mypy on each one separately to avoid duplicate module errors
with namespace packages.

Uses --namespace-packages and --explicit-package-bases flags for proper
namespace package support.

See: https://github.com/python/mypy/issues/8944
"""

import subprocess
import sys
from pathlib import Path


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


def run_mypy_on_package(pkg_path: Path, root: Path) -> int:
    """Run mypy on a single package."""
    src_path = pkg_path / "src"
    
    if not src_path.exists():
        print(f"  Skipping {pkg_path.name}: no src directory")
        return 0
    
    print(f"  Checking {pkg_path.name}...")
    
    cmd = [
        sys.executable, "-m", "mypy",
        str(src_path),
        "--namespace-packages",
        "--explicit-package-bases",
        "--install-types",
        "--non-interactive",
    ]
    
    # Set MYPYPATH to include this package's src
    env = subprocess.os.environ.copy()
    env["MYPYPATH"] = str(src_path)
    
    result = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode


def main() -> int:
    root = Path(__file__).parent.parent
    
    # Find all workspace members dynamically
    members = find_workspace_members(root)
    
    if not members:
        print("No workspace members found!")
        return 1
    
    print(f"Running mypy on {len(members)} packages...")
    
    failures = 0
    for member in members:
        ret = run_mypy_on_package(member, root)
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
