#!/usr/bin/env python3
"""Fail closed when public Haven 42 milestone status documents disagree."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "project-status-consistency.json"


class StatusError(ValueError):
    pass


def load_contract(path: Path = CONTRACT) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise StatusError("status contract must be an object")
    expected_keys = {
        "schemaVersion",
        "authority",
        "milestones",
        "documents",
        "classificationPatterns",
        "requiredMarkers",
        "forbiddenMarkers",
        "effects",
    }
    if set(value) != expected_keys:
        raise StatusError("status contract keys do not match the closed schema")
    if value.get("schemaVersion") != 2:
        raise StatusError("unsupported status contract schema")
    effects = value.get("effects")
    if effects != {
        "writesFiles": False,
        "networkAllowed": False,
        "processLaunchAllowed": False,
        "statusPromotionAllowed": False,
    }:
        raise StatusError("status verifier effects must remain fully denied")
    documents = value.get("documents")
    milestones = value.get("milestones")
    patterns = value.get("classificationPatterns")
    authority = value.get("authority")
    if not isinstance(documents, dict) or not documents:
        raise StatusError("status documents must be a non-empty object")
    if authority not in documents:
        raise StatusError("status authority must be one of the checked documents")
    for relative, settings in documents.items():
        if (
            not isinstance(relative, str)
            or not relative
            or not isinstance(settings, dict)
            or set(settings) != {"rowPrefix"}
            or not isinstance(settings["rowPrefix"], str)
        ):
            raise StatusError("status document entries must contain only rowPrefix")
    if not isinstance(milestones, dict) or not milestones:
        raise StatusError("milestones must be a non-empty object")
    if not isinstance(patterns, dict) or not patterns:
        raise StatusError("classification patterns must be a non-empty object")
    for milestone, classification in milestones.items():
        if (
            not isinstance(milestone, str)
            or not milestone.isdecimal()
            or not isinstance(classification, str)
            or classification not in patterns
        ):
            raise StatusError("milestone classifications must reference known patterns")
    for classification, pattern in patterns.items():
        if not isinstance(classification, str) or not isinstance(pattern, str):
            raise StatusError("classification patterns must be strings")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise StatusError(f"invalid classification pattern: {classification}") from exc
    for field in ("requiredMarkers", "forbiddenMarkers"):
        groups = value.get(field)
        if not isinstance(groups, dict):
            raise StatusError(f"{field} must be an object")
        for relative, markers in groups.items():
            if (
                not isinstance(relative, str)
                or not relative
                or not isinstance(markers, list)
                or not markers
                or any(not isinstance(marker, str) or not marker for marker in markers)
                or len(markers) != len(set(markers))
            ):
                raise StatusError(f"{field} entries must contain unique non-empty strings")
    return value


def table_statuses(text: str, row_prefix: str) -> dict[str, str]:
    found: dict[str, str] = {}
    prefix = re.escape(row_prefix)
    row = re.compile(rf"^\|\s*{prefix}(\d+):[^|]*\|\s*([^|]+?)\s*\|")
    for line in text.splitlines():
        match = row.match(line)
        if not match:
            continue
        milestone, status = match.groups()
        if milestone in found:
            raise StatusError(f"duplicate milestone {milestone} status row")
        found[milestone] = status.strip()
    return found


def verify(root: Path, contract: dict) -> list[str]:
    errors: list[str] = []
    milestones = contract["milestones"]
    patterns = {
        key: re.compile(pattern)
        for key, pattern in contract["classificationPatterns"].items()
    }
    for relative, settings in contract["documents"].items():
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing status document")
            continue
        try:
            statuses = table_statuses(
                path.read_text(encoding="utf-8"), settings["rowPrefix"]
            )
        except StatusError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        for milestone, classification in milestones.items():
            status = statuses.get(milestone)
            if status is None:
                errors.append(f"{relative}: missing milestone {milestone} status row")
                continue
            if not patterns[classification].search(status):
                errors.append(
                    f"{relative}: milestone {milestone} status {status!r} "
                    f"does not classify as {classification!r}"
                )
    for relative, markers in contract["requiredMarkers"].items():
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing required status companion")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if text.count(marker) != 1:
                errors.append(
                    f"{relative}: marker must appear exactly once: {marker!r}"
                )
    for relative, markers in contract["forbiddenMarkers"].items():
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: missing forbidden-marker companion")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker in text:
                errors.append(f"{relative}: stale marker must be absent: {marker!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    args = parser.parse_args()
    try:
        contract = load_contract(args.contract.resolve())
        errors = verify(args.root.resolve(), contract)
    except (OSError, json.JSONDecodeError, StatusError) as exc:
        print(f"Project status consistency failed: {exc}")
        return 1
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"Project status consistency failed with {len(errors)} error(s).")
        return 1
    count = len(contract["milestones"]) * len(contract["documents"])
    print(f"Project status consistency passed: {count} milestone/document cells.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
