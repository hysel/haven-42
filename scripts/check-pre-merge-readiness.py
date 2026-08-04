#!/usr/bin/env python3
"""Report deterministic local readiness before the expensive Full gate."""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "pre-merge-readiness.json"
PRECOMMIT_PATH = ROOT / "scripts" / "verify-pre-commit-readiness.py"
HEX_SHA = re.compile(r"[0-9a-f]{40}")
GROUP_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class ReadinessError(ValueError):
    pass


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=False,
        capture_output=True,
        text=False,
    )
    if check and result.returncode != 0:
        raise ReadinessError(f"git-command-failed:{arguments[0]}")
    return result


def load_json_strict(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ReadinessError("duplicate-config-key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)
    except ReadinessError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReadinessError("invalid-config-json") from error
    if not isinstance(value, dict):
        raise ReadinessError("invalid-config-shape")
    return value


def _valid_pattern(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and "\\" not in value
        and not value.startswith("/")
        and not any(part in {"", ".", ".."} for part in value.split("/"))
    )


def validate_config(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schemaVersion", "repository", "defaultBranch", "upstreamRef",
        "approvedIgnoredPatterns", "sensitiveIgnoredPatterns", "testGroups",
        "fullGate",
    }
    if set(value) != required or value["schemaVersion"] != 1:
        raise ReadinessError("invalid-config-shape")
    if value["repository"] != "hysel/haven-42" or value["defaultBranch"] != "main":
        raise ReadinessError("invalid-repository-policy")
    if value["upstreamRef"] != "origin/main":
        raise ReadinessError("invalid-upstream-policy")
    for key in ("approvedIgnoredPatterns", "sensitiveIgnoredPatterns"):
        patterns = value[key]
        if not isinstance(patterns, list) or not patterns or not all(_valid_pattern(item) for item in patterns):
            raise ReadinessError(f"invalid-{key}")
    groups = value["testGroups"]
    if not isinstance(groups, list) or not groups:
        raise ReadinessError("invalid-test-groups")
    seen: set[str] = set()
    for group in groups:
        if not isinstance(group, dict) or set(group) != {"id", "patterns", "commands"}:
            raise ReadinessError("invalid-test-group")
        group_id = group["id"]
        if not isinstance(group_id, str) or not GROUP_ID.fullmatch(group_id) or group_id in seen:
            raise ReadinessError("invalid-test-group-id")
        seen.add(group_id)
        if not isinstance(group["patterns"], list) or not group["patterns"] or not all(
            _valid_pattern(item) for item in group["patterns"]
        ):
            raise ReadinessError("invalid-test-group-patterns")
        if not isinstance(group["commands"], list) or not group["commands"] or not all(
            isinstance(item, str) and item and "\n" not in item and "\r" not in item
            for item in group["commands"]
        ):
            raise ReadinessError("invalid-test-group-commands")
    if groups[-1]["id"] != "repository-core" or groups[-1]["patterns"] != ["**"]:
        raise ReadinessError("missing-test-fallback")
    full_gate = value["fullGate"]
    if not isinstance(full_gate, dict) or set(full_gate) != {"windows", "posix"} or not all(
        isinstance(item, str) and item for item in full_gate.values()
    ):
        raise ReadinessError("invalid-full-gate")
    return value


def normalize_remote(value: str) -> str:
    candidate = value.strip().removesuffix(".git")
    prefixes = (
        "https://github.com/",
        "http://github.com/",
        "ssh://git@github.com/",
        "git@github.com:",
    )
    for prefix in prefixes:
        if candidate.lower().startswith(prefix):
            return candidate[len(prefix):].lower()
    return ""


def safe_paths(raw: bytes, label: str) -> list[str]:
    values = [os.fsdecode(item).rstrip("/") for item in raw.split(b"\0") if item]
    for value in values:
        if (
            not value
            or "\\" in value
            or Path(value).is_absolute()
            or any(part in {"", ".", ".."} for part in value.split("/"))
        ):
            raise ReadinessError(f"unsafe-{label}-path")
    return sorted(set(values), key=lambda item: (item.casefold(), item))


def changed_paths(root: Path) -> list[str]:
    tracked = git(root, "diff", "--name-only", "-z", "HEAD", "--").stdout
    untracked = git(root, "ls-files", "-z", "--others", "--exclude-standard").stdout
    return safe_paths(tracked + untracked, "changed")


def _matches(path: str, pattern: str) -> bool:
    pure = PurePosixPath(path)
    patterns = (pattern, pattern[3:]) if pattern.startswith("**/") else (pattern,)
    return any(
        pure.match(candidate) or fnmatch.fnmatchcase(path, candidate)
        for candidate in patterns
    )


def unexpected_ignored_sensitive(root: Path, config: dict[str, Any]) -> int:
    ignored = safe_paths(
        git(
            root, "ls-files", "-z", "--others", "--ignored",
            "--exclude-standard", "--directory",
        ).stdout,
        "ignored",
    )
    approved = config["approvedIgnoredPatterns"]
    sensitive = config["sensitiveIgnoredPatterns"]
    return sum(
        1
        for path in ignored
        if any(_matches(path.casefold(), pattern.casefold()) for pattern in sensitive)
        and not any(_matches(path.casefold(), pattern.casefold()) for pattern in approved)
    )


def history_relation(root: Path, upstream: str) -> str:
    head = git(root, "rev-parse", "HEAD").stdout.decode("ascii").strip()
    upstream_sha = git(root, "rev-parse", upstream).stdout.decode("ascii").strip()
    if not HEX_SHA.fullmatch(head) or not HEX_SHA.fullmatch(upstream_sha):
        raise ReadinessError("invalid-history-identity")
    if head == upstream_sha:
        return "equal"
    upstream_is_ancestor = git(root, "merge-base", "--is-ancestor", upstream, "HEAD", check=False).returncode == 0
    head_is_ancestor = git(root, "merge-base", "--is-ancestor", "HEAD", upstream, check=False).returncode == 0
    if upstream_is_ancestor:
        return "ahead"
    if head_is_ancestor:
        return "behind"
    return "diverged"


def test_selection(paths: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for group in config["testGroups"]:
        matches = sorted(
            path for path in paths if any(_matches(path, pattern) for pattern in group["patterns"])
        )
        if matches:
            selected.append({
                "id": group["id"],
                "matchedPaths": matches,
                "commands": list(group["commands"]),
            })
    return selected


def verify_commit_receipt(root: Path) -> None:
    spec = importlib.util.spec_from_file_location("haven42_precommit", PRECOMMIT_PATH)
    if not spec or not spec.loader:
        raise ReadinessError("precommit-verifier-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.verify(root)
    except module.ReadinessError as error:
        raise ReadinessError(f"exact-tree-receipt:{error}") from error


def evaluate(root: Path, config_path: Path, mode: str) -> dict[str, Any]:
    root = root.resolve()
    config = validate_config(load_json_strict(config_path))
    actual_root = Path(git(root, "rev-parse", "--show-toplevel").stdout.decode("utf-8").strip()).resolve()
    if actual_root != root or root.name.casefold() != "haven-42":
        raise ReadinessError("wrong-repository-root")
    remote = git(root, "remote", "get-url", "origin").stdout.decode("utf-8").strip()
    if normalize_remote(remote) != config["repository"]:
        raise ReadinessError("wrong-origin-repository")
    branch_result = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch_result.returncode != 0:
        raise ReadinessError("detached-head")
    branch = branch_result.stdout.decode("utf-8").strip()
    if not branch or branch == config["defaultBranch"]:
        raise ReadinessError("feature-branch-required")
    relation = history_relation(root, config["upstreamRef"])
    if relation in {"behind", "diverged"}:
        raise ReadinessError(f"history-{relation}-from-{config['upstreamRef'].replace('/', '-')}")
    sensitive_count = unexpected_ignored_sensitive(root, config)
    if sensitive_count:
        raise ReadinessError(f"unexpected-ignored-sensitive-inputs:{sensitive_count}")
    paths = changed_paths(root)
    if not paths:
        raise ReadinessError("no-local-change")
    if mode == "commit":
        verify_commit_receipt(root)
    groups = test_selection(paths, config)
    if not groups or groups[-1]["id"] != "repository-core":
        raise ReadinessError("changed-path-without-test-group")
    return {
        "schemaVersion": 1,
        "mode": mode,
        "repository": config["repository"],
        "branch": branch,
        "upstreamRef": config["upstreamRef"],
        "history": relation,
        "changedPathCount": len(paths),
        "changedPaths": paths,
        "ignoredSensitiveFindingCount": 0,
        "testGroups": groups,
        "fullGateRequiredBeforePush": True,
        "fullGate": config["fullGate"],
        "exactTreeReceiptVerified": mode == "commit",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--mode", choices=("spot", "commit"), default="spot")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = evaluate(args.root, args.config, args.mode)
    except ReadinessError as error:
        print(f"Pre-merge readiness failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"Pre-merge readiness passed in {args.mode} mode for "
            f"{report['changedPathCount']} changed path(s)."
        )
        for group in report["testGroups"]:
            print(f"[{group['id']}]")
            for command in group["commands"]:
                print(f"  {command}")
        print("The Full gate remains required before push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
