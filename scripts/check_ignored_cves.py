#!/usr/bin/env python3
"""Check if fixes have been released for CVEs suppressed in pip-audit config.

Reads --ignore-vuln=CVE-xxx entries from .pre-commit-config.yaml,
queries OSV API for all packages in uv.lock, and exits with code 1
if any suppressed CVE now has a fix version available.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

PRECOMMIT_CONFIG = Path(".pre-commit-config.yaml")
UV_LOCK = Path("uv.lock")
OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
OSV_VULN_URL = "https://api.osv.dev/v1/vulns/{}"


def get_ignored_cves() -> set[str]:
    """Extract CVE IDs suppressed via --ignore-vuln in .pre-commit-config.yaml.

    Returns:
        Set of CVE strings (e.g., ``{'CVE-2023-1234'}``).
    """
    text = PRECOMMIT_CONFIG.read_text()
    return set(re.findall(r"--ignore-vuln=(CVE-[\d-]+)", text))


def parse_uv_lock() -> list[tuple[str, str]]:
    """Return list of (name, version) from uv.lock."""
    text = UV_LOCK.read_text()
    packages = []
    for block in re.split(r"\[\[package]]", text)[1:]:
        name = re.search(r'^name\s*=\s*"([^"]+)"', block, re.MULTILINE)
        version = re.search(r'^version\s*=\s*"([^"]+)"', block, re.MULTILINE)
        if name and version:
            packages.append((name.group(1), version.group(1)))
    return packages


def query_osv_batch(packages: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Return OSV batch query results (one entry per package, with stub vuln ids only)."""
    queries = [
        {"version": ver, "package": {"name": name, "ecosystem": "PyPI"}} for name, ver in packages
    ]
    payload = json.dumps({"queries": queries}).encode()
    req = urllib.request.Request(  # noqa: S310
        OSV_BATCH_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    # nosec B310
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.load(resp).get("results", [])


def fetch_osv_vuln(osv_id: str) -> dict[str, Any] | None:
    """Fetch full vuln record by OSV ID (includes aliases and fix versions)."""
    url = OSV_VULN_URL.format(osv_id)
    try:
        # nosec B310
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            return json.load(resp)
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def main() -> int:
    """Check if fixes have been released for CVEs suppressed in pip-audit config.

    Queries OSV API for all packages in uv.lock and reports:
    - CVEs with fixes available (exit code 1)
    - CVEs without fixes yet
    - CVEs not found in OSV

    Returns:
        Exit code 1 if any suppressed CVE now has a fix, 0 otherwise.
    """
    ignored = get_ignored_cves()
    if not ignored:
        print("No suppressed CVEs found in .pre-commit-config.yaml")
        return 0

    packages = parse_uv_lock()
    if not packages:
        print("Could not parse uv.lock")
        return 0

    try:
        results = query_osv_batch(packages)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"OSV API error: {exc}")
        return 0

    # Map (name, version) → OSV results; fetch full records for alias+fix resolution
    found_fixes = False
    reported: set[str] = set()
    fetched_vulns: dict[str, Any] = {}  # osv_id → full record cache

    for (name, version), result in zip(packages, results, strict=False):
        for stub in result.get("vulns", []):
            osv_id = stub.get("id", "")
            if osv_id in fetched_vulns:
                full = fetched_vulns[osv_id]
            else:
                full = fetch_osv_vuln(osv_id) or {}
                fetched_vulns[osv_id] = full

            aliases = set(full.get("aliases", []))
            matched = ignored & ({osv_id} | aliases)
            if not matched or matched & reported:
                continue

            cve = next((c for c in matched if c.startswith("CVE-")), next(iter(matched)))
            reported.add(cve)

            fix_versions: list[str] = []
            for affected in full.get("affected", []):
                for rng in affected.get("ranges", []):
                    for event in rng.get("events", []):
                        if "fixed" in event:
                            fix_versions.append(event["fixed"])

            if fix_versions:
                found_fixes = True
                print(
                    f"[FIX AVAILABLE] {cve} ({name} {version}): "
                    f"fixed in {', '.join(fix_versions)}\n"
                    f"  → uv lock --upgrade-package {name}\n"
                    f"  → remove --ignore-vuln={cve} from .pre-commit-config.yaml",
                )
            else:
                print(f"[no fix yet]    {cve} ({name} {version}): still no patch released")

    # Report ignored CVEs not found in OSV at all
    for cve in ignored - reported:
        print(f"[not found]     {cve}: not found in OSV for any installed package")

    return 1 if found_fixes else 0


if __name__ == "__main__":
    sys.exit(main())
