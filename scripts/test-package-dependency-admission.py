#!/usr/bin/env python3
"""Prove the admitted build dependency graph matches locks, code, and CI."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "package-dependency-admission.json"
REQUIREMENTS = ROOT / "package" / "requirements-build.txt"
BUILDER = ROOT / "scripts" / "build-portable-development-package.py"
WORKFLOW = ROOT / ".github" / "workflows" / "validate-pack.yml"
HASH = re.compile(r"--hash=sha256:([0-9a-f]{64})")
PIN = re.compile(r"^([a-zA-Z0-9_.-]+)==([^\s;\\]+)(?:;\s*sys_platform\s*==\s*\"([^\"]+)\")?")


def assignments(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in {"COMMON_BUILD_DISTRIBUTIONS", "PLATFORM_BUILD_DISTRIBUTIONS"}:
                values[node.targets[0].id] = ast.literal_eval(node.value)
    return values


def requirements() -> dict:
    records = {}
    current = None
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        match = PIN.match(line)
        if match:
            name, version, platform = match.groups()
            current = name.casefold()
            records[current] = {"version": version, "platform": platform or "all", "hashes": []}
        for digest in HASH.findall(line):
            assert current is not None
            records[current]["hashes"].append(digest)
    return records


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schemaVersion"] == 1
    assert contract["status"] == "unsigned-development-build-only"
    declared = contract["buildDependencies"]
    locked = requirements()
    assert set(locked) == set(declared)
    assert all(item["version"] == declared[name]["version"] for name, item in locked.items())
    assert all(item["platform"] == declared[name]["platform"] for name, item in locked.items())
    assert all(item["hashes"] and len(item["hashes"]) == len(set(item["hashes"])) for item in locked.values())
    code = assignments(BUILDER)
    mapped = dict(code["COMMON_BUILD_DISTRIBUTIONS"])
    for platform, items in code["PLATFORM_BUILD_DISTRIBUTIONS"].items():
        marker = {"Windows": "win32", "Darwin": "darwin", "Linux": "all"}[platform]
        for name, pair in items.items():
            assert declared[name]["platform"] == marker
            mapped[name] = pair
    assert {name: (item["version"], item["license"]) for name, item in declared.items()} == mapped
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert 'python-version: "3.14.6"' in workflow
    assert "--require-hashes -r package/requirements-build.txt" in workflow
    assert all(value is False for value in contract["unadmittedEcosystems"].values())
    assert all(value is False for value in contract["authority"].values())
    print("Package dependency admission passed 12 exact-lock and non-admission checks.")


if __name__ == "__main__":
    main()
