#!/usr/bin/env python3
"""Hostile tests for the exact-tree security-review commit gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "security-review-gate.py"
CONFIG_PATH = ROOT / "config" / "security-review-gate.json"
SPEC = importlib.util.spec_from_file_location("security_review_gate", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def run(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
    ).stdout


def reject(action, expected: str) -> None:
    try:
        action()
    except MODULE.SecurityReviewError as error:
        if expected not in str(error):
            raise AssertionError(f"unexpected rejection: {error}") from error
    else:
        raise AssertionError(f"unsafe security-review case accepted: {expected}")


def reset(root: Path) -> None:
    run(root, "reset", "--hard", "HEAD")
    run(root, "clean", "-fd")
    MODULE.receipt_path(root, MODULE.load_config(CONFIG_PATH)).unlink(missing_ok=True)


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-security-review-") as raw:
        root = Path(raw)
        run(root, "init", "--initial-branch=main")
        run(root, "config", "user.name", "Haven 42 Test")
        run(root, "config", "user.email", "haven42@example.invalid")
        (root / "base.txt").write_text("base\n", encoding="utf-8")
        run(root, "add", "base.txt")
        run(root, "commit", "-m", "fixture")

        (root / "notes.txt").write_text("small\n", encoding="utf-8")
        run(root, "add", "notes.txt")
        review = MODULE.verify(root, CONFIG_PATH)
        if review["required"] or review["changedFiles"] != 1:
            raise AssertionError("small ordinary change should not require a receipt")
        checks += 1

        reset(root)
        (root / "web").mkdir()
        (root / "web" / "app.js").write_text("safe();\n", encoding="utf-8")
        run(root, "add", "web/app.js")
        reject(lambda: MODULE.verify(root, CONFIG_PATH), "receipt-required")
        review = MODULE.record_clean(root, CONFIG_PATH)
        if review["reasons"] != ["security-sensitive-path"]:
            raise AssertionError("security-sensitive path classification drifted")
        MODULE.verify(root, CONFIG_PATH)
        checks += 3

        reset(root)
        (root / "WEB").mkdir()
        (root / "WEB" / "case.js").write_text("safe();\n", encoding="utf-8")
        run(root, "add", "WEB/case.js")
        reject(lambda: MODULE.verify(root, CONFIG_PATH), "receipt-required")
        checks += 1

        reset(root)
        (root / "web").mkdir()
        (root / "web" / "app.js").write_text("safe();\n", encoding="utf-8")
        run(root, "add", "web/app.js")
        MODULE.record_clean(root, CONFIG_PATH)
        (root / "web" / "app.js").write_text("changedAgain();\n", encoding="utf-8")
        run(root, "add", "web/app.js")
        reject(lambda: MODULE.verify(root, CONFIG_PATH), "does-not-match-staged-tree")
        checks += 1
        MODULE.record_clean(root, CONFIG_PATH)
        reject(lambda: MODULE.record_findings(root, CONFIG_PATH), "findings-present")
        reject(lambda: MODULE.verify(root, CONFIG_PATH), "receipt-required")
        checks += 2

        reset(root)
        (root / "large.txt").write_text("".join(f"line-{index}\n" for index in range(500)), encoding="utf-8")
        run(root, "add", "large.txt")
        review = MODULE.classify(MODULE.staged_change(root), MODULE.load_config(CONFIG_PATH))
        if "large-line-count" not in review["reasons"]:
            raise AssertionError("large line count did not require review")
        checks += 1

        reset(root)
        for index in range(10):
            (root / f"file-{index}.txt").write_text("change\n", encoding="utf-8")
        run(root, "add", ".")
        review = MODULE.classify(MODULE.staged_change(root), MODULE.load_config(CONFIG_PATH))
        if "large-file-count" not in review["reasons"]:
            raise AssertionError("large file count did not require review")
        checks += 1

        reset(root)
        (root / "payload.bin").write_bytes(b"\x00\x01\x02")
        run(root, "add", "payload.bin")
        review = MODULE.classify(MODULE.staged_change(root), MODULE.load_config(CONFIG_PATH))
        if review["binaryFiles"] != 1 or "binary-content" not in review["reasons"]:
            raise AssertionError("binary content did not require review")
        checks += 1

        (root / "untracked.txt").write_text("local\n", encoding="utf-8")
        reject(lambda: MODULE.record_clean(root, CONFIG_PATH), "untracked-files-remain")
        (root / "untracked.txt").unlink()
        (root / "base.txt").write_text("unstaged\n", encoding="utf-8")
        reject(lambda: MODULE.record_clean(root, CONFIG_PATH), "unstaged-tracked-changes-remain")
        checks += 2

    print(f"Security review gate hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
