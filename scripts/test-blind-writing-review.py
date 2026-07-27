#!/usr/bin/env python3
"""Offline hostile and rendering tests for the blind writing review harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "blind_writing_review",
    ROOT / "scripts/run-blind-writing-review.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def expect_rejected(value: str) -> None:
    try:
        MODULE.validate_output_directory(value)
    except ValueError:
        return
    raise AssertionError(f"unsafe output path accepted: {value}")


def main() -> int:
    expect_rejected(str(ROOT / "review-output"))
    with tempfile.TemporaryDirectory(prefix="haven42-blind-review-test-") as temporary:
        output = MODULE.validate_output_directory(str(Path(temporary) / "review"))
        assert output.is_dir()
        (output / "blind-review-packet.md").write_text("occupied", encoding="utf-8")
        expect_rejected(str(output))

    cases = [{
        "title": "Synthetic",
        "prompt": "Synthetic prompt",
        "reviewFocus": ("fidelity", "tone"),
        "candidates": [
            {"alias": "A", "output": "First output"},
            {"alias": "B", "output": "Second output"},
        ],
    }]
    rendered = MODULE.render_packet(cases, "2026-07-25T00:00:00Z")
    assert "Candidate A" in rendered
    assert "Candidate B" in rendered
    assert "fidelity=__" in rendered
    assert "Overall rank, best to worst (A, B): __" in rendered
    assert "model" not in rendered.casefold()
    second = MODULE.render_packet(
        [{
            "title": item["title"],
            "prompt": item["prompt"],
            "reviewFocus": item["reviewFocus"],
            "candidates": [
                {"alias": "A", "output": "First output"},
                {"alias": "B", "output": "Second output"},
            ],
        } for item in MODULE.CASE_SETS["second"]],
        "2026-07-27T00:00:00Z",
        "second",
    )
    assert "Prompt-set revision: second" in second
    assert "Long-form continuity and section coherence" in second
    assert "Distractor-resistant source summary" in second
    assert "Constrained fact-preserving edit" in second
    assert "model" not in second.casefold()
    print("Blind writing review harness passed 12 offline safety checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
