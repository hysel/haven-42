#!/usr/bin/env python3
"""Materialize hash-verified historical qualification metadata snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
MAP_PATH = ROOT / "config/alpha-2-qualification-campaign-snapshots.json"
CURRENT_INVENTORY = ROOT / "config/alpha-2-model-version-inventory.json"
CURRENT_MATRIX = ROOT / "config/alpha-2-model-qualification-matrix.json"
MAX_BYTES = 2 * 1024 * 1024


class SnapshotError(ValueError):
    """Snapshot inputs or derived hashes were invalid."""


def _load(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise SnapshotError("unsafe-snapshot-input")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SnapshotError("invalid-snapshot-input") from error
    if not isinstance(value, dict):
        raise SnapshotError("invalid-snapshot-input")
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def _from_git(commit: str, path: str) -> dict[str, Any]:
    if len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit):
        raise SnapshotError("invalid-snapshot-commit")
    if path != "config/alpha-2-model-version-inventory.json":
        raise SnapshotError("invalid-snapshot-git-path")
    try:
        completed = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        if len(completed.stdout) > MAX_BYTES:
            raise SnapshotError("invalid-snapshot-input")
        value = json.loads(completed.stdout.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        raise SnapshotError("historical-snapshot-unavailable") from error
    if not isinstance(value, dict):
        raise SnapshotError("invalid-snapshot-input")
    return value


def _remove_inventory_entries(
    inventory: dict[str, Any], candidate_ids: set[str], family_names: set[str],
    drop_empty_candidate_versions: set[str] | None = None,
) -> dict[str, Any]:
    value = json.loads(json.dumps(inventory))
    drop_empty_candidate_versions = drop_empty_candidate_versions or set()
    value["families"] = [
        family for family in value.get("families", [])
        if isinstance(family, dict) and family.get("family") not in family_names
    ]
    for family in value["families"]:
        for version in family.get("versions", []):
            if isinstance(version, dict) and isinstance(version.get("candidates"), list):
                version["candidates"] = [
                    candidate for candidate in version["candidates"]
                    if not isinstance(candidate, dict)
                    or candidate.get("id") not in candidate_ids
                ]
                version_key = f"{family.get('family', '')}/{version.get('version', '')}"
                if not version["candidates"] and version_key in drop_empty_candidate_versions:
                    del version["candidates"]
    return value


def _remove_matrix_candidates(
    matrix: dict[str, Any], candidate_ids: set[str], inventory_sha: str
) -> dict[str, Any]:
    value = json.loads(json.dumps(matrix))
    value["candidates"] = [
        candidate for candidate in value.get("candidates", [])
        if not isinstance(candidate, dict)
        or candidate.get("modelId") not in candidate_ids
    ]
    value["inventoryBinding"] = {
        "path": "config/alpha-2-model-version-inventory.json",
        "canonicalSha256": inventory_sha,
    }
    return value


def materialize(output: Path) -> list[dict[str, str]]:
    if output.exists() or output.is_symlink():
        raise SnapshotError("output-already-exists")
    mapping = _load(MAP_PATH)
    current_inventory = _load(CURRENT_INVENTORY)
    current_matrix = _load(CURRENT_MATRIX)
    results: list[dict[str, str]] = []
    values: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for snapshot in mapping.get("snapshots", []):
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("id"), str):
            raise SnapshotError("invalid-snapshot-map")
        inventory_source = snapshot.get("inventorySource")
        matrix_source = snapshot.get("matrixSource")
        if not isinstance(inventory_source, dict) or not isinstance(matrix_source, dict):
            raise SnapshotError("invalid-snapshot-map")
        if inventory_source.get("kind") == "git-commit":
            inventory = _from_git(
                inventory_source.get("commit", ""), inventory_source.get("path", "")
            )
        elif inventory_source.get("kind") == "current-minus-release-additions":
            inventory = _remove_inventory_entries(
                current_inventory,
                set(inventory_source.get("removedCandidateIds", [])),
                set(inventory_source.get("removedFamilies", [])),
                set(inventory_source.get("removedEmptyCandidateVersions", [])),
            )
        elif inventory_source.get("kind") == "current-minus-candidates":
            inventory = _remove_inventory_entries(
                current_inventory,
                set(inventory_source.get("removedCandidateIds", [])),
                set(),
                set(inventory_source.get("removedEmptyCandidateVersions", [])),
            )
        elif inventory_source.get("kind") == "current":
            inventory = json.loads(json.dumps(current_inventory))
        else:
            raise SnapshotError("invalid-snapshot-map")
        inventory_sha = _canonical_sha256(inventory)
        if matrix_source.get("kind") == "current-minus-candidates":
            matrix = _remove_matrix_candidates(
                current_matrix,
                set(matrix_source.get("removedCandidateIds", [])),
                inventory_sha,
            )
        elif matrix_source.get("kind") == "current":
            matrix = json.loads(json.dumps(current_matrix))
        else:
            raise SnapshotError("invalid-snapshot-map")
        matrix_sha = _canonical_sha256(matrix)
        if (
            inventory_sha != snapshot.get("inventoryCanonicalSha256")
            or matrix_sha != snapshot.get("matrixCanonicalSha256")
        ):
            raise SnapshotError("snapshot-hash-mismatch")
        values.append((snapshot["id"], inventory, matrix))
        results.append({
            "id": snapshot["id"],
            "inventoryCanonicalSha256": inventory_sha,
            "matrixCanonicalSha256": matrix_sha,
        })
    output.mkdir(mode=0o700, parents=False)
    for snapshot_id, inventory, matrix in values:
        directory = output / snapshot_id
        directory.mkdir(mode=0o700)
        (directory / "inventory.json").write_text(
            json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (directory / "matrix.json").write_text(
            json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        results = materialize(args.output_dir)
    except SnapshotError as error:
        print(json.dumps({"outcome": "failed", "errorCode": str(error)}, sort_keys=True))
        return 1
    print(json.dumps({
        "schemaVersion": 1,
        "kind": "alpha2-qualification-snapshot-materialization",
        "outcome": "passed",
        "snapshots": results,
        "containsPrivateInfrastructure": False,
        "automaticPromotionAllowed": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
