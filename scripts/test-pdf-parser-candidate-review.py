#!/usr/bin/env python3
"""Verify the reviewed PDF parser candidate remains fail-closed and unadmitted."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
REVIEW_PATH = ROOT / "config" / "pdf-parser-candidate-review.json"
WORKER_CONTRACT_PATH = ROOT / "config" / "restricted-parser-worker-contract.json"
DOCUMENT_POLICY_PATH = ROOT / "config" / "document-context-policy.json"


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0].lower())
    return roots


def main() -> int:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    worker = json.loads(WORKER_CONTRACT_PATH.read_text(encoding="utf-8"))
    document = json.loads(DOCUMENT_POLICY_PATH.read_text(encoding="utf-8"))
    checks: list[str] = []

    def require(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    require(review["schemaVersion"] == 1, "versioned review")
    require(review["status"] == "reviewed-candidate-not-admitted", "non-admitted status")
    require(review["reviewDate"] == "2026-07-30", "review date")
    preferred = review["preferredCandidate"]
    require(preferred["package"] == "pypdf", "preferred package identity")
    require(preferred["version"] == "6.14.2", "reviewed package version")
    require(bool(re.fullmatch(r"\d+\.\d+\.\d+", preferred["version"])), "version shape")
    require(preferred["license"] == "BSD-3-Clause", "license identity")
    require(preferred["pythonRequires"] == ">=3.9", "Python compatibility")
    require(preferred["distribution"] == {
        "purePython": True,
        "universalWheel": True,
        "nativeLibraries": False,
    }, "distribution facts")
    require(preferred["artifactSha256"] == "3f07891af76dc002657e04993ab9b4de81de29f9013b9761d0b7968bff12e946", "verified artifact digest")
    require((preferred["artifactVerified"], preferred["licenseDigestPinned"]) == (True, True), "artifact and license verified")
    for field in ("dependencyAdmitted", "importAllowed", "workerAllowed", "runtimeRouteAllowed", "uiAllowed"):
        require(preferred[field] is False, f"preferred candidate {field} denied")

    alternatives = {item["package"]: item for item in review["alternatives"]}
    require(set(alternatives) == {"PyMuPDF", "pdfminer.six"}, "bounded alternative set")
    require(all(item["status"] == "not-preferred-not-admitted" for item in alternatives.values()), "alternatives unadmitted")
    require("AGPL-3.0-or-commercial" in alternatives["PyMuPDF"]["reason"], "PyMuPDF license risk recorded")
    require("native" in alternatives["PyMuPDF"]["reason"].lower(), "PyMuPDF native packaging risk recorded")
    require("unsafe pickle" in alternatives["pdfminer.six"]["reason"].lower(), "pdfminer unsafe deserialization history recorded")
    require("GHSA-f83h-ghpp-7wcc" in " ".join(alternatives["pdfminer.six"]["sources"]), "pdfminer advisory recorded")

    sources = preferred["sources"] + [
        source
        for item in alternatives.values()
        for source in item["sources"]
    ]
    allowed_hosts = {"pypi.org", "github.com", "pypdf.readthedocs.io"}
    require(all(urlparse(source).scheme == "https" for source in sources), "HTTPS evidence sources")
    require(all(urlparse(source).hostname in allowed_hosts for source in sources), "evidence host allowlist")
    require(all(not urlparse(source).username and not urlparse(source).password for source in sources), "no source credentials")

    gates = set(review["requiredAdmissionGates"])
    required_gates = {
        "dependency-inventory-third-party-notices-and-sbom",
        "real-hostile-pdf-corpus",
        "reject-encryption-and-passwords",
        "reject-javascript-actions-launch-and-submit",
        "reject-embedded-and-associated-files",
        "reject-external-references",
        "bound-pages-objects-streams-output-and-recovery",
        "isolated-worker-no-network-no-child-processes",
        "worker-timeout-cancel-force-kill-and-no-residue",
        "source-versus-package-parity",
        "native-windows-linux-and-macos-package-smoke",
    }
    require(required_gates <= gates, "required future admission gates")
    require(len(gates) == len(review["requiredAdmissionGates"]), "unique admission gates")
    require(set(review["completedAdmissionPrerequisites"]) == {
        "download-exact-wheel-and-pin-sha256",
        "pin-license-text-digest",
    }, "completed artifact prerequisites")

    prohibitions = set(review["prohibitions"])
    require({
        "no-package-install",
        "no-parser-import",
        "no-document-open",
        "no-worker-start",
        "no-runtime-route",
        "no-ui-control",
        "no-filesystem-path",
        "no-temporary-file",
        "no-network",
        "no-ocr",
        "no-pdf-rendering",
    } == prohibitions, "exact current prohibitions")
    require(review["effects"] and all(value is False for value in review["effects"].values()), "all review effects denied")

    require(worker["parserDependenciesAdmitted"] == [], "worker dependency allowlist empty")
    require(worker["workerProcessAllowed"] is False, "worker process denied")
    require(worker["runtimeRouteAllowed"] is False, "worker runtime route denied")
    require(all(value is False for value in worker["effects"].values()), "all worker effects denied")
    require(document["formats"]["pdfAllowed"] is False, "document policy blocks PDF")

    parser_packages = {"pypdf", "fitz", "pymupdf", "pdfminer"}
    runtime_python = sorted((ROOT / "web").rglob("*.py"))
    require(bool(runtime_python), "runtime Python files discovered")
    require(all(imported_roots(path).isdisjoint(parser_packages) for path in runtime_python), "runtime imports no reviewed parser")

    serialized = REVIEW_PATH.read_text(encoding="utf-8").lower()
    require("192.168." not in serialized and "localhost" not in serialized, "no local environment disclosure")
    user_home_fragment = "/" + "users/"
    require(not re.search(r"[a-z]:\\\\|/home/", serialized) and user_home_fragment not in serialized, "no filesystem path disclosure")

    print(f"PDF parser candidate review passed {len(checks)} fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
