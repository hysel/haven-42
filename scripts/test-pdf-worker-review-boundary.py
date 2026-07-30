#!/usr/bin/env python3
"""Check contract/implementation parity and package exclusion for the PDF prototype."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "scripts" / "restricted-pdf-worker.py"
HARNESS = ROOT / "scripts" / "run-restricted-pdf-worker.py"


def constants(path: Path) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values: dict[str, object] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    return values


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    contract = json.loads(
        (ROOT / "config/pdf-parser-worker-prototype-contract.json").read_text(encoding="utf-8")
    )
    worker_text = WORKER.read_text(encoding="utf-8")
    harness_text = HARNESS.read_text(encoding="utf-8")
    worker = constants(WORKER)
    limits = contract["limits"]
    expected = {
        "MAXIMUM_SERIALIZED_REQUEST_BYTES": limits["maximumSerializedRequestBytes"],
        "MAXIMUM_INPUT_BYTES": limits["maximumInputBytes"],
        "MAXIMUM_PAGES": limits["maximumPages"],
        "MAXIMUM_OBJECTS": limits["maximumObjects"],
        "MAXIMUM_NESTING_DEPTH": limits["maximumNestingDepth"],
        "MAXIMUM_EXPANSION_RATIO": limits["maximumExpansionRatio"],
        "MAXIMUM_EXPANDED_BYTES": limits["maximumExpandedBytes"],
        "MAXIMUM_OUTPUT_CHARACTERS": limits["maximumOutputCharacters"],
        "MAXIMUM_CPU_SECONDS": limits["maximumCpuSeconds"],
        "MAXIMUM_MEMORY_BYTES": limits["maximumMemoryBytes"],
        "ROOT_OBJECT_RECOVERY_LIMIT": contract["contentPolicy"]["rootObjectRecoveryLimit"],
    }
    checks = 0
    assert all(worker[name] == value for name, value in expected.items())
    checks += len(expected)
    assert worker["EXPECTED_WHEEL_NAME"] == contract["artifact"]["filename"]
    assert worker["EXPECTED_WHEEL_SHA256"] == contract["artifact"]["sha256"]
    assert worker["EXPECTED_PYPDF_VERSION"] == contract["artifact"]["version"]
    checks += 3
    for marker in (
        "resource.RLIMIT_CPU",
        "resource.RLIMIT_AS",
        "resource.RLIMIT_FSIZE",
        "resource.RLIMIT_NOFILE",
        "resource.RLIMIT_NPROC",
    ):
        assert marker in worker_text
        checks += 1
    for marker in (
        "subprocess.CREATE_NO_WINDOW | 0x00000004",
        "AssignProcessToJobObject",
        "NtResumeProcess",
        "bounded_process_io",
        "snapshot-entry-budget-exceeded",
    ):
        assert marker in harness_text
        checks += 1
    assert ".communicate(" not in harness_text and ".rglob(" not in harness_text
    checks += 2

    package_text = (ROOT / "package/haven42.spec").read_text(encoding="utf-8").lower()
    resources = (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8").lower()
    assert "pypdf" not in package_text and "restricted-pdf-worker" not in package_text
    assert "pypdf" not in resources and "restricted-pdf-worker" not in resources
    checks += 2
    for manifest in ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "poetry.lock"):
        path = ROOT / manifest
        if path.exists():
            assert "pypdf" not in path.read_text(encoding="utf-8").lower()
        checks += 1
    assert all(
        "restricted-pdf-worker" not in path.read_text(encoding="utf-8")
        and "run-restricted-pdf-worker" not in path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*.py")
    )
    checks += 1
    assert contract["reviewAuthority"]["runtimeRouteAllowed"] is False
    assert contract["reviewAuthority"]["packageInclusionAllowed"] is False
    assert contract["reviewAuthority"]["userDocumentAllowed"] is False
    checks += 3

    generator = ROOT / "scripts/generate-pdf-prospective-package-evidence.py"
    generator_text = generator.read_text(encoding="utf-8")
    assert imported_roots(generator).isdisjoint(
        {"pypdf", "requests", "socket", "subprocess", "urllib", "http"}
    )
    assert "dist\" / \"local-review\" / \"pdf-parser-prospective-package-evidence" in generator_text
    assert '"packageIncluded": False' in generator_text and '"runtimeAdmitted": False' in generator_text
    evidence = json.loads(
        (ROOT / "config/pdf-parser-prospective-package-evidence.json").read_text(encoding="utf-8")
    )
    assert not any(evidence["generation"].values()) and not any(evidence["authority"].values())
    checks += 4
    print(f"PDF worker review boundary passed {checks} contract-parity and exclusion checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
