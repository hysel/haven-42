#!/usr/bin/env python3
"""Routing checks for multi-snapshot qualification reporting."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "alpha2-multi-snapshot-qualification-report.py"
SPEC = importlib.util.spec_from_file_location("multi_snapshot_report", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MultiSnapshotReportTests(unittest.TestCase):
    def test_routes_exact_inventory_and_matrix_pair(self) -> None:
        mapping = json.loads((
            ROOT / "config/alpha-2-qualification-campaign-snapshots.json"
        ).read_text(encoding="utf-8"))
        current = mapping["snapshots"][-1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            root.mkdir()
            (root / "task.json").write_text(json.dumps({
                "kind": "alpha2-model-task-qualification-evidence",
                "evidence": {
                    "qualificationInventoryCanonicalSha256": current[
                        "inventoryCanonicalSha256"
                    ],
                    "qualificationMatrixCanonicalSha256": current[
                        "matrixCanonicalSha256"
                    ],
                },
            }), encoding="utf-8")
            fake = {"results": [{
                "modelId": "x",
                "profileId": "p",
                "platformFamily": "linux",
                "operatingSystemId": "os",
            }]}
            with patch.object(MODULE.REPORT, "build_report", return_value=fake):
                result = MODULE.build_multi_report([root])
            self.assertEqual(
                result["results"][0]["metadataSnapshotId"], "campaign-current"
            )
            self.assertFalse(result["automaticDefaultChangeAllowed"])

    def test_unknown_pair_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "task.json").write_text(json.dumps({
                "kind": "alpha2-model-task-qualification-evidence",
                "evidence": {
                    "qualificationInventoryCanonicalSha256": "0" * 64,
                    "qualificationMatrixCanonicalSha256": "1" * 64,
                },
            }), encoding="utf-8")
            with self.assertRaisesRegex(
                MODULE.MultiSnapshotError, "unknown-evidence-snapshot"
            ):
                MODULE.build_multi_report([root])

    def test_routes_and_validates_full_residency_evidence(self) -> None:
        mapping = json.loads((
            ROOT / "config/alpha-2-qualification-campaign-snapshots.json"
        ).read_text(encoding="utf-8"))
        current = mapping["snapshots"][-1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "task.json").write_text(json.dumps({
                "kind": "alpha2-model-task-qualification-evidence",
                "evidence": {
                    "qualificationInventoryCanonicalSha256": current["inventoryCanonicalSha256"],
                    "qualificationMatrixCanonicalSha256": current["matrixCanonicalSha256"],
                },
            }), encoding="utf-8")
            (root / "residency.json").write_text(json.dumps({
                "kind": MODULE.RESIDENCY_KIND,
                "outcome": "passed",
                "containsPrivateMachineIdentity": False,
                "containsRawPromptsOrResponses": False,
                "evidence": {
                    "qualificationInventoryCanonicalSha256": current["inventoryCanonicalSha256"],
                    "modelId": "model-one",
                    "operatingSystemId": "ubuntu-test",
                    "backendMode": "vulkan",
                    "hardwareProfileId": "amd-test",
                    "automaticPromotionAllowed": False,
                    "fullGpuResidencyObserved": True,
                    "reportedModelBytes": 100,
                    "reportedGpuResidentBytes": 100,
                    "manifestDigest": "a" * 64,
                    "providerVersion": "0.32.13",
                },
            }), encoding="utf-8")
            fake = {"results": [{
                "modelId": "x", "profileId": "p", "platformFamily": "linux",
                "operatingSystemId": "os",
            }]}
            with patch.object(MODULE.REPORT, "build_report", return_value=fake):
                result = MODULE.build_multi_report([root])
            residency = result["fullGpuResidencyResults"][0]
            self.assertEqual(residency["metadataSnapshotId"], "campaign-current")
            self.assertTrue(residency["fullGpuResidencyObserved"])

    def test_partial_residency_cannot_be_reported_as_passed(self) -> None:
        mapping = json.loads((
            ROOT / "config/alpha-2-qualification-campaign-snapshots.json"
        ).read_text(encoding="utf-8"))
        current = mapping["snapshots"][-1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "task.json").write_text(json.dumps({
                "kind": "alpha2-model-task-qualification-evidence",
                "evidence": {
                    "qualificationInventoryCanonicalSha256": current["inventoryCanonicalSha256"],
                    "qualificationMatrixCanonicalSha256": current["matrixCanonicalSha256"],
                },
            }), encoding="utf-8")
            (root / "residency.json").write_text(json.dumps({
                "kind": MODULE.RESIDENCY_KIND,
                "outcome": "passed",
                "containsPrivateMachineIdentity": False,
                "containsRawPromptsOrResponses": False,
                "evidence": {
                    "qualificationInventoryCanonicalSha256": current["inventoryCanonicalSha256"],
                    "modelId": "model-one", "operatingSystemId": "ubuntu-test",
                    "backendMode": "vulkan", "hardwareProfileId": "amd-test",
                    "automaticPromotionAllowed": False,
                    "fullGpuResidencyObserved": True,
                    "reportedModelBytes": 100, "reportedGpuResidentBytes": 99,
                },
            }), encoding="utf-8")
            fake = {"results": [{
                "modelId": "x", "profileId": "p", "platformFamily": "linux",
                "operatingSystemId": "os",
            }]}
            with patch.object(MODULE.REPORT, "build_report", return_value=fake):
                result = MODULE.build_multi_report([root])
            self.assertEqual(result["fullGpuResidencyResults"][0]["outcome"], "failed")


if __name__ == "__main__":
    unittest.main()
