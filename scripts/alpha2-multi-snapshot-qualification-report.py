#!/usr/bin/env python3
"""Merge qualification evidence across exact, hash-bound metadata generations."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MAX_FILES = 2048
MAX_BYTES = 2 * 1024 * 1024
RECOGNIZED = {
    "alpha2-model-task-qualification-evidence",
    "alpha2-linux-model-soak-evidence",
    "alpha2-windows-model-soak-evidence",
    "haven42-alpha2-extended-model-qualification",
}
RESIDENCY_KIND = "alpha2-ollama-full-gpu-residency-evidence"


def _module(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot-load-{name}")
    value = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(value)
    return value


REPORT = _module(
    "alpha2_model_qualification_report_for_multi_snapshot",
    ROOT / "scripts/alpha2-model-qualification-report.py",
)
SNAPSHOTS = _module(
    "alpha2_campaign_snapshots_for_multi_snapshot",
    ROOT / "scripts/materialize-alpha2-qualification-snapshots.py",
)


class MultiSnapshotError(ValueError):
    """Evidence could not be bound to exactly one reviewed snapshot."""


def _load(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise MultiSnapshotError("unsafe-evidence-file")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MultiSnapshotError("invalid-evidence-file") from error
    if not isinstance(value, dict):
        raise MultiSnapshotError("invalid-evidence-file")
    return value


def _binding(record: dict[str, Any]) -> tuple[str, str | None]:
    kind = record.get("kind")
    if kind == "haven42-alpha2-extended-model-qualification":
        return record.get("inventorySha256"), record.get("matrixSha256")
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        raise MultiSnapshotError("missing-evidence-binding")
    return (
        evidence.get("qualificationInventoryCanonicalSha256"),
        evidence.get("qualificationMatrixCanonicalSha256"),
    )


def build_multi_report(evidence_roots: list[Path]) -> dict[str, Any]:
    if not evidence_roots:
        raise MultiSnapshotError("missing-evidence-root")
    roots: list[Path] = []
    for root in evidence_roots:
        if root.is_symlink():
            raise MultiSnapshotError("unsafe-evidence-root")
        try:
            resolved = root.resolve(strict=True)
        except OSError as error:
            raise MultiSnapshotError("unsafe-evidence-root") from error
        if not resolved.is_dir():
            raise MultiSnapshotError("unsafe-evidence-root")
        roots.append(resolved)
    files = [path for root in roots for path in root.rglob("*.json")]
    if len(files) > MAX_FILES:
        raise MultiSnapshotError("evidence-file-limit")
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        snapshot_root = work / "snapshots"
        snapshots = SNAPSHOTS.materialize(snapshot_root)
        by_pair = {
            (
                item["inventoryCanonicalSha256"],
                item["matrixCanonicalSha256"],
            ): item["id"]
            for item in snapshots
        }
        by_inventory: dict[str, list[str]] = {}
        for item in snapshots:
            by_inventory.setdefault(
                item["inventoryCanonicalSha256"], []
            ).append(item["id"])
        grouped: dict[str, list[Path]] = {}
        residency_results: list[dict[str, Any]] = []
        residency_keys: set[tuple[str, str, str, str]] = set()
        for path in sorted(files):
            record = _load(path)
            kind = record.get("kind")
            if kind not in RECOGNIZED and kind != RESIDENCY_KIND:
                continue
            inventory_sha, matrix_sha = _binding(record)
            if not isinstance(inventory_sha, str):
                raise MultiSnapshotError("missing-evidence-binding")
            if matrix_sha is None:
                matches = by_inventory.get(inventory_sha, [])
                if len(matches) != 1:
                    raise MultiSnapshotError("ambiguous-evidence-snapshot")
                snapshot_id = matches[0]
            else:
                snapshot_id = by_pair.get((inventory_sha, matrix_sha))
                if snapshot_id is None:
                    raise MultiSnapshotError("unknown-evidence-snapshot")
            if kind == RESIDENCY_KIND:
                evidence = record.get("evidence")
                if (
                    not isinstance(evidence, dict)
                    or record.get("containsPrivateMachineIdentity") is not False
                    or record.get("containsRawPromptsOrResponses") is not False
                    or not isinstance(evidence.get("modelId"), str)
                    or not isinstance(evidence.get("operatingSystemId"), str)
                    or not isinstance(evidence.get("backendMode"), str)
                    or not isinstance(evidence.get("hardwareProfileId"), str)
                    or evidence.get("automaticPromotionAllowed") is not False
                ):
                    raise MultiSnapshotError("invalid-residency-evidence")
                size = evidence.get("reportedModelBytes")
                size_vram = evidence.get("reportedGpuResidentBytes")
                passed = (
                    record.get("outcome") == "passed"
                    and evidence.get("fullGpuResidencyObserved") is True
                    and isinstance(size, int) and not isinstance(size, bool) and size > 0
                    and isinstance(size_vram, int) and not isinstance(size_vram, bool)
                    and size_vram == size
                )
                key = (
                    evidence["modelId"], evidence["operatingSystemId"],
                    evidence["hardwareProfileId"], snapshot_id,
                )
                if key in residency_keys:
                    raise MultiSnapshotError("duplicate-residency-result")
                residency_keys.add(key)
                residency_results.append({
                    "metadataSnapshotId": snapshot_id,
                    "modelId": evidence["modelId"],
                    "operatingSystemId": evidence["operatingSystemId"],
                    "backendMode": evidence["backendMode"],
                    "hardwareProfileId": evidence["hardwareProfileId"],
                    "outcome": "passed" if passed else "failed",
                    "fullGpuResidencyObserved": passed,
                    "reportedModelBytes": size,
                    "reportedGpuResidentBytes": size_vram,
                    "manifestDigest": evidence.get("manifestDigest"),
                    "providerVersion": evidence.get("providerVersion"),
                })
            else:
                grouped.setdefault(snapshot_id, []).append(path)
        if not grouped:
            raise MultiSnapshotError("no-qualification-evidence")
        merged: list[dict[str, Any]] = []
        keys: set[tuple[str, str, str, str, str]] = set()
        for snapshot_id, paths in grouped.items():
            group = work / "groups" / snapshot_id
            group.mkdir(parents=True)
            for index, path in enumerate(paths):
                shutil.copyfile(path, group / f"evidence-{index:04d}.json")
            report = REPORT.build_report(
                group,
                snapshot_root / snapshot_id / "inventory.json",
                snapshot_root / snapshot_id / "matrix.json",
            )
            for result in report["results"]:
                key = (
                    result["modelId"],
                    result["profileId"],
                    result["platformFamily"],
                    result["operatingSystemId"],
                    snapshot_id,
                )
                if key in keys:
                    raise MultiSnapshotError("duplicate-summary-result")
                keys.add(key)
                merged.append({"metadataSnapshotId": snapshot_id, **result})
        return {
            "schemaVersion": 1,
            "kind": "alpha2-multi-snapshot-model-qualification-summary",
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
            "automaticSelectionEvidenceAllowed": False,
            "automaticDefaultChangeAllowed": False,
            "metadataSnapshots": snapshots,
            "fullGpuResidencyResults": sorted(residency_results, key=lambda value: (
                value["modelId"], value["hardwareProfileId"],
                value["operatingSystemId"], value["metadataSnapshotId"],
            )),
            "results": sorted(merged, key=lambda value: (
                value["modelId"], value["profileId"], value["platformFamily"],
                value["operatingSystemId"], value["metadataSnapshotId"],
            )),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = build_multi_report(args.evidence_dir)
    except (MultiSnapshotError, REPORT.ReportError, SNAPSHOTS.SnapshotError) as error:
        print(json.dumps({"outcome": "failed", "errorCode": str(error)}, sort_keys=True))
        return 1
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.exists() or args.output.is_symlink():
            print(json.dumps({"outcome": "failed", "errorCode": "output-already-exists"}, sort_keys=True))
            return 1
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
