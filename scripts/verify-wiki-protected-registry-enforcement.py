#!/usr/bin/env python3
"""Independently verify sampled protected strings by mutation testing.

This verifier deliberately does not reconstruct assertion-to-source bindings. It
consumes the generated registry, mutates a registered source phrase in a disposable
Git worktree, and proves that the registered test fails and then passes after restore.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-wiki-protected-registry.py"
SAMPLE_WEIGHTS = (
    ("native-assert", 3),
    ("assertIn", 2),
    ("assertRegex", 2),
    ("custom-helper", 4),
    ("powershell", 3),
    ("shell", 3),
    ("powershell-inline", 1),
    ("shell-embedded-python", 1),
    ("case-insensitive", 1),
    ("multi-source", 1),
)
SHELL_RUN_TEST = re.compile(r'^run_test\s+"(?P<name>[^"]+)"\s+(?P<function>test_[A-Za-z0-9_]+)\s*$')


@dataclass(frozen=True)
class Candidate:
    sources: tuple[str, ...]
    pattern: str
    test: str
    kind: str
    match_mode: str


@dataclass(frozen=True)
class Command:
    arguments: tuple[str, ...]
    expected_test_name: str | None


def run(
    arguments: list[str] | tuple[str, ...],
    *,
    cwd: Path,
    timeout: int = 180,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(arguments),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        detail = (completed.stdout + completed.stderr).strip()
        raise RuntimeError(f"Command failed ({completed.returncode}): {' '.join(arguments)}\n{detail}")
    return completed


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_file(root: Path, relative: str) -> Path:
    base = root.resolve()
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as error:
        raise RuntimeError(f"Registry path escaped the repository: {relative}") from error
    if not candidate.is_file():
        raise RuntimeError(f"Registry path is not a file: {relative}")
    return candidate


def repository_status(root: Path) -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout


def python_kind(binding: dict[str, object], cache: dict[str, ast.AST]) -> str | None:
    test = str(binding["test"])
    test_path, separator, _function = test.partition("::")
    if not separator or not test_path.endswith(".py"):
        return None
    tree = cache.get(test_path)
    if tree is None:
        tree = ast.parse(repository_file(ROOT, test_path).read_text(encoding="utf-8"), filename=test_path)
        cache[test_path] = tree
    line = int(binding["line"])
    nodes = [
        node
        for node in ast.walk(tree)
        if getattr(node, "lineno", line + 1) <= line <= getattr(node, "end_lineno", -1)
    ]
    calls = sorted(
        (node for node in nodes if isinstance(node, ast.Call)),
        key=lambda node: (node.end_lineno - node.lineno, node.col_offset),
    )
    for node in calls:
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"assertIn", "assertRegex"}:
            return node.func.attr
    if any(isinstance(node, ast.Assert) for node in nodes):
        return "native-assert"
    if any(isinstance(node.func, ast.Name) for node in calls):
        return "custom-helper"
    return None


def candidate_kind(binding: dict[str, object], cache: dict[str, ast.AST]) -> str | None:
    if binding.get("recordType") == "multi-source":
        return "multi-source"
    if binding.get("matchMode") == "case-insensitive":
        return "case-insensitive"
    test = str(binding["test"])
    syntax = str(binding.get("syntax", ""))
    variable = str(binding.get("variable", ""))
    if syntax.startswith("powershell-inline-"):
        return "powershell-inline"
    if syntax.startswith("shell-embedded-"):
        return "shell-embedded-python"
    if test.startswith("scripts/test-pack.ps1::"):
        if variable.startswith("inline:"):
            return "powershell-inline"
        return "powershell"
    if test.startswith("scripts/test-pack.shared.sh::"):
        if variable.startswith("embedded-python:"):
            return "shell-embedded-python"
        return "shell"
    return python_kind(binding, cache)


def mutation(pattern: str) -> str | None:
    for index in range(len(pattern) // 2, len(pattern)):
        if pattern[index].isalnum() and pattern[index].isascii():
            replacement = "x" if pattern[index].lower() != "x" else "y"
            return pattern[:index] + replacement + pattern[index + 1 :]
    for index, character in enumerate(pattern):
        if character.isalnum() and character.isascii():
            replacement = "x" if character.lower() != "x" else "y"
            return pattern[:index] + replacement + pattern[index + 1 :]
    return None


def pattern_occurrences(text: str, pattern: str, match_mode: str) -> list[tuple[int, int]]:
    flags = re.IGNORECASE if match_mode == "case-insensitive" else 0
    return [match.span() for match in re.finditer(re.escape(pattern), text, flags)]


def stable_order(candidate: Candidate) -> tuple[str, str, str]:
    digest = hashlib.sha256(
        f"haven42-protected-registry-enforcement-v1\0{candidate.kind}\0"
        f"{candidate.test}\0{','.join(candidate.sources)}\0{candidate.pattern}".encode("utf-8")
    ).hexdigest()
    return digest, candidate.test, candidate.pattern


def select_candidates(bindings: list[dict[str, object]], sample_size: int) -> list[Candidate]:
    cache: dict[str, ast.AST] = {}
    pools: dict[str, list[Candidate]] = {kind: [] for kind, _count in SAMPLE_WEIGHTS}
    for binding in bindings:
        kind = candidate_kind(binding, cache)
        if kind not in pools:
            continue
        sources = tuple(
            str(source)
            for source in (
                binding.get("sources", [])
                if binding.get("recordType") == "multi-source"
                else [binding["source"]]
            )
        )
        pattern = str(binding["pattern"])
        mode = str(binding.get("matchMode", "case-sensitive"))
        occurrence_count = sum(
            len(pattern_occurrences(repository_file(ROOT, source).read_text(encoding="utf-8"), pattern, mode))
            for source in sources
        )
        if occurrence_count < 1 or mutation(pattern) is None:
            continue
        pools[kind].append(Candidate(sources, pattern, str(binding["test"]), kind, mode))
    for pool in pools.values():
        pool.sort(key=stable_order)

    selected: list[Candidate] = []
    used_tests: set[str] = set()
    used_pairs: set[tuple[str, str]] = set()
    for kind, target in SAMPLE_WEIGHTS:
        pool = pools[kind]
        preferred = [item for item in pool if item.test not in used_tests]
        fallback = [item for item in pool if item.test in used_tests]
        for item in [*preferred, *fallback]:
            key = ("\0".join(item.sources), item.pattern)
            if key in used_pairs:
                continue
            selected.append(item)
            used_tests.add(item.test)
            used_pairs.add(key)
            if sum(candidate.kind == kind for candidate in selected) >= target:
                break

    remaining = sorted(
        (
            item
            for pool in pools.values()
            for item in pool
            if ("\0".join(item.sources), item.pattern) not in used_pairs
        ),
        key=stable_order,
    )
    for item in remaining:
        if len(selected) >= sample_size:
            break
        selected.append(item)
        used_pairs.add(("\0".join(item.sources), item.pattern))

    selected = selected[:sample_size]
    missing = [
        kind
        for kind, _target in SAMPLE_WEIGHTS
        if pools[kind] and not any(item.kind == kind for item in selected)
    ]
    if len(selected) != sample_size or missing:
        raise RuntimeError(
            f"Could not build the requested {sample_size}-binding stratified sample; "
            f"selected {len(selected)}, missing categories: {', '.join(missing) or 'none'}."
        )
    inventory = ", ".join(f"{kind}={len(pools[kind])}" for kind, _target in SAMPLE_WEIGHTS)
    print(f"Eligible binding inventory: {inventory}")
    return selected


def shell_test_names(path: Path) -> dict[str, str]:
    results: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SHELL_RUN_TEST.match(line.strip())
        if match:
            results[match.group("function")] = match.group("name")
    return results


def test_command(candidate: Candidate, worktree: Path, shell_names: dict[str, str]) -> Command:
    test_path, _separator, test_name = candidate.test.partition("::")
    if test_path == "scripts/test-pack.ps1":
        return Command(
            (
                "pwsh",
                "-NoProfile",
                "-File",
                str(worktree / test_path),
                "-Tier",
                "Full",
                "-TestName",
                test_name,
                "-NoReceipt",
            ),
            test_name,
        )
    if test_path == "scripts/test-pack.shared.sh":
        display_name = shell_names.get(test_name)
        if display_name is None:
            raise RuntimeError(f"No run_test registration found for shell function {test_name}.")
        bash = shutil.which("bash")
        if bash is None:
            raise RuntimeError("bash is required to verify shell protected-string bindings.")
        return Command(
            (
                bash,
                str(worktree / test_path),
                "--tier",
                "full",
                "--test-name",
                display_name,
                "--no-receipt",
            ),
            display_name,
        )
    return Command((sys.executable, str(worktree / test_path)), None)


def verify_selected_test_ran(candidate: Candidate, command: Command, output: str) -> None:
    if candidate.test.startswith(("scripts/test-pack.ps1::", "scripts/test-pack.shared.sh::")):
        if not re.search(r"\b1 tests executed\b", output, re.IGNORECASE):
            raise RuntimeError(
                f"Selected runner did not report exactly one executed test for {candidate.test}.\n{output}"
            )


def overlay_current_files(worktree: Path, selected: list[Candidate]) -> None:
    paths = {source for candidate in selected for source in candidate.sources}
    paths.update(candidate.test.partition("::")[0] for candidate in selected)
    paths.update(
        {
            "scripts/test-pack.ps1",
            "scripts/test-pack.shared.sh",
            "scripts/ensure-test-python3.shared.sh",
        }
    )
    for relative in sorted(paths):
        source = repository_file(ROOT, relative)
        destination = repository_file(worktree, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def worktree_is_registered(path: Path) -> bool:
    completed = run(["git", "worktree", "list", "--porcelain"], cwd=ROOT, check=True)
    expected = os.path.normcase(str(path.resolve()))
    for line in completed.stdout.splitlines():
        if line.startswith("worktree "):
            registered = os.path.normcase(str(Path(line[9:]).resolve()))
            if registered == expected:
                return True
    return False


def worktree_admin_path(worktree: Path) -> Path:
    marker = (worktree / ".git").read_text(encoding="utf-8").strip()
    if not marker.startswith("gitdir: "):
        raise RuntimeError(f"Temporary worktree has an unexpected .git marker: {marker!r}")
    admin = Path(marker[8:]).resolve()
    common = run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT, check=True)
    common_directory = Path(common.stdout.strip())
    if not common_directory.is_absolute():
        common_directory = (ROOT / common_directory).resolve()
    expected_parent = (common_directory / "worktrees").resolve()
    if admin.parent != expected_parent:
        raise RuntimeError(f"Temporary worktree metadata escaped {expected_parent}: {admin}")
    return admin


def remove_read_only_tree(path: Path) -> None:
    if not path.exists():
        return

    def retry(function: object, failing_path: str, _error: object) -> None:
        os.chmod(failing_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(failing_path)

    shutil.rmtree(path, onerror=retry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-size", type=int, default=21, choices=range(21, 24))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()

    temp_root = Path(
        tempfile.mkdtemp(prefix=f"haven42-protected-registry-mutation-{os.getpid()}-{uuid.uuid4().hex[:8]}-")
    )
    worktree = temp_root / "git-worktree"
    registry_json = temp_root / "protected-registry.json"
    registry_markdown = temp_root / "protected-registry.md"
    worktree_added = False
    admin_path: Path | None = None
    cleanup_errors: list[str] = []
    original_signal_handlers: dict[int, object] = {}
    selected: list[Candidate] = []
    source_hashes: dict[str, str] = {}
    status_before = repository_status(ROOT)
    passed = 0

    def interrupt(signum: int, _frame: object) -> None:
        raise InterruptedError(f"Mutation verification interrupted by signal {signum}.")

    for signal_name in ("SIGTERM", "SIGBREAK"):
        if hasattr(signal, signal_name):
            signal_number = int(getattr(signal, signal_name))
            original_signal_handlers[signal_number] = signal.getsignal(signal_number)
            signal.signal(signal_number, interrupt)

    try:
        run(
            [
                sys.executable,
                str(GENERATOR),
                "--output",
                str(registry_markdown),
                "--json-output",
                str(registry_json),
            ],
            cwd=ROOT,
            check=True,
        )
        registry = json.loads(registry_json.read_text(encoding="utf-8"))
        bindings = [*registry["bindings"], *registry["multiSourceContracts"]]
        selected = select_candidates(bindings, args.sample_size)
        source_hashes = {
            source: sha256(repository_file(ROOT, source))
            for candidate in selected
            for source in candidate.sources
        }

        run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], cwd=ROOT, check=True)
        worktree_added = True
        admin_path = worktree_admin_path(worktree)
        overlay_current_files(worktree, selected)
        shell_names = shell_test_names(repository_file(worktree, "scripts/test-pack.shared.sh"))

        for index, candidate in enumerate(selected, start=1):
            command = test_command(candidate, worktree, shell_names)
            changed = mutation(candidate.pattern)
            if changed is None:
                raise RuntimeError(f"Selected binding is not safely mutable: {candidate}")
            originals: dict[Path, bytes] = {}
            mutations: dict[Path, bytes] = {}
            for source in candidate.sources:
                source_path = repository_file(worktree, source)
                original_text = source_path.read_text(encoding="utf-8")
                spans = pattern_occurrences(original_text, candidate.pattern, candidate.match_mode)
                if not spans:
                    continue
                originals[source_path] = source_path.read_bytes()
                for start, end in reversed(spans):
                    original_text = original_text[:start] + changed + original_text[end:]
                mutations[source_path] = original_text.encode("utf-8")
            if not mutations:
                raise RuntimeError(f"Selected binding has no mutable source occurrence: {candidate}")

            baseline = run(command.arguments, cwd=worktree, timeout=args.timeout_seconds)
            baseline_output = baseline.stdout + baseline.stderr
            verify_selected_test_ran(candidate, command, baseline_output)
            if baseline.returncode != 0:
                raise RuntimeError(f"Baseline failed for {candidate.test}.\n{baseline_output}")

            try:
                for source_path, mutated in mutations.items():
                    source_path.write_bytes(mutated)
                failed = run(command.arguments, cwd=worktree, timeout=args.timeout_seconds)
                failed_output = failed.stdout + failed.stderr
                verify_selected_test_ran(candidate, command, failed_output)
                if failed.returncode == 0:
                    raise RuntimeError(
                        f"Mutation did not fail its registered test: {candidate.test} -> "
                        f"{', '.join(candidate.sources)} / {candidate.pattern!r}"
                    )
            finally:
                for source_path, original in originals.items():
                    source_path.write_bytes(original)

            restored = run(command.arguments, cwd=worktree, timeout=args.timeout_seconds)
            restored_output = restored.stdout + restored.stderr
            verify_selected_test_ran(candidate, command, restored_output)
            if restored.returncode != 0:
                raise RuntimeError(f"Restored source did not pass for {candidate.test}.\n{restored_output}")
            passed += 1
            print(
                f"PASS {index}/{len(selected)} [{candidate.kind}] {', '.join(candidate.sources)} :: "
                f"{candidate.pattern!r} :: {candidate.test}"
            )
    finally:
        for signal_number, handler in original_signal_handlers.items():
            try:
                signal.signal(signal_number, handler)
            except Exception as error:  # pragma: no cover - platform signal restoration
                cleanup_errors.append(f"Could not restore signal handler {signal_number}: {error}")

        try:
            registered = worktree_is_registered(worktree)
        except Exception as error:
            registered = False
            cleanup_errors.append(f"Could not inspect temporary worktree registration: {error}")
        if worktree_added or registered:
            try:
                run(["git", "worktree", "remove", "--force", str(worktree)], cwd=ROOT)
            except Exception as error:
                cleanup_errors.append(f"git worktree remove could not run: {error}")
        if worktree.exists():
            try:
                remove_read_only_tree(worktree)
            except Exception as error:
                cleanup_errors.append(f"Could not remove temporary worktree directory: {error}")
        if admin_path is not None and admin_path.exists():
            try:
                remove_read_only_tree(admin_path)
            except Exception as error:
                cleanup_errors.append(f"Could not remove exact temporary worktree metadata: {error}")
        try:
            remove_read_only_tree(temp_root)
        except Exception as error:
            cleanup_errors.append(f"Could not remove temporary verification root: {error}")

        try:
            still_registered = worktree_is_registered(worktree)
        except Exception as error:
            still_registered = True
            cleanup_errors.append(f"Could not confirm temporary worktree deregistration: {error}")
        if worktree.exists() or still_registered:
            cleanup_errors.append(f"Temporary worktree still exists or is registered: {worktree}")
        if admin_path is not None and admin_path.exists():
            cleanup_errors.append(f"Temporary worktree metadata still exists: {admin_path}")
        for source, expected_hash in source_hashes.items():
            try:
                actual_hash = sha256(repository_file(ROOT, source))
                if actual_hash != expected_hash:
                    cleanup_errors.append(f"Real working-tree source changed during mutation test: {source}")
            except Exception as error:
                cleanup_errors.append(f"Could not verify real working-tree source {source}: {error}")
        try:
            if repository_status(ROOT) != status_before:
                cleanup_errors.append("Real working-tree Git status changed during mutation verification.")
        except Exception as error:
            cleanup_errors.append(f"Could not verify final real working-tree Git status: {error}")
        if cleanup_errors:
            raise RuntimeError("Mutation verifier cleanup/integrity failure:\n- " + "\n- ".join(cleanup_errors))

    print(f"Protected-string mutation enforcement passed: {passed}/{len(selected)} bindings (100.0%).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
