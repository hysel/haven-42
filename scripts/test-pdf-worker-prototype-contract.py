#!/usr/bin/env python3
"""Verify the PDF worker remains a review-only, unpackaged prototype."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def top_level_imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    contract = load("config/pdf-parser-worker-prototype-contract.json")
    artifact = load("config/pdf-parser-artifact-lock.json")
    foundation = load("config/restricted-parser-worker-contract.json")
    evidence = load("config/pdf-parser-prospective-package-evidence.json")
    checks: list[str] = []

    def require(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    require(contract["schemaVersion"] == 1, "versioned prototype")
    require(contract["status"] == "offline-security-prototype-not-runtime-admitted", "prototype status")
    require(contract["artifact"]["package"] == "pypdf", "parser identity")
    require(contract["artifact"]["version"] == "6.14.2", "parser version")
    require(contract["artifact"]["sha256"] == artifact["artifact"]["sha256"], "artifact digest parity")
    require(contract["artifact"]["installed"] is False, "artifact not installed")
    require(contract["artifact"]["retainedInRepository"] is False, "artifact not retained")
    review = contract["reviewAuthority"]
    require(review["exactArtifactReadAllowed"] is True, "exact artifact review read")
    require(review["syntheticFixtureReadAllowed"] is True, "synthetic fixture review read")
    require(review["parserImportForReviewAllowed"] is True, "review parser import")
    require(review["workerProcessForReviewAllowed"] is True, "review worker process")
    require(review["arbitraryDocumentPathAllowed"] is False, "arbitrary path denied")
    require(review["userDocumentAllowed"] is False, "user document denied")
    require(review["runtimeRouteAllowed"] is False, "runtime route denied")
    require(review["uiControlAllowed"] is False, "UI control denied")
    require(review["packageInclusionAllowed"] is False, "package inclusion denied")
    require(review["dependencyAdmissionGranted"] is False, "dependency admission denied")

    containment = contract["containment"]
    require(containment["isolatedPythonFlags"] == ["-I", "-S"], "isolated Python flags")
    require(containment["sitePackagesAllowed"] is False, "site packages denied")
    require(containment["bytecodeWritesAllowed"] is False, "bytecode writes denied")
    require(containment["networkPythonApisDenied"] is True, "network APIs denied")
    require(containment["childProcessPythonApisDenied"] is True, "child process APIs denied")
    require(containment["filesystemApisDeniedAfterExactArtifactImport"] is True, "filesystem APIs denied")
    require(containment["temporaryFilesAllowed"] is False, "temporary files denied")
    require(containment["parentWallTimeoutAndForcedTerminationRequired"] is True, "forced termination required")
    require(containment["parentStreamingOutputLimitsRequired"] is True, "streaming output limits required")
    require(containment["boundedDirectResidueSnapshotRequired"] is True, "bounded residue snapshot required")
    require(containment["productionGradeIsolationClaimed"] is False, "no production isolation claim")
    require(containment["windowsJobCpuMemoryProcessLimitsRequired"] is True, "Windows Job limits required")
    require(containment["windowsSuspendedAssignmentRequired"] is True, "Windows suspended assignment required")
    require(containment["windowsOsMemoryLimitImplemented"] is True, "Windows memory limit implemented")

    effects = contract["reviewEffects"]
    require(effects["parserImportedInWorker"] is True, "parser effect disclosed")
    require(effects["workerProcessStarted"] is True, "worker effect disclosed")
    require(effects["syntheticDocumentParsedInWorker"] is True, "synthetic parse effect disclosed")
    require(effects["networkUsed"] is False, "network effect denied")
    require(effects["temporaryFileWritten"] is False, "temporary write denied")
    require(effects["childProcessStarted"] is False, "child process effect denied")
    require(effects["runtimeAdmissionGranted"] is False, "runtime admission effect denied")
    require(effects["userDocumentRead"] is False, "user read effect denied")

    require(foundation["parserDependenciesAdmitted"] == [], "foundation dependency list empty")
    require(foundation["workerProcessAllowed"] is False, "foundation worker denied")
    require(foundation["runtimeRouteAllowed"] is False, "foundation route denied")
    require(all(value is False for value in foundation["effects"].values()), "foundation effects denied")

    require(evidence["status"] == "prospective-evidence-dependency-not-admitted", "prospective evidence status")
    require(evidence["component"]["artifactSha256"] == contract["artifact"]["sha256"], "evidence artifact parity")
    require(evidence["component"]["licenseSha256"] == artifact["license"]["sha256"], "evidence license parity")
    require(evidence["dependencyInventoryPlan"]["mandatoryDependencies"] == [], "no mandatory dependency plan")
    require(evidence["dependencyInventoryPlan"]["extrasSelected"] == [], "no extras selected")
    require(all(value is False for value in evidence["generation"].values()), "package evidence not generated")
    require(all(value is False for value in evidence["authority"].values()), "package authority denied")

    worker = ROOT / "scripts/restricted-pdf-worker.py"
    harness = ROOT / "scripts/run-restricted-pdf-worker.py"
    require(worker.is_file() and harness.is_file(), "prototype scripts present")
    require("pypdf" not in top_level_imported_roots(worker), "worker has no top-level parser import")
    require("pypdf" not in imported_roots(harness), "harness has no parser import")
    require("base64-over-stdin" in json.dumps(contract["transport"]), "stdin document transport")
    require(contract["transport"]["pathInWorkerRequestAllowed"] is False, "request path denied")

    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".css", ".html", ".js", ".py"}
    )
    require("restricted-pdf-worker" not in runtime_text, "runtime has no worker reference")
    require("run-restricted-pdf-worker" not in runtime_text, "runtime has no harness reference")
    require("pypdf" not in {
        root
        for path in (ROOT / "web").rglob("*.py")
        for root in imported_roots(path)
    }, "runtime has no parser import")

    specification = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    resource_manifest = (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8")
    require("pypdf" not in specification.lower(), "package specification excludes parser")
    require("restricted-pdf-worker" not in specification, "package specification excludes worker")
    require("pypdf" not in resource_manifest.lower(), "resource manifest excludes parser")
    require("restricted-pdf-worker" not in resource_manifest, "resource manifest excludes worker")

    serialized = json.dumps(contract).lower() + json.dumps(evidence).lower()
    require("192.168." not in serialized and "localhost" not in serialized, "no local endpoint disclosure")
    require(not re.search(r"[a-z]:\\\\|/home/", serialized), "no local path disclosure")

    print(f"PDF worker prototype contract passed {len(checks)} fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
