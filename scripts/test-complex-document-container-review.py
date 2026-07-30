#!/usr/bin/env python3
"""Exercise synthetic Office/OpenDocument containers without runtime admission."""

from __future__ import annotations

import hashlib
import importlib.util
import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


GENERATOR = module("complex_fixture_generator", ROOT / "scripts/create-complex-document-review-fixtures.py")
INSPECTOR = module("complex_container_inspector", ROOT / "scripts/inspect-complex-document-container.py")
EXPECTED = {
    "traversal.docx": "unsafe-member-name",
    "duplicate.docx": "duplicate-member",
    "macro.docx": "macro-content",
    "external.docx": "external-relationship",
    "embedded.docx": "embedded-object",
    "activex.docx": "embedded-object",
    "symlink.docx": "symlink-member",
    "malformed-xml.docx": "malformed-xml",
    "encrypted.docx": "encrypted-container",
    "expansion.docx": "expansion-ratio-exceeded",
    "doctype.odt": "active-xml",
    "external.odt": "external-relationship",
    "embedded.odt": "embedded-object",
    "mimetype-confusion.odt": "format-identity-mismatch",
}


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
    checks = 0
    first = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in GENERATOR.generate()}
    second = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in GENERATOR.generate()}
    assert first == second and len(first) == 16
    checks += 2
    for name, format_id in (("safe.docx", "docx"), ("safe.odt", "odt")):
        result = INSPECTOR.inspect((GENERATOR.OUTPUT / name).read_bytes(), format_id)
        assert result["status"] == "candidate-safe-metadata"
        assert result["contentExtracted"] is False
        assert result["runtimeAdmissionGranted"] is False
        checks += 3
    for name, reason in EXPECTED.items():
        try:
            INSPECTOR.inspect((GENERATOR.OUTPUT / name).read_bytes(), name.rsplit(".", 1)[1])
        except INSPECTOR.ContainerRejected as error:
            assert str(error) == reason, (name, str(error), reason)
            checks += 1
        else:
            raise AssertionError(f"{name} was not rejected")
    contract = json.loads(
        (ROOT / "config/complex-document-container-review.json").read_text(encoding="utf-8")
    )
    assert not any(contract["authority"].values())
    assert not any(contract["effects"].values())
    assert not any(contract["policy"].values())
    assert set(contract["formats"]) == {"docx", "xlsx", "pptx", "odt", "ods", "odp"}
    checks += 4
    limits = contract["limits"]
    assert INSPECTOR.MAX_INPUT == limits["maximumInputBytes"]
    assert INSPECTOR.MAX_ENTRIES == limits["maximumEntries"]
    assert INSPECTOR.MAX_MEMBER == limits["maximumMemberBytes"]
    assert INSPECTOR.MAX_EXPANDED == limits["maximumExpandedBytes"]
    assert INSPECTOR.MAX_RATIO == limits["maximumExpansionRatio"]
    assert INSPECTOR.MAX_XML == limits["maximumXmlBytes"]
    checks += 6
    inspector_path = ROOT / "scripts/inspect-complex-document-container.py"
    generator_path = ROOT / "scripts/create-complex-document-review-fixtures.py"
    assert imported_roots(inspector_path).isdisjoint({"socket", "subprocess", "requests", "urllib", "http"})
    assert imported_roots(generator_path).isdisjoint({"socket", "subprocess", "requests", "urllib", "http"})
    checks += 2
    inspector_text = inspector_path.read_text(encoding="utf-8")
    assert ".extract(" not in inspector_text and ".extractall(" not in inspector_text
    assert "def inspect(data: bytes, format_id: str)" in inspector_text
    checks += 2
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"}
    )
    assert "inspect-complex-document-container" not in runtime_text
    checks += 1
    package_text = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    resources = (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8")
    assert "inspect-complex-document-container" not in package_text + resources
    assert "complex-document-container-review" not in package_text + resources
    checks += 2
    foundation = json.loads(
        (ROOT / "config/restricted-parser-worker-contract.json").read_text(encoding="utf-8")
    )
    assert all(foundation["candidateFormats"][key] == value for key, value in contract["formats"].items())
    assert foundation["parserDependenciesAdmitted"] == [] and foundation["workerProcessAllowed"] is False
    checks += 2
    print(f"Complex-document container review passed {checks} deterministic security checks across 16 fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
