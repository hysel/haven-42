#!/usr/bin/env python3
"""Rank fully qualified models for owner review without changing a default."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
MATRIX_PATH = ROOT / "config/alpha-2-model-qualification-matrix.json"
CAPABILITIES = ("general.chat", "content.write", "content.summarize")
MAX_INPUT_BYTES = 2 * 1024 * 1024


class RankingError(ValueError):
    """The qualification summary was stale, unsafe, or incomplete."""


def _load(path: Path, code: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            raise RankingError(code)
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RankingError(code) from error
    if not isinstance(value, dict):
        raise RankingError(code)
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _positive_rate(value: Any) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value <= 0
    ):
        raise RankingError("invalid-qualification-summary")
    return float(value)


def build_ranking(
    summary_path: Path,
    inventory_path: Path = INVENTORY_PATH,
    matrix_path: Path = MATRIX_PATH,
) -> dict[str, Any]:
    inventory = _load(inventory_path, "invalid-qualification-inventory")
    matrix = _load(matrix_path, "invalid-qualification-matrix")
    inventory_sha = _canonical_sha256(inventory)
    matrix_sha = _canonical_sha256(matrix)
    if matrix.get("inventoryBinding") != {
        "path": "config/alpha-2-model-version-inventory.json",
        "canonicalSha256": inventory_sha,
    }:
        raise RankingError("stale-qualification-matrix")

    summary = _load(summary_path, "invalid-qualification-summary")
    if (
        summary.get("schemaVersion") != 1
        or summary.get("kind") != "alpha2-model-qualification-summary"
        or summary.get("qualificationInventoryCanonicalSha256") != inventory_sha
        or summary.get("qualificationMatrixCanonicalSha256") != matrix_sha
        or summary.get("containsRawPromptsOrResponses") is not False
        or summary.get("containsPrivateMachineIdentity") is not False
        or summary.get("automaticSelectionEvidenceAllowed") is not False
        or summary.get("automaticDefaultChangeAllowed") is not False
    ):
        raise RankingError("invalid-qualification-summary")
    results = summary.get("results")
    if not isinstance(results, list):
        raise RankingError("invalid-qualification-summary")

    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    seen: set[tuple[str, str, str, str]] = set()
    for result in results:
        if not isinstance(result, dict) or result.get("status") != "passed":
            continue
        model_id = result.get("modelId")
        profile_id = result.get("profileId")
        platform_family = result.get("platformFamily")
        operating_system_id = result.get("operatingSystemId")
        if not all(
            isinstance(value, str) and value
            for value in (
                model_id,
                profile_id,
                platform_family,
                operating_system_id,
            )
        ) or platform_family not in {"linux", "windows"}:
            raise RankingError("invalid-qualification-summary")
        identity = (model_id, profile_id, platform_family, operating_system_id)
        if identity in seen:
            raise RankingError("duplicate-qualification-result")
        seen.add(identity)
        tasks = result.get("tasks")
        soak = result.get("soak")
        if not isinstance(tasks, dict) or not isinstance(soak, dict):
            raise RankingError("invalid-qualification-summary")
        soak_rate = _positive_rate(soak.get("averageTokensPerSecond"))
        if soak.get("outcome") != "passed":
            raise RankingError("invalid-qualification-summary")
        for capability in CAPABILITIES:
            task = tasks.get(capability)
            metrics = task.get("metrics") if isinstance(task, dict) else None
            if (
                not isinstance(task, dict)
                or task.get("outcome") != "passed"
                or not isinstance(metrics, dict)
            ):
                raise RankingError("invalid-qualification-summary")
            output_tokens = metrics.get("outputTokens")
            peak_gpu_memory = metrics.get("peakGpuMemoryBytes")
            if (
                metrics.get("samplesPassed") != 3
                or metrics.get("unloadPasses") != 3
                or isinstance(output_tokens, bool)
                or not isinstance(output_tokens, int)
                or output_tokens <= 0
                or isinstance(peak_gpu_memory, bool)
                or not isinstance(peak_gpu_memory, int)
                or peak_gpu_memory < 0
            ):
                raise RankingError("invalid-qualification-summary")
            rate = _positive_rate(metrics.get("tokensPerSecond"))
            groups.setdefault(
                (platform_family, profile_id, operating_system_id, capability), []
            ).append(
                {
                    "modelId": model_id,
                    "taskTokensPerSecond": rate,
                    "soakTokensPerSecond": soak_rate,
                }
            )

    rankings = []
    for key, candidates in sorted(groups.items()):
        ordered = sorted(
            candidates,
            key=lambda item: (
                -item["taskTokensPerSecond"],
                -item["soakTokensPerSecond"],
                item["modelId"],
            ),
        )
        rankings.append(
            {
                "platformFamily": key[0],
                "profileId": key[1],
                "operatingSystemId": key[2],
                "capability": key[3],
                "candidates": [
                    {**candidate, "rank": index}
                    for index, candidate in enumerate(ordered, start=1)
                ],
            }
        )
    return {
        "schemaVersion": 1,
        "kind": "alpha2-model-qualification-owner-review-ranking",
        "qualificationInventoryCanonicalSha256": inventory_sha,
        "qualificationMatrixCanonicalSha256": matrix_sha,
        "rankingBasis": "task-throughput-after-all-quality-gates-and-soak-pass",
        "containsRawPromptsOrResponses": False,
        "containsPrivateMachineIdentity": False,
        "automaticSelectionAllowed": False,
        "automaticDefaultChangeAllowed": False,
        "ownerApprovalRequired": True,
        "rankings": rankings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument(
        "--inventory",
        type=Path,
        help="Pinned inventory snapshot used to create a historical summary.",
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        help="Pinned matrix snapshot bound to the historical inventory.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if (args.inventory is None) != (args.matrix is None):
        parser.error("inventory-and-matrix-must-be-supplied-together")
    try:
        result = build_ranking(
            args.summary,
            args.inventory or INVENTORY_PATH,
            args.matrix or MATRIX_PATH,
        )
    except RankingError as error:
        parser.error(str(error))
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        if args.output.exists() or args.output.is_symlink():
            parser.error("output-already-exists")
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
