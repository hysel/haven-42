#!/usr/bin/env python3
"""Fail closed unless the complete staged tree has a Full-test receipt."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT_NAME = "haven-42-test-receipt-v1"
RECEIPT_KEYS = {"schema", "commit", "tree", "source", "tier", "runner"}


class ReadinessError(ValueError):
    pass


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        text=False,
    )
    if check and result.returncode != 0:
        raise ReadinessError(f"git command failed: {' '.join(arguments)}")
    return result


def parse_receipt(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as exc:
        raise ReadinessError("the exact staged tree has no Full-test receipt") from exc
    values: dict[str, str] = {}
    for line in lines:
        if line.count("=") != 1:
            raise ReadinessError("the Full-test receipt is malformed")
        key, value = line.split("=", 1)
        if key in values or key not in RECEIPT_KEYS or not value:
            raise ReadinessError("the Full-test receipt is malformed")
        values[key] = value
    if set(values) != RECEIPT_KEYS:
        raise ReadinessError("the Full-test receipt is malformed")
    if (
        values["schema"] != "3"
        or values["tier"] != "full"
        or values["source"] not in {"head", "index"}
        or values["runner"] not in {"windows", "native-shell"}
        or not re.fullmatch(r"[0-9a-f]{40}", values["commit"])
        or not re.fullmatch(r"[0-9a-f]{40}", values["tree"])
    ):
        raise ReadinessError("the Full-test receipt has invalid values")
    return values


def verify(root: Path) -> str:
    root = root.resolve()
    if not root.is_dir():
        raise ReadinessError("repository root does not exist")
    if git(root, "diff", "--quiet", "--", check=False).returncode != 0:
        raise ReadinessError("unstaged tracked changes remain")
    if git(root, "ls-files", "--others", "--exclude-standard").stdout:
        raise ReadinessError("untracked files remain")
    if git(root, "diff", "--cached", "--quiet", check=False).returncode == 0:
        raise ReadinessError("no staged change is available to commit")
    index_tree = git(root, "write-tree").stdout.decode("ascii").strip()
    git_dir_text = git(root, "rev-parse", "--git-dir").stdout.decode("utf-8").strip()
    git_dir = Path(git_dir_text)
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    receipt = parse_receipt(git_dir.resolve() / RECEIPT_NAME)
    if receipt["tree"] != index_tree:
        raise ReadinessError("the Full-test receipt does not match the staged tree")
    return index_tree


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        tree = verify(args.root)
    except ReadinessError as exc:
        print(f"Pre-commit readiness failed: {exc}")
        return 1
    print(f"Pre-commit readiness passed for staged tree {tree}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
