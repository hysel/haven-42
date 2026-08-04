#!/usr/bin/env python3
"""Require a clean, exact-tree security review before significant commits."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "security-review-gate.json"
HEX_SHA = re.compile(r"[0-9a-f]{40}")
RECEIPT_KEYS = {
    "schema", "tree", "result", "changed-files", "changed-lines",
    "binary-files", "security-sensitive-paths",
}


class SecurityReviewError(ValueError):
    pass


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise SecurityReviewError(f"git-command-failed:{arguments[0]}")
    return result


def _valid_pattern(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and "\\" not in value
        and not value.startswith("/")
        and not any(part in {"", ".", ".."} for part in value.split("/"))
    )


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise SecurityReviewError("duplicate-config-key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except SecurityReviewError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SecurityReviewError("invalid-config-json") from error
    if not isinstance(value, dict) or set(value) != {
        "alwaysReviewPatterns", "largeChange", "receiptName", "repository", "schemaVersion",
    }:
        raise SecurityReviewError("invalid-config-shape")
    if value["schemaVersion"] != 1 or value["repository"] != "hysel/haven-42":
        raise SecurityReviewError("invalid-config-identity")
    if value["receiptName"] != "haven-42-security-review-v1":
        raise SecurityReviewError("invalid-receipt-name")
    patterns = value["alwaysReviewPatterns"]
    if not isinstance(patterns, list) or not patterns or not all(_valid_pattern(item) for item in patterns):
        raise SecurityReviewError("invalid-review-patterns")
    large = value["largeChange"]
    if not isinstance(large, dict) or set(large) != {
        "minimumChangedFiles", "minimumChangedLines",
    }:
        raise SecurityReviewError("invalid-large-change-policy")
    if (
        type(large["minimumChangedFiles"]) is not int
        or type(large["minimumChangedLines"]) is not int
        or large["minimumChangedFiles"] < 2
        or large["minimumChangedLines"] < 1
    ):
        raise SecurityReviewError("invalid-large-change-threshold")
    return value


def _safe_path(raw: bytes) -> str:
    value = os.fsdecode(raw)
    if (
        not value
        or "\\" in value
        or Path(value).is_absolute()
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise SecurityReviewError("unsafe-staged-path")
    return value


def staged_change(root: Path) -> dict[str, Any]:
    raw = git(root, "diff", "--cached", "--numstat", "--no-renames", "-z", "--").stdout
    records = []
    total_lines = 0
    binary_files = 0
    for item in raw.split(b"\0"):
        if not item:
            continue
        fields = item.split(b"\t", 2)
        if len(fields) != 3:
            raise SecurityReviewError("invalid-staged-numstat")
        added_raw, deleted_raw, path_raw = fields
        path = _safe_path(path_raw)
        if added_raw == b"-" or deleted_raw == b"-":
            added = deleted = 0
            binary = True
            binary_files += 1
        else:
            try:
                added = int(added_raw)
                deleted = int(deleted_raw)
            except ValueError as error:
                raise SecurityReviewError("invalid-staged-numstat") from error
            if added < 0 or deleted < 0:
                raise SecurityReviewError("invalid-staged-numstat")
            binary = False
        total_lines += added + deleted
        records.append({"path": path, "added": added, "deleted": deleted, "binary": binary})
    records.sort(key=lambda item: (item["path"].casefold(), item["path"]))
    return {
        "records": records,
        "changedFiles": len(records),
        "changedLines": total_lines,
        "binaryFiles": binary_files,
    }


def _matches(path: str, pattern: str) -> bool:
    normalized_path = path.casefold()
    normalized_pattern = pattern.casefold()
    pure = PurePosixPath(normalized_path)
    patterns = (
        (normalized_pattern, normalized_pattern[3:])
        if normalized_pattern.startswith("**/")
        else (normalized_pattern,)
    )
    return any(
        pure.match(candidate) or fnmatch.fnmatchcase(normalized_path, candidate)
        for candidate in patterns
    )


def classify(change: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    sensitive = sorted(
        {
            record["path"]
            for record in change["records"]
            if any(_matches(record["path"], pattern) for pattern in config["alwaysReviewPatterns"])
        },
        key=lambda item: (item.casefold(), item),
    )
    reasons = []
    large = config["largeChange"]
    if change["changedFiles"] >= large["minimumChangedFiles"]:
        reasons.append("large-file-count")
    if change["changedLines"] >= large["minimumChangedLines"]:
        reasons.append("large-line-count")
    if sensitive:
        reasons.append("security-sensitive-path")
    if change["binaryFiles"]:
        reasons.append("binary-content")
    return {
        **change,
        "required": bool(reasons),
        "reasons": reasons,
        "securitySensitivePaths": sensitive,
    }


def git_directory(root: Path) -> Path:
    raw = git(root, "rev-parse", "--git-dir").stdout.decode("utf-8").strip()
    path = Path(raw)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def receipt_path(root: Path, config: dict[str, Any]) -> Path:
    return git_directory(root) / config["receiptName"]


def index_tree(root: Path) -> str:
    value = git(root, "write-tree").stdout.decode("ascii").strip()
    if not HEX_SHA.fullmatch(value):
        raise SecurityReviewError("invalid-index-tree")
    return value


def parse_receipt(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as error:
        raise SecurityReviewError("clean-security-review-receipt-required") from error
    values: dict[str, str] = {}
    for line in lines:
        if line.count("=") != 1:
            raise SecurityReviewError("invalid-security-review-receipt")
        key, value = line.split("=", 1)
        if key in values or key not in RECEIPT_KEYS or not value:
            raise SecurityReviewError("invalid-security-review-receipt")
        values[key] = value
    if (
        set(values) != RECEIPT_KEYS
        or values["schema"] != "1"
        or values["result"] != "clean"
        or not HEX_SHA.fullmatch(values["tree"])
        or not values["changed-files"].isdigit()
        or not values["changed-lines"].isdigit()
        or not values["binary-files"].isdigit()
        or not values["security-sensitive-paths"].isdigit()
    ):
        raise SecurityReviewError("invalid-security-review-receipt")
    return values


def verify(root: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = load_config(config_path)
    review = classify(staged_change(root), config)
    if not review["records"]:
        raise SecurityReviewError("no-staged-change")
    if not review["required"]:
        return review
    receipt = parse_receipt(receipt_path(root, config))
    if receipt["tree"] != index_tree(root):
        raise SecurityReviewError("security-review-receipt-does-not-match-staged-tree")
    expected = {
        "changed-files": str(review["changedFiles"]),
        "changed-lines": str(review["changedLines"]),
        "binary-files": str(review["binaryFiles"]),
        "security-sensitive-paths": str(len(review["securitySensitivePaths"])),
    }
    if any(receipt[key] != value for key, value in expected.items()):
        raise SecurityReviewError("security-review-receipt-metadata-mismatch")
    return review


def _require_complete_index(root: Path) -> None:
    if git(root, "diff", "--quiet", "--", check=False).returncode != 0:
        raise SecurityReviewError("unstaged-tracked-changes-remain")
    if git(root, "ls-files", "--others", "--exclude-standard").stdout:
        raise SecurityReviewError("untracked-files-remain")


def record_clean(root: Path, config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = load_config(config_path)
    _require_complete_index(root)
    review = classify(staged_change(root), config)
    if not review["records"]:
        raise SecurityReviewError("no-staged-change")
    if not review["required"]:
        receipt_path(root, config).unlink(missing_ok=True)
        return review
    receipt_path(root, config).write_text(
        "\n".join(
            (
                "schema=1",
                f"tree={index_tree(root)}",
                "result=clean",
                f"changed-files={review['changedFiles']}",
                f"changed-lines={review['changedLines']}",
                f"binary-files={review['binaryFiles']}",
                f"security-sensitive-paths={len(review['securitySensitivePaths'])}",
                "",
            )
        ),
        encoding="utf-8",
    )
    return review


def record_findings(root: Path, config_path: Path = CONFIG_PATH) -> None:
    config = load_config(config_path)
    receipt_path(root, config).unlink(missing_ok=True)
    raise SecurityReviewError(
        "security-findings-present:stop-fix-findings-and-notify-repository-owner"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--verify", action="store_true")
    action.add_argument("--record-clean", action="store_true")
    action.add_argument("--record-findings", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    try:
        if args.record_findings:
            record_findings(args.root.resolve(), args.config)
        elif args.record_clean:
            review = record_clean(args.root.resolve(), args.config)
            print(
                "Clean security review recorded for exact staged tree: "
                f"{review['changedFiles']} files, {review['changedLines']} changed lines."
            )
        else:
            review = verify(args.root.resolve(), args.config)
            if review["required"]:
                print("Exact staged-tree security review verified clean.")
            else:
                print("Security review gate passed: staged change is below the mandatory threshold.")
        return 0
    except SecurityReviewError as error:
        print(f"Security review gate blocked: {error}", file=sys.stderr)
        if "receipt-required" in str(error) or "findings-present" in str(error):
            print(
                "Stop before commit. Review the complete staged diff. If any finding exists, "
                "notify the repository owner and fix it; record clean only when zero findings remain.",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
