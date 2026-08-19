#!/usr/bin/env python3
"""Verify that an evidence record is bound to exact repository inputs.

This checker is intentionally generic. It grants no product admission and
does not update support labels; it only reports whether every declared input
still matches the bytes or canonical JSON that were originally evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SHA256 = set("0123456789abcdef")


class FreshnessError(ValueError):
    pass


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise FreshnessError("invalid-repository-path")
    logical = PurePosixPath(value)
    if logical.is_absolute() or ".." in logical.parts:
        raise FreshnessError("invalid-repository-path")
    candidate = (root / Path(*logical.parts)).resolve()
    resolved_root = root.resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as error:
        raise FreshnessError("repository-path-escaped") from error
    return candidate


def validate_binding(binding: Any) -> list[dict[str, str]]:
    if not isinstance(binding, dict) or set(binding) != {
        "schemaVersion", "kind", "evidenceId", "inputs"
    }:
        raise FreshnessError("invalid-binding-shape")
    if binding["schemaVersion"] != 1 or binding["kind"] != "haven42-evidence-input-binding":
        raise FreshnessError("invalid-binding-identity")
    if not isinstance(binding["evidenceId"], str) or not binding["evidenceId"]:
        raise FreshnessError("invalid-evidence-id")
    inputs = binding["inputs"]
    if not isinstance(inputs, list) or not inputs:
        raise FreshnessError("missing-bound-inputs")
    roles: set[str] = set()
    validated: list[dict[str, str]] = []
    for item in inputs:
        if not isinstance(item, dict) or set(item) != {"role", "path", "hashMode", "sha256"}:
            raise FreshnessError("invalid-input-shape")
        if not isinstance(item["role"], str) or not item["role"] or item["role"] in roles:
            raise FreshnessError("invalid-input-role")
        roles.add(item["role"])
        if item["hashMode"] not in {"file-bytes", "canonical-json"}:
            raise FreshnessError("invalid-hash-mode")
        digest = item["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in SHA256 for c in digest):
            raise FreshnessError("invalid-input-sha256")
        validated.append(item)
    return validated


def assess(binding: Any, root: Path = ROOT) -> dict[str, Any]:
    inputs = validate_binding(binding)
    checks: list[dict[str, Any]] = []
    for item in inputs:
        path = _safe_path(root, item["path"])
        if not path.is_file():
            checks.append({
                "role": item["role"], "path": item["path"], "status": "missing",
                "expectedSha256": item["sha256"], "actualSha256": None,
            })
            continue
        if item["hashMode"] == "canonical-json":
            try:
                actual = canonical_json_sha256(json.loads(path.read_text(encoding="utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise FreshnessError("invalid-bound-json") from error
        else:
            actual = file_sha256(path)
        checks.append({
            "role": item["role"], "path": item["path"],
            "status": "matched" if actual == item["sha256"] else "changed",
            "expectedSha256": item["sha256"], "actualSha256": actual,
        })
    fresh = all(item["status"] == "matched" for item in checks)
    return {
        "schemaVersion": 1,
        "kind": "haven42-evidence-freshness-result",
        "evidenceId": binding["evidenceId"],
        "status": "fresh" if fresh else "stale",
        "admissionAllowed": False,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check exact evidence input bindings.")
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        binding = json.loads(args.binding.read_text(encoding="utf-8"))
        result = assess(binding, args.root)
    except (OSError, json.JSONDecodeError, FreshnessError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "fresh" else 1


if __name__ == "__main__":
    raise SystemExit(main())
