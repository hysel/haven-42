#!/usr/bin/env python3
"""Generate an exact, repository-relative evidence input binding."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("alpha2_binding_freshness", ROOT / "scripts/alpha2-evidence-freshness.py")
assert SPEC and SPEC.loader
FRESHNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FRESHNESS)


class BindingError(ValueError):
    pass


def build_binding(evidence_id: str, specifications: list[str], root: Path = ROOT) -> dict[str, Any]:
    if not evidence_id or len(evidence_id) > 128:
        raise BindingError("invalid-evidence-id")
    inputs: list[dict[str, str]] = []
    for specification in specifications:
        parts = specification.split("=", 2)
        if len(parts) != 3:
            raise BindingError("input must be role=hash-mode=repository/path")
        role, mode, logical_path = parts
        if not role:
            raise BindingError("input role is required")
        path = FRESHNESS._safe_path(root, logical_path)
        if not path.is_file() or path.is_symlink():
            raise BindingError(f"input is not a regular file: {logical_path}")
        if mode == "canonical-json":
            try:
                digest = FRESHNESS.canonical_json_sha256(json.loads(path.read_text(encoding="utf-8")))
            except (UnicodeError, json.JSONDecodeError) as error:
                raise BindingError(f"input is not valid UTF-8 JSON: {logical_path}") from error
        elif mode == "file-bytes":
            digest = FRESHNESS.file_sha256(path)
        else:
            raise BindingError(f"unsupported hash mode: {mode}")
        inputs.append({"role": role, "path": logical_path, "hashMode": mode, "sha256": digest})
    binding = {
        "schemaVersion": 1,
        "kind": "haven42-evidence-input-binding",
        "evidenceId": evidence_id,
        "inputs": inputs,
    }
    FRESHNESS.validate_binding(binding)
    return binding


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-id", required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", action="append", required=True, dest="inputs")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        binding = build_binding(args.evidence_id, args.inputs, args.root)
    except (OSError, BindingError, FRESHNESS.FreshnessError) as error:
        print(f"Refused: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(binding, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(rendered, encoding="utf-8")
        temporary.replace(args.output)
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
