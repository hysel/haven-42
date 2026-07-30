#!/usr/bin/env python3
"""Verify and materialize the inert hostile PDF review corpus."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GENERATOR_PATH = ROOT / "scripts" / "create-pdf-parser-review-fixtures.py"
CORPUS_PATH = ROOT / "config" / "pdf-parser-hostile-corpus.json"
DOCUMENT_POLICY_PATH = ROOT / "config" / "document-context-policy.json"
WORKER_PATH = ROOT / "config" / "restricted-parser-worker-contract.json"
SPEC = importlib.util.spec_from_file_location("pdf_parser_review_fixtures", GENERATOR_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


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
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    document = json.loads(DOCUMENT_POLICY_PATH.read_text(encoding="utf-8"))
    worker = json.loads(WORKER_PATH.read_text(encoding="utf-8"))
    cases = MODULE.build_cases()
    generated_manifest = MODULE.manifest(cases)
    checks: list[str] = []

    def require(condition: bool, label: str) -> None:
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    require(corpus["schemaVersion"] == 1, "versioned corpus")
    require(corpus["status"] == "synthetic-inert-no-parser-executed", "inert corpus status")
    require(corpus["generator"] == "scripts/create-pdf-parser-review-fixtures.py", "fixed generator")
    require(corpus["runtimeAdmissionGranted"] is False, "runtime admission denied")
    require(corpus["parserImported"] is False, "parser import denied")
    require(corpus["documentOpenedByHaven"] is False, "document open denied")
    require(len(corpus["cases"]) == len(cases) == 14, "bounded case count")
    require(corpus["cases"] == generated_manifest, "manifest and deterministic bytes match")
    require(MODULE.manifest(MODULE.build_cases()) == generated_manifest, "repeat generation deterministic")

    filenames = [item["filename"] for item in corpus["cases"]]
    require(filenames == sorted(filenames), "stable filename order")
    require(len(filenames) == len(set(filenames)), "unique filenames")
    require(all("/" not in name and "\\" not in name and name.endswith(".pdf") for name in filenames), "flat PDF filenames")
    require(sum(item["category"] == "control" for item in corpus["cases"]) == 1, "one safe control")
    require(sum(item["expected"].startswith("reject-") for item in corpus["cases"]) == 13, "thirteen hostile cases")
    require({
        "control",
        "encryption",
        "active-content",
        "embedded-content",
        "external-reference",
        "malformed-structure",
        "resource-abuse",
    } == {item["category"] for item in corpus["cases"]}, "required threat categories")

    for item in corpus["cases"]:
        data = cases[item["filename"]]["bytes"]
        require(data.startswith(b"%PDF-1.7"), f"{item['filename']} PDF header")
        require(len(data) == item["sizeBytes"] <= 2048, f"{item['filename']} bounded bytes")
        require(hashlib.sha256(data).hexdigest() == item["sha256"], f"{item['filename']} digest")
        decoded = data.decode("latin-1")
        require(all(marker in decoded for marker in item["markers"]), f"{item['filename']} markers")

    require(document["formats"]["pdfAllowed"] is False, "active document policy still rejects PDF")
    require(worker["parserDependenciesAdmitted"] == [], "worker dependency list empty")
    require(worker["workerProcessAllowed"] is False and worker["runtimeRouteAllowed"] is False, "worker and route denied")
    require(imported_roots(GENERATOR_PATH).isdisjoint({"pypdf", "fitz", "pymupdf", "pdfminer"}), "generator imports no PDF parser")
    require(imported_roots(GENERATOR_PATH).isdisjoint({"requests", "socket", "subprocess", "urllib"}), "generator imports no network or process API")

    MODULE.main()
    on_disk_manifest = json.loads((MODULE.OUTPUT / "MANIFEST.json").read_text(encoding="utf-8"))
    require(on_disk_manifest["cases"] == generated_manifest, "generated on-disk manifest")
    require(
        all((MODULE.OUTPUT / item["filename"]).read_bytes() == cases[item["filename"]]["bytes"] for item in corpus["cases"]),
        "generated on-disk fixture bytes",
    )

    print(f"PDF parser review fixture suite passed {len(checks)} checks and created {len(cases)} inert files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
