#!/usr/bin/env python3
"""Hostile tests for deterministic local pre-merge readiness."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "check-pre-merge-readiness.py"
SPEC = importlib.util.spec_from_file_location("premerge_readiness", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASE_CONFIG = json.loads((ROOT / "config" / "pre-merge-readiness.json").read_text(encoding="utf-8"))


def run(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
    )
    return result.stdout


def write_config(root: Path, value: dict | None = None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "readiness.json"
    path.write_text(json.dumps(value or BASE_CONFIG, indent=2) + "\n", encoding="utf-8")
    return path


def commit(root: Path, text: str) -> None:
    (root / "tracked.txt").write_text(text + "\n", encoding="utf-8")
    run(root, "add", "tracked.txt")
    run(root, "commit", "-m", text)


def fixture(parent: Path) -> tuple[Path, Path]:
    parent.mkdir(parents=True)
    remote = parent / "remote.git"
    root = parent / "haven-42"
    run(parent, "init", "--bare", str(remote))
    run(parent, "init", "--initial-branch=main", str(root))
    run(root, "config", "user.name", "Haven 42 Test")
    run(root, "config", "user.email", "haven42@example.invalid")
    commit(root, "base")
    run(root, "remote", "add", "origin", "https://github.com/hysel/haven-42.git")
    run(root, "update-ref", "refs/remotes/origin/main", "HEAD")
    run(root, "switch", "-c", "batch/test")
    (root / "ROADMAP.md").write_text("pending\n", encoding="utf-8")
    return root, write_config(parent)


def rejected(root: Path, config: Path, expected: str, mode: str = "spot") -> None:
    try:
        MODULE.evaluate(root, config, mode)
    except MODULE.ReadinessError as error:
        if expected not in str(error):
            raise AssertionError(f"unexpected rejection: {error}") from error
    else:
        raise AssertionError(f"unsafe case accepted: {expected}")


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-premerge-") as raw:
        parent = Path(raw)

        root, config = fixture(parent / "accepted")
        report = MODULE.evaluate(root, config, "spot")
        if report["history"] != "equal" or report["changedPaths"] != ["ROADMAP.md"]:
            raise AssertionError("deterministic spot report was incorrect")
        if [group["id"] for group in report["testGroups"]] != ["repository-core"]:
            raise AssertionError("fallback test mapping was not deterministic")
        checks += 1

        run(root, "remote", "set-url", "origin", "https://github.com/example/wrong.git")
        rejected(root, config, "wrong-origin")
        run(root, "remote", "set-url", "origin", "https://github.com/hysel/haven-42.git")
        checks += 1

        run(root, "switch", "main")
        rejected(root, config, "feature-branch-required")
        run(root, "switch", "batch/test")
        checks += 1

        run(root, "checkout", "--detach")
        rejected(root, config, "detached-head")
        run(root, "switch", "batch/test")
        checks += 1

        run(root, "reset", "--hard", "HEAD")
        commit(root, "feature")
        run(root, "update-ref", "refs/remotes/origin/main", "HEAD^")
        (root / "ROADMAP.md").write_text("pending\n", encoding="utf-8")
        if MODULE.evaluate(root, config, "spot")["history"] != "ahead":
            raise AssertionError("ahead history was not accepted")
        checks += 1

        remote_commit = run(
            root, "commit-tree", "HEAD^{tree}", "-p", "HEAD^", "-m", "remote"
        ).decode("ascii").strip()
        run(root, "update-ref", "refs/remotes/origin/main", remote_commit)
        rejected(root, config, "history-diverged")
        checks += 1

        run(root, "reset", "--hard", "HEAD^")
        run(root, "update-ref", "refs/remotes/origin/main", remote_commit)
        (root / "ROADMAP.md").write_text("pending\n", encoding="utf-8")
        rejected(root, config, "history-behind")
        checks += 1

        root, config = fixture(parent / "ignored")
        (root / ".git" / "info" / "exclude").write_text("unexpected-secret.pem\n", encoding="utf-8")
        (root / "unexpected-secret.pem").write_text("fixture\n", encoding="utf-8")
        rejected(root, config, "unexpected-ignored-sensitive-inputs")
        checks += 1

        (root / "unexpected-secret.pem").unlink()
        (root / ".git" / "info" / "exclude").write_text(".env\n", encoding="utf-8")
        (root / ".env").write_text("fixture\n", encoding="utf-8")
        if MODULE.evaluate(root, config, "spot")["ignoredSensitiveFindingCount"] != 0:
            raise AssertionError("approved ignored input was rejected")
        checks += 1

        config_value = copy.deepcopy(BASE_CONFIG)
        config_value["testGroups"][0]["commands"] = ["safe\nunsafe"]
        bad_config = write_config(parent / "bad-command", config_value)
        rejected(root, bad_config, "invalid-test-group-commands")
        checks += 1

        duplicate = parent / "duplicate.json"
        duplicate.write_text('{"schemaVersion":1,"schemaVersion":1}\n', encoding="utf-8")
        rejected(root, duplicate, "duplicate-config-key")
        checks += 1

        rejected(root, config, "exact-tree-receipt", mode="commit")
        checks += 1

    print(f"Pre-merge readiness hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
