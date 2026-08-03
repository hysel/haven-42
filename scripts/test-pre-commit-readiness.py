#!/usr/bin/env python3
"""Hostile tests for exact staged-tree pre-commit readiness."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify-pre-commit-readiness.py"
SPEC = importlib.util.spec_from_file_location("precommit_readiness", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def run(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
    ).stdout


def reject(root: Path, expected: str) -> None:
    try:
        MODULE.verify(root)
    except MODULE.ReadinessError as exc:
        if expected not in str(exc):
            raise AssertionError(f"unexpected rejection: {exc}") from exc
    else:
        raise AssertionError(f"unsafe case was accepted: {expected}")


def write_receipt(root: Path, tree: str) -> None:
    commit = run(root, "rev-parse", "HEAD").decode("ascii").strip()
    git_dir = Path(run(root, "rev-parse", "--git-dir").decode().strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    (git_dir / MODULE.RECEIPT_NAME).write_text(
        "\n".join(
            (
                "schema=3",
                f"commit={commit}",
                f"tree={tree}",
                "source=index",
                "tier=full",
                "runner=windows",
                "",
            )
        ),
        encoding="utf-8",
    )


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-precommit-") as raw:
        root = Path(raw)
        run(root, "init", "--initial-branch=main")
        run(root, "config", "user.name", "Haven 42 Test")
        run(root, "config", "user.email", "haven42@example.invalid")
        tracked = root / "tracked.txt"
        tracked.write_text("base\n", encoding="utf-8")
        run(root, "add", "tracked.txt")
        run(root, "commit", "-m", "fixture")

        tracked.write_text("staged\n", encoding="utf-8")
        run(root, "add", "tracked.txt")
        reject(root, "no Full-test receipt")
        checks += 1

        tree = run(root, "write-tree").decode("ascii").strip()
        write_receipt(root, "0" * 40)
        reject(root, "does not match")
        checks += 1

        write_receipt(root, tree)
        if MODULE.verify(root) != tree:
            raise AssertionError("matching staged tree was not accepted")
        checks += 1

        tracked.write_text("unstaged\n", encoding="utf-8")
        reject(root, "unstaged tracked")
        checks += 1
        tracked.write_text("staged\n", encoding="utf-8")

        untracked = root / "untracked.txt"
        untracked.write_text("local\n", encoding="utf-8")
        reject(root, "untracked files")
        checks += 1
        untracked.unlink()

        run(root, "reset")
        run(root, "restore", "tracked.txt")
        reject(root, "no staged change")
        checks += 1

    print(f"Pre-commit readiness hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
