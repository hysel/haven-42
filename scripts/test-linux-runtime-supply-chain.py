#!/usr/bin/env python3
"""Offline hostile tests for the Linux runtime supply-chain review."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_linux_runtime_supply_chain",
    ROOT / "scripts" / "audit-linux-runtime-supply-chain.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.SupplyChainError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"Expected {code}")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    checks = 0
    review = MODULE.validate_review()
    assert review["managedRuntimeChangeApproved"] is False
    assert review["automaticDefaultChangeAllowed"] is False
    assert all(
        artifact["managedInstallationAllowed"] is False
        for artifact in review["runtime"]["artifacts"]
    )
    checks += 3

    model_review = MODULE.validate_model_review()
    assert model_review["selectionPolicyChangeAllowed"] is False
    assert model_review["automaticDefaultChangeAllowed"] is False
    assert len(model_review["models"]) == 6
    checks += 3

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source_review = json.loads(MODULE.REVIEW_PATH.read_text(encoding="utf-8"))
        source_compatibility = json.loads(
            MODULE.COMPATIBILITY_PATH.read_text(encoding="utf-8")
        )
        source_model_review = json.loads(
            MODULE.MODEL_REVIEW_PATH.read_text(encoding="utf-8")
        )

        hostile_cases = []
        candidate = copy.deepcopy(source_review)
        candidate["managedRuntimeChangeApproved"] = True
        hostile_cases.append((candidate, source_compatibility, "invalid-linux-runtime-artifact-review"))

        candidate = copy.deepcopy(source_review)
        candidate["runtime"]["artifacts"][0]["sha256"] = "0" * 64
        hostile_cases.append((candidate, source_compatibility, "runtime-review-artifact-mismatch"))

        candidate = copy.deepcopy(source_review)
        candidate["runtime"]["artifacts"][1]["managedInstallationAllowed"] = True
        hostile_cases.append((candidate, source_compatibility, "invalid-reviewed-artifact"))

        candidate = copy.deepcopy(source_review)
        candidate["runtime"]["artifacts"][1]["requiredExecutableRelativePath"] = "bin/ollama"
        hostile_cases.append((candidate, source_compatibility, "invalid-reviewed-artifact-role"))

        candidate = copy.deepcopy(source_review)
        candidate["runtime"]["license"]["embeddedInReleaseArchives"] = True
        hostile_cases.append((candidate, source_compatibility, "invalid-runtime-license-record"))

        candidate_compatibility = copy.deepcopy(source_compatibility)
        candidate_compatibility["runtimes"][1]["admissionState"] = "admitted"
        hostile_cases.append((source_review, candidate_compatibility, "runtime-review-compatibility-mismatch"))

        for index, (candidate_review, candidate_compatibility, code) in enumerate(hostile_cases):
            review_path = root / f"review-{index}.json"
            compatibility_path = root / f"compatibility-{index}.json"
            write_json(review_path, candidate_review)
            write_json(compatibility_path, candidate_compatibility)
            refused(
                lambda rp=review_path, cp=compatibility_path: MODULE.validate_review(
                    rp, cp, ROOT
                ),
                code,
            )
            checks += 1

        model_catalog_path = ROOT / "config" / "alpha-2-model-catalog.json"
        candidate_model_review = copy.deepcopy(source_model_review)
        candidate_model_review["models"][0]["layers"][1]["sha256"] = "0" * 64
        candidate_model_review_path = root / "model-review.json"
        write_json(candidate_model_review_path, candidate_model_review)
        refused(
            lambda: MODULE.validate_model_review(
                candidate_model_review_path, model_catalog_path
            ),
            "model-layer-catalog-mismatch",
        )
        checks += 1

        candidate_model_review = copy.deepcopy(source_model_review)
        candidate_model_review["automaticDefaultChangeAllowed"] = True
        write_json(candidate_model_review_path, candidate_model_review)
        refused(
            lambda: MODULE.validate_model_review(
                candidate_model_review_path, model_catalog_path
            ),
            "invalid-linux-model-artifact-review",
        )
        checks += 1

    refused(
        lambda: MODULE.audit_archives(review, {"core": Path("missing")}),
        "incomplete-runtime-archive-set",
    )
    checks += 1
    print(f"Linux runtime supply-chain review passed {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
