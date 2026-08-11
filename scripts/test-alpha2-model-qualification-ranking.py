#!/usr/bin/env python3
"""Offline hostile checks for owner-review qualification rankings."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha2_model_qualification_ranking",
    ROOT / "scripts/alpha2-model-qualification-ranking.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.RankingError as error:
        assert str(error) == code, str(error)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> None:
    inventory = MODULE._load(MODULE.INVENTORY_PATH, "bad")
    matrix = MODULE._load(MODULE.MATRIX_PATH, "bad")
    result = {
        "modelId": "candidate-b",
        "profileId": "cuda-16gib",
        "platformFamily": "linux",
        "operatingSystemId": "test-linux",
        "status": "passed",
        "tasks": {},
        "soak": {"outcome": "passed", "averageTokensPerSecond": 25.0},
    }
    for index, capability in enumerate(MODULE.CAPABILITIES):
        result["tasks"][capability] = {
            "outcome": "passed",
            "errorCode": None,
            "metrics": {
                "samplesPassed": 3,
                "unloadPasses": 3,
                "outputTokens": 12,
                "peakGpuMemoryBytes": 1,
                "tokensPerSecond": 20.0 + index,
            },
        }
    result_a = json.loads(json.dumps(result))
    result_a["modelId"] = "candidate-a"
    result_a["tasks"]["general.chat"]["metrics"]["tokensPerSecond"] = 30.0
    summary = {
        "schemaVersion": 1,
        "kind": "alpha2-model-qualification-summary",
        "qualificationInventoryCanonicalSha256": MODULE._canonical_sha256(inventory),
        "qualificationMatrixCanonicalSha256": MODULE._canonical_sha256(matrix),
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "automaticSelectionEvidenceAllowed": False,
        "automaticDefaultChangeAllowed": False,
        "results": [result, result_a],
    }
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "summary.json"
        path.write_text(json.dumps(summary), encoding="utf-8")
        ranking = MODULE.build_ranking(path)
        assert ranking["automaticSelectionAllowed"] is False
        assert ranking["ownerApprovalRequired"] is True
        assert all(
            item["platformFamily"] == "linux" for item in ranking["rankings"]
        )
        chat = next(
            item for item in ranking["rankings"] if item["capability"] == "general.chat"
        )
        assert [item["modelId"] for item in chat["candidates"]] == [
            "candidate-a",
            "candidate-b",
        ]
        summary["containsRawPromptsOrResponses"] = True
        path.write_text(json.dumps(summary), encoding="utf-8")
        refused(lambda: MODULE.build_ranking(path), "invalid-qualification-summary")
        summary["containsRawPromptsOrResponses"] = False
        result["platformFamily"] = "macos"
        path.write_text(json.dumps(summary), encoding="utf-8")
        refused(lambda: MODULE.build_ranking(path), "invalid-qualification-summary")
        result["platformFamily"] = "linux"
        historical_inventory = json.loads(json.dumps(inventory))
        historical_inventory["reviewedAtUtc"] = "2026-08-08T00:00:00Z"
        historical_inventory_path = Path(temporary) / "inventory.json"
        historical_inventory_path.write_text(
            json.dumps(historical_inventory), encoding="utf-8"
        )
        historical_matrix = json.loads(json.dumps(matrix))
        historical_matrix["inventoryBinding"]["canonicalSha256"] = (
            MODULE._canonical_sha256(historical_inventory)
        )
        historical_matrix_path = Path(temporary) / "matrix.json"
        historical_matrix_path.write_text(
            json.dumps(historical_matrix), encoding="utf-8"
        )
        summary["qualificationInventoryCanonicalSha256"] = (
            MODULE._canonical_sha256(historical_inventory)
        )
        summary["qualificationMatrixCanonicalSha256"] = MODULE._canonical_sha256(
            historical_matrix
        )
        path.write_text(json.dumps(summary), encoding="utf-8")
        historical_ranking = MODULE.build_ranking(
            path, historical_inventory_path, historical_matrix_path
        )
        assert historical_ranking["rankings"]
        refused(
            lambda: MODULE.build_ranking(
                path, historical_inventory_path, MODULE.MATRIX_PATH
            ),
            "stale-qualification-matrix",
        )
    source = (ROOT / "scripts/alpha2-model-qualification-ranking.py").read_text(
        encoding="utf-8"
    )
    assert "subprocess" not in source and "urllib" not in source
    assert '.get("response")' not in source and '["response"]' not in source
    print("Alpha 2 qualification ranking passed hostile offline checks.")


if __name__ == "__main__":
    main()
