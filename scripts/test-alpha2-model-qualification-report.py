#!/usr/bin/env python3
"""Offline hostile checks for the qualification summary generator."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha2_model_qualification_report",
    ROOT / "scripts/alpha2-model-qualification-report.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.ReportError as error:
        assert str(error) == code, str(error)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> None:
    cells, inventory_sha, matrix_sha = MODULE._reviewed_cells()
    context, _, _ = MODULE._reviewed_context()
    assert ("gemma3-4b-q4", "cpu-16gib") in cells
    assert ("qwen36-27b-q4", "cuda-32gib-system-16gib") in cells
    assert ("qwen36-35b-a3b-q4", "cuda-32gib-system-16gib") not in cells
    assert ("minicpm-v46-1b-q4", "vulkan-8gib-system-16gib") in cells
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        base = root / "evidence"
        base.mkdir()
        common = {
            "qualificationInventoryCanonicalSha256": inventory_sha,
            "qualificationMatrixCanonicalSha256": matrix_sha,
            "modelId": "gemma3-4b-q4",
            "manifestDigest": context[("gemma3-4b-q4", "cpu-16gib")][
                "manifestDigest"
            ],
            "profileId": "cpu-16gib",
            "platformFamily": "linux",
            "operatingSystemId": "test-linux",
            "backendMode": "cpu",
            "provider": "ollama",
            "providerVersion": context[("gemma3-4b-q4", "cpu-16gib")][
                "providerVersion"
            ],
            "systemMemoryGiB": 16,
            "usableGpuMemoryGiB": 0,
            "automaticPromotionAllowed": False,
        }
        for index, capability in enumerate(MODULE.CAPABILITIES):
            record = {
                "kind": "alpha2-model-task-qualification-evidence",
                "outcome": "passed",
                "errorCode": None,
                "containsRawPromptsOrResponses": False,
                "containsPrivateMachineIdentity": False,
                "metrics": {
                    "samplesPassed": 3,
                    "unloadPasses": 3,
                    "outputTokens": 12,
                    "tokensPerSecond": 18.5 + index,
                    "peakGpuMemoryBytes": 0,
                },
                "evidence": {
                    **common,
                    "capability": capability,
                    "check": context[("gemma3-4b-q4", "cpu-16gib")]["checks"][
                        capability
                    ],
                },
            }
            (base / f"task-{index}.json").write_text(json.dumps(record), encoding="utf-8")
        soak = {
            "kind": "alpha2-linux-model-soak-evidence",
            "outcome": "passed",
            "errorCode": None,
            "durationSeconds": 1800,
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "metrics": {
                "cellsPassed": 13,
                "samplesPassed": 39,
                "unloadPasses": 39,
                "outputTokens": 120,
                "averageTokensPerSecond": 20,
                "peakGpuMemoryBytes": 0,
                "capabilityCells": {
                    "general.chat": 5,
                    "content.write": 4,
                    "content.summarize": 4,
                },
            },
            "evidence": {
                **{key: value for key, value in common.items() if key != "qualificationMatrixCanonicalSha256"},
                "qualificationProfileId": "cpu-16gib",
                "qualificationOnly": True,
            },
        }
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        report = MODULE.build_report(base)
        assert report["results"][0]["status"] == "passed"
        assert report["results"][0]["tasks"]["general.chat"]["metrics"] == {
            "samplesPassed": 3,
            "unloadPasses": 3,
            "outputTokens": 12,
            "peakGpuMemoryBytes": 0,
            "tokensPerSecond": 18.5,
        }
        assert report["automaticDefaultChangeAllowed"] is False
        assert report["results"][0]["platformFamily"] == "linux"
        assert "test-linux" in str(report)
        soak_base = root / "soaks"
        soak_base.mkdir()
        (base / "soak.json").replace(soak_base / "soak.json")
        separated_roots = MODULE.build_report([base, soak_base])
        assert separated_roots["results"][0]["status"] == "passed"
        (soak_base / "soak.json").replace(base / "soak.json")
        refused(
            lambda: MODULE.build_report([base, base]),
            "overlapping-evidence-directories",
        )
        nested = base / "nested"
        nested.mkdir()
        refused(
            lambda: MODULE.build_report([base, nested]),
            "overlapping-evidence-directories",
        )
        task_with_bom = (base / "task-0.json").read_text(encoding="utf-8")
        (base / "task-0.json").write_text(task_with_bom, encoding="utf-8-sig")
        assert MODULE.build_report(base)["results"][0]["status"] == "passed"
        (base / "task-0.json").write_text(task_with_bom, encoding="utf-8")
        soak["evidence"]["platformFamily"] = "windows"
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        refused(
            lambda: MODULE.build_report(base), "unreviewed-qualification-evidence"
        )
        soak["kind"] = "alpha2-windows-model-soak-evidence"
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        separated = MODULE.build_report(base)
        assert len(separated["results"]) == 2
        assert {item["platformFamily"] for item in separated["results"]} == {
            "linux",
            "windows",
        }
        assert all(item["status"] == "incomplete" for item in separated["results"])
        soak["kind"] = "alpha2-linux-model-soak-evidence"
        soak["evidence"]["platformFamily"] = "linux"
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        task = json.loads((base / "task-0.json").read_text(encoding="utf-8"))
        del task["evidence"]["platformFamily"]
        task["evidence"]["operatingSystemId"] = "windows-11-x64"
        (base / "task-0.json").write_text(json.dumps(task), encoding="utf-8")
        refused(
            lambda: MODULE.build_report(base), "unreviewed-qualification-evidence"
        )
        task["evidence"]["platformFamily"] = "linux"
        task["evidence"]["operatingSystemId"] = "test-linux"
        (base / "task-0.json").write_text(json.dumps(task), encoding="utf-8")
        task = json.loads((base / "task-0.json").read_text(encoding="utf-8"))
        task["containsRawPromptsOrResponses"] = True
        (base / "task-0.json").write_text(json.dumps(task), encoding="utf-8")
        refused(lambda: MODULE.build_report(base), "unsafe-qualification-evidence")
        task["containsRawPromptsOrResponses"] = False
        task["metrics"]["unloadPasses"] = 2
        (base / "task-0.json").write_text(json.dumps(task), encoding="utf-8")
        refused(
            lambda: MODULE.build_report(base),
            "invalid-task-qualification-evidence",
        )
        task["metrics"]["unloadPasses"] = 3
        (base / "task-0.json").write_text(json.dumps(task), encoding="utf-8")
        soak["metrics"]["samplesPassed"] = 0
        soak["metrics"]["unloadPasses"] = 0
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        refused(lambda: MODULE.build_report(base), "invalid-soak-evidence")
        soak["metrics"]["samplesPassed"] = 39
        soak["metrics"]["unloadPasses"] = 39
        soak["metrics"]["averageTokensPerSecond"] = float("nan")
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        refused(lambda: MODULE.build_report(base), "invalid-soak-evidence")
        soak["metrics"]["averageTokensPerSecond"] = 20
        (base / "soak.json").write_text(json.dumps(soak), encoding="utf-8")
        task["evidence"]["providerVersion"] = "0.32.6"
        (base / "task-0.json").write_text(json.dumps(task), encoding="utf-8")
        refused(
            lambda: MODULE.build_report(base), "invalid-qualification-binding"
        )
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        historical_inventory = json.loads(
            MODULE.INVENTORY_PATH.read_text(encoding="utf-8")
        )
        historical_inventory["reviewedAtUtc"] = "2026-08-08T00:00:00Z"
        historical_inventory_path = base / "inventory.json"
        historical_inventory_path.write_text(
            json.dumps(historical_inventory), encoding="utf-8"
        )
        historical_matrix = json.loads(MODULE.MATRIX_PATH.read_text(encoding="utf-8"))
        historical_matrix["inventoryBinding"]["canonicalSha256"] = (
            MODULE._canonical_sha256(historical_inventory)
        )
        historical_matrix_path = base / "matrix.json"
        historical_matrix_path.write_text(
            json.dumps(historical_matrix), encoding="utf-8"
        )
        historical_cells, historical_inventory_sha, historical_matrix_sha = (
            MODULE._reviewed_cells(historical_inventory_path, historical_matrix_path)
        )
        assert historical_cells == cells
        assert historical_inventory_sha != inventory_sha
        assert historical_matrix_sha != matrix_sha
        refused(
            lambda: MODULE._reviewed_cells(
                historical_inventory_path, MODULE.MATRIX_PATH
            ),
            "stale-qualification-matrix",
        )
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        expected = context[(
            "minicpm-v46-1b-q4", "vulkan-8gib-system-16gib"
        )]
        common_extended = {
            "schemaVersion": 1,
            "kind": "haven42-alpha2-extended-model-qualification",
            "modelId": "minicpm-v46-1b-q4",
            "outcome": "passed",
            "platformFamily": "linux",
            "operatingSystemId": "test-rx-linux",
            "backend": "vulkan",
            "profileId": "vulkan-8gib-system-16gib",
            "provider": "ollama",
            "providerVersion": expected["providerVersion"],
            "manifestDigest": expected["manifestDigest"],
            "systemMemoryGiB": 32,
            "usableGpuMemoryGiB": 8,
            "inventorySha256": inventory_sha,
            "matrixSha256": matrix_sha,
            "peakObservedGpuResidencyBytes": 1024,
            "durationMilliseconds": 1000,
            "rawPromptRecorded": False,
            "rawResponseRecorded": False,
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "automaticPromotionAllowed": False,
        }
        vision = {
            **common_extended,
            "capability": "vision",
            "details": {"syntheticImages": 2, "groundedAnswers": 2},
        }
        recovery = {
            **common_extended,
            "capability": "failure-recovery",
            "details": {
                "timeoutObserved": True,
                "postTimeoutRequestPassed": True,
            },
        }
        (base / "vision.json").write_text(json.dumps(vision), encoding="utf-8")
        (base / "recovery.json").write_text(
            json.dumps(recovery), encoding="utf-8"
        )
        extended_report = MODULE.build_report(base)
        result = extended_report["results"][0]
        assert result["status"] == "incomplete"
        assert result["extendedStatus"] == "passed"
        assert result["extendedCapabilities"]["vision"]["metrics"][
            "groundedAnswers"
        ] == 2
        vision["containsRawPromptsOrResponses"] = True
        (base / "vision.json").write_text(json.dumps(vision), encoding="utf-8")
        refused(
            lambda: MODULE.build_report(base),
            "invalid-extended-qualification-evidence",
        )
    source = (ROOT / "scripts/alpha2-model-qualification-report.py").read_text(encoding="utf-8")
    assert '.get("response")' not in source and '["response"]' not in source
    print("Alpha 2 model qualification report passed hostile offline checks.")


if __name__ == "__main__":
    main()
