#!/usr/bin/env python3
"""Exercise review-only semantic extraction across six complex formats."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
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


GENERATOR = module(
    "semantic_fixture_generator",
    ROOT / "scripts/create-complex-document-semantic-fixtures.py",
)
REVIEWER = module(
    "complex_semantic_reviewer",
    ROOT / "scripts/review-complex-document-semantics.py",
)
SAFE = {
    "safe.docx": ("docx", "Word review text"),
    "safe.xlsx": ("xlsx", "Sheet review text"),
    "safe.pptx": ("pptx", "Slide review text"),
    "safe.odt": ("odt", "Writer review text"),
    "safe.ods": ("ods", "Calc review text"),
    "safe.odp": ("odp", "Impress review text"),
}
HOSTILE = {
    "formula.xlsx": ("xlsx", "formula-rejected"),
    "formula.ods": ("ods", "formula-rejected"),
    "segments.docx": ("docx", "text-segment-budget-exceeded"),
    "segments.odt": ("odt", "text-segment-budget-exceeded"),
    "parts.pptx": ("pptx", "selected-part-budget-exceeded"),
    "segments.odp": ("odp", "text-segment-budget-exceeded"),
    "tracked.docx": ("docx", "tracked-change-rejected"),
    "shared-index.xlsx": ("xlsx", "shared-string-index-invalid"),
}
RICH = {
    "rich.docx": (
        "docx",
        [
            ("paragraph-text", "Body text"),
            ("table-cell-text", "Table cell"),
            ("header-text", "Header text"),
            ("footer-text", "Footer text"),
            ("comment-text", "Review comment"),
        ],
    ),
    "rich.xlsx": (
        "xlsx",
        [
            ("shared-string", "Shared value"),
            ("literal-cell-value", "42"),
            ("inline-string", "Inline value"),
        ],
    ),
    "rich.pptx": (
        "pptx",
        [
            ("shape-text", "Slide body"),
            ("speaker-note-text", "Speaker note"),
        ],
    ),
}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    values: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            values.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            values.add(node.module.split(".", 1)[0])
    return values


def main() -> int:
    checks = 0
    first = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in GENERATOR.generate()
    }
    second = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in GENERATOR.generate()
    }
    assert first == second and len(first) == 17
    checks += 2
    for name, (format_id, expected) in SAFE.items():
        result = REVIEWER.extract((GENERATOR.OUTPUT / name).read_bytes(), format_id)
        assert result["status"] == "review-only-semantic-text"
        assert [value["text"] for value in result["segments"]] == [expected]
        assert result["runtimeAdmissionGranted"] is False
        assert result["providerPayloadAllowed"] is False
        checks += 4
    for name, (format_id, expected) in RICH.items():
        result = REVIEWER.extract((GENERATOR.OUTPUT / name).read_bytes(), format_id)
        assert [
            (value["kind"], value["text"]) for value in result["segments"]
        ] == expected
        assert len({value["source"] for value in result["segments"]}) == len(expected)
        assert result["runtimeAdmissionGranted"] is False
        checks += 3
    for name, (format_id, reason) in HOSTILE.items():
        try:
            REVIEWER.extract((GENERATOR.OUTPUT / name).read_bytes(), format_id)
        except REVIEWER.SemanticRejected as error:
            assert str(error) == reason, (name, str(error), reason)
            checks += 1
        else:
            raise AssertionError(f"{name} unexpectedly passed")
    contract = json.loads(
        (ROOT / "config/complex-document-semantic-review.json").read_text(
            encoding="utf-8"
        )
    )
    assert set(contract["formats"]) == {"docx", "xlsx", "pptx", "odt", "ods", "odp"}
    assert all(candidate["selected"] is False for candidate in contract["dependencyResearch"])
    assert contract["policy"]["containerInspectionMustPassFirst"] is True
    assert contract["policy"]["formulasAllowed"] is False
    assert contract["policy"]["commentsExtracted"] is True
    assert contract["policy"]["trackedChangesRejected"] is True
    assert contract["policy"]["archiveExtractionAllowed"] is False
    assert not any(contract["authority"].values())
    checks += 8
    reviewer = ROOT / "scripts/review-complex-document-semantics.py"
    generator = ROOT / "scripts/create-complex-document-semantic-fixtures.py"
    assert imported_roots(reviewer).isdisjoint(
        {"socket", "subprocess", "requests", "urllib", "http", "lxml"}
    )
    assert imported_roots(generator).isdisjoint(
        {"socket", "subprocess", "requests", "urllib", "http"}
    )
    reviewer_text = reviewer.read_text(encoding="utf-8")
    assert ".extract(" not in reviewer_text and ".extractall(" not in reviewer_text
    checks += 3
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"}
    )
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    resources = (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8")
    assert "review-complex-document-semantics" not in runtime
    assert "review-complex-document-semantics" not in package + resources
    assert "complex-document-semantic-review" not in package + resources
    checks += 3
    print(
        f"Complex-document semantic review passed {checks} checks across 17 fixtures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
