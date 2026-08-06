#!/usr/bin/env python3
"""Contract and hostile tests for the response-compliance runner."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "run-windows-alpha-response-compliance.py"
SPEC = importlib.util.spec_from_file_location("response_compliance", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> int:
    plan = MODULE.build_plan()
    assert plan["kind"] == "windows-alpha-response-compliance-plan"
    assert plan["cellCount"] == 30 and len(plan["cells"]) == 30
    assert plan["models"] == [{
        "model": "qwen3.5:9b",
        "modelDigest": "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
    }]
    assert {cell["capabilityId"] for cell in plan["cells"]} == {
        "general.chat", "content.write", "content.summarize",
    }
    assert all(cell["prompt"] and cell["expectedBehavior"] and cell["forbiddenBehavior"] for cell in plan["cells"])
    source = PATH.read_text(encoding="utf-8")
    assert "installed = dict(state.model_digests)" in source
    assert 'item.get("digest", "")' not in source
    checks = 8

    candidate = MODULE.build_plan(
        "gemma3:12b",
        "f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a",
        ("general.chat", "content.write"),
        ("unknown-individual-reference", "secret-repetition"),
    )
    assert candidate["candidateOnly"] is True and candidate["cellCount"] == 4
    assert {cell["capabilityId"] for cell in candidate["cells"]} == {"general.chat", "content.write"}
    assert {cell["caseId"] for cell in candidate["cells"]} == {
        "unknown-individual-reference", "secret-repetition",
    }
    try:
        MODULE.build_plan("bad model", "0" * 64, ("general.chat",), ("secret-repetition",))
        raise AssertionError("invalid candidate model accepted")
    except ValueError as error:
        assert str(error) == "invalid-candidate-compliance-plan"
    checks += 4

    for hostile in ("../escape", "two/levels", "UPPER", "", "x" * 81):
        try:
            MODULE._output_directory(hostile)
            raise AssertionError(f"unsafe output accepted: {hostile!r}")
        except ValueError:
            checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-compliance-contract-") as raw:
        matrix = json.loads(MODULE.MATRIX_PATH.read_text(encoding="utf-8"))
        matrix["cases"][0]["prompt"] = "x" * 1001
        hostile_matrix = Path(raw) / "matrix.json"
        hostile_matrix.write_text(json.dumps(matrix), encoding="utf-8")
        with patch.object(MODULE, "MATRIX_PATH", hostile_matrix):
            try:
                MODULE.build_plan()
                raise AssertionError("oversized prompt accepted")
            except ValueError as error:
                assert str(error) == "invalid-compliance-case"
        checks += 1

    print(f"Windows Alpha response compliance runner tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
