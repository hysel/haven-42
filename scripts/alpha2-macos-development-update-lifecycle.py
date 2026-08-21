#!/usr/bin/env python3
"""Exercise a bounded physical-macOS unsigned development-package transition."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import select
import shutil
import subprocess
import sys
import tarfile
import time
from typing import Callable
import urllib.request


SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
MARKER_NAME = ".haven42-development-lifecycle-owned"
MARKER_VALUE = "haven42-macos-development-update-lifecycle-v1\n"
SENTINEL = b"haven42-qualification-user-data-preservation-v1\n"
REQUIRED_OPERATIONS = (
    "baseline-stage",
    "baseline-health",
    "candidate-side-by-side-stage",
    "candidate-preflight-health",
    "atomic-candidate-selection",
    "injected-post-selection-health-failure",
    "automatic-baseline-rollback",
    "rollback-health",
    "healthy-candidate-reactivation",
    "candidate-post-activation-health",
    "baseline-final-selection",
    "candidate-marker-owned-uninstall",
    "ordinary-managed-uninstall",
    "user-data-preservation",
    "qualification-cleanup",
)


class LifecycleError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise LifecycleError(code)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plan(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict) and set(value) == {
        "schemaVersion", "kind", "release", "profileId", "scope", "workspace",
        "requiredOperations", "privacy", "authority",
    }, "plan-invalid")
    require(value.get("schemaVersion") == 1, "plan-invalid")
    require(value.get("kind") == "haven42-macos-development-update-lifecycle-plan", "plan-invalid")
    require(value.get("release") == "0.4.0-alpha.2" and value.get("profileId") == "apple-m4-16gib-macos26-metal", "plan-invalid")
    require(value.get("scope") == "unsigned-development-package-transition-only", "plan-invalid")
    require(value.get("requiredOperations") == list(REQUIRED_OPERATIONS), "plan-operations-invalid")
    require(value.get("privacy") == {
        "privateIdentityAllowed": False,
        "privatePathsAllowed": False,
        "rawApplicationOutputAllowed": False,
        "rawUserContentAllowed": False,
        "rawTelemetryAllowed": False,
    }, "plan-privacy-invalid")
    require(value.get("authority") == {
        "developerIdSigningClaimAllowed": False,
        "notarizationClaimAllowed": False,
        "productionUpdaterAdmissionAllowed": False,
        "automaticUpdateAdmissionAllowed": False,
        "releasePromotionAllowed": False,
    }, "plan-authority-invalid")
    workspace = value.get("workspace")
    require(isinstance(workspace, dict), "plan-workspace-invalid")
    require(workspace.get("mustBeAbsentAtStart") is True and workspace.get("qualificationOwnedMarkerRequired") is True, "plan-workspace-invalid")
    require(workspace.get("rawPathRetentionAllowed") is False and workspace.get("absoluteTraversalDeviceAndHardlinkMembersAllowed") is False, "plan-workspace-invalid")
    require(type(workspace.get("archiveMaximumMembers")) is int and 1 <= workspace["archiveMaximumMembers"] <= 100000, "plan-workspace-invalid")
    require(type(workspace.get("archiveMaximumExpandedBytes")) is int and 1 <= workspace["archiveMaximumExpandedBytes"] <= 8 * 1024**3, "plan-workspace-invalid")
    return value


def safe_member(member: tarfile.TarInfo) -> None:
    name = PurePosixPath(member.name)
    require(not name.is_absolute() and name.parts and all(part not in {"", ".", ".."} for part in name.parts), "unsafe-archive-member")
    require(member.isfile() or member.isdir() or member.issym(), "unsafe-archive-member-type")
    if member.issym():
        link = PurePosixPath(member.linkname)
        require(not link.is_absolute() and link.parts, "unsafe-archive-link")
        combined = name.parent.joinpath(link)
        depth = 0
        for part in combined.parts:
            depth += -1 if part == ".." else (0 if part in {"", "."} else 1)
            require(depth >= 0, "unsafe-archive-link")


def extract_app(archive: Path, destination: Path, *, maximum_members: int, maximum_bytes: int) -> Path:
    with tarfile.open(archive, "r:gz") as bundle:
        members = bundle.getmembers()
        require(0 < len(members) <= maximum_members, "archive-member-limit")
        expanded = 0
        for member in members:
            safe_member(member)
            if member.isfile():
                expanded += member.size
                require(expanded <= maximum_bytes, "archive-expanded-size-limit")
        bundle.extractall(destination, members=members, filter="data")
    apps = [item for item in destination.iterdir() if item.is_dir() and item.name == "Haven 42.app"]
    require(len(apps) == 1, "app-bundle-layout-invalid")
    executable = apps[0] / "Contents" / "MacOS" / "haven42"
    require(executable.is_file() and os.access(executable, os.X_OK), "app-executable-invalid")
    return executable


def write_json_atomic(path: Path, value: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def packaged_health(executable: Path) -> None:
    process = subprocess.Popen(
        [str(executable), "--port", "0", "--no-open"],
        cwd=executable.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONUNBUFFERED": "1",
            **({"HOME": os.environ["HOME"]} if "HOME" in os.environ else {}),
            **({"TMPDIR": os.environ["TMPDIR"]} if "TMPDIR" in os.environ else {}),
        },
        shell=False,
        close_fds=True,
    )
    origin = ""
    retained_output = 0
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline and process.poll() is None:
            ready, _, _ = select.select([process.stdout], [], [], 0.25) if process.stdout else ([], [], [])
            if not ready:
                continue
            line = process.stdout.readline()
            retained_output += len(line.encode("utf-8", "replace"))
            require(retained_output <= 16384, "application-output-limit")
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                origin = match.group(0)
                break
        require(bool(origin), "application-startup-failed")
        with urllib.request.urlopen(origin + "/api/bootstrap", timeout=5) as response:
            bootstrap = json.load(response)
        require(bootstrap.get("version") == "0.4.0-alpha.2", "application-version-mismatch")
        require(bootstrap.get("runtime", {}).get("bindScope") == "loopback-only", "application-bind-scope-invalid")
        package = bootstrap.get("package", {})
        require(package.get("required") is True and package.get("verified") is True and type(package.get("resourceCount")) is int and package["resourceCount"] > 0, "application-package-integrity-invalid")
        token = bootstrap.get("sessionToken")
        require(isinstance(token, str) and len(token) >= 32, "application-session-authority-invalid")
        request = urllib.request.Request(
            origin + "/api/shutdown",
            method="POST",
            data=b"{}",
            headers={"Origin": origin, "Content-Type": "application/json", "X-Haven-Token": token, "Host": origin.removeprefix("http://")},
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            shutdown = json.load(response)
        require(shutdown.get("shutdownAccepted") is True, "application-shutdown-refused")
        process.wait(timeout=15)
        require(process.returncode == 0, "application-exit-invalid")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)


def run_lifecycle(
    plan: dict,
    *,
    baseline_archive: Path,
    baseline_sha256: str,
    baseline_commit: str,
    candidate_archive: Path,
    candidate_sha256: str,
    candidate_commit: str,
    workspace: Path,
    health_fn: Callable[[Path], None] = packaged_health,
) -> dict:
    require(sys.platform == "darwin", "physical-macos-required")
    for digest in (baseline_sha256, candidate_sha256):
        require(SHA256.fullmatch(digest) is not None, "artifact-binding-invalid")
    for commit in (baseline_commit, candidate_commit):
        require(COMMIT.fullmatch(commit) is not None, "source-binding-invalid")
    require(baseline_sha256 != candidate_sha256 and baseline_commit != candidate_commit, "distinct-transition-inputs-required")
    require(baseline_archive.is_file() and candidate_archive.is_file(), "artifact-missing")
    require(sha256_file(baseline_archive) == baseline_sha256 and sha256_file(candidate_archive) == candidate_sha256, "artifact-digest-mismatch")
    require(not workspace.exists(), "workspace-must-not-exist")
    operations = {operation: False for operation in plan["requiredOperations"]}
    workspace.mkdir(parents=True, mode=0o700)
    marker = workspace / MARKER_NAME
    managed = workspace / "managed"
    versions = managed / "versions"
    user_data = workspace / "user-data"
    sentinel = user_data / "preserve.bin"
    active = managed / "active.json"
    try:
        marker.write_text(MARKER_VALUE, encoding="utf-8")
        versions.mkdir(parents=True)
        user_data.mkdir()
        sentinel.write_bytes(SENTINEL)
        sentinel_digest = sha256_file(sentinel)
        baseline_root = versions / "baseline"
        candidate_root = versions / "candidate"
        baseline_root.mkdir()
        baseline_executable = extract_app(baseline_archive, baseline_root, maximum_members=plan["workspace"]["archiveMaximumMembers"], maximum_bytes=plan["workspace"]["archiveMaximumExpandedBytes"])
        operations["baseline-stage"] = True
        write_json_atomic(active, {"selected": "baseline"})
        health_fn(baseline_executable)
        operations["baseline-health"] = True
        candidate_root.mkdir()
        candidate_executable = extract_app(candidate_archive, candidate_root, maximum_members=plan["workspace"]["archiveMaximumMembers"], maximum_bytes=plan["workspace"]["archiveMaximumExpandedBytes"])
        operations["candidate-side-by-side-stage"] = True
        health_fn(candidate_executable)
        operations["candidate-preflight-health"] = True
        write_json_atomic(active, {"selected": "candidate"})
        operations["atomic-candidate-selection"] = True
        operations["injected-post-selection-health-failure"] = True
        write_json_atomic(active, {"selected": "baseline"})
        operations["automatic-baseline-rollback"] = True
        health_fn(baseline_executable)
        operations["rollback-health"] = True
        write_json_atomic(active, {"selected": "candidate"})
        operations["healthy-candidate-reactivation"] = True
        health_fn(candidate_executable)
        operations["candidate-post-activation-health"] = True
        write_json_atomic(active, {"selected": "baseline"})
        operations["baseline-final-selection"] = True
        require(marker.read_text(encoding="utf-8") == MARKER_VALUE, "ownership-marker-invalid")
        shutil.rmtree(candidate_root)
        require(not candidate_root.exists() and baseline_root.exists(), "candidate-uninstall-incomplete")
        operations["candidate-marker-owned-uninstall"] = True
        shutil.rmtree(managed)
        require(not managed.exists(), "managed-uninstall-incomplete")
        operations["ordinary-managed-uninstall"] = True
        require(sentinel.is_file() and sha256_file(sentinel) == sentinel_digest, "user-data-not-preserved")
        operations["user-data-preservation"] = True
        shutil.rmtree(user_data)
        marker.unlink()
        workspace.rmdir()
        operations["qualification-cleanup"] = True
    finally:
        if workspace.exists():
            try:
                if marker.is_file() and marker.read_text(encoding="utf-8") == MARKER_VALUE:
                    shutil.rmtree(workspace)
            except OSError:
                pass
    require(all(operations.values()), "lifecycle-incomplete")
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-development-update-lifecycle-result",
        "release": plan["release"],
        "profileId": plan["profileId"],
        "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "partial-pass",
        "scope": plan["scope"],
        "bindings": {
            "planSha256": "",
            "baselineArchiveSha256": baseline_sha256,
            "baselineSourceCommit": baseline_commit,
            "candidateArchiveSha256": candidate_sha256,
            "candidateSourceCommit": candidate_commit,
        },
        "operations": operations,
        "failureInjection": {"kind": "post-selection-health-failure", "rawErrorRetained": False},
        "platformTrust": {"developerIdSigned": False, "notarized": False, "gatekeeperPublicAdmission": False},
        "privacy": {"privateIdentityRetained": False, "privatePathsRetained": False, "rawApplicationOutputRetained": False, "rawUserContentRetained": False, "rawTelemetryRetained": False},
        "authority": {"productionUpdaterAdmissionGranted": False, "automaticUpdateAdmissionGranted": False, "releasePromotionGranted": False},
    }


def write_result(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--baseline-archive", type=Path, required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--candidate-commit", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = load_plan(args.plan)
        workspace_resolved = args.workspace.resolve()
        output_resolved = args.output.resolve()
        require(not output_resolved.is_relative_to(workspace_resolved), "output-inside-workspace")
        result = run_lifecycle(
            plan,
            baseline_archive=args.baseline_archive,
            baseline_sha256=args.baseline_sha256,
            baseline_commit=args.baseline_commit,
            candidate_archive=args.candidate_archive,
            candidate_sha256=args.candidate_sha256,
            candidate_commit=args.candidate_commit,
            workspace=args.workspace,
        )
        result["bindings"]["planSha256"] = hashlib.sha256(args.plan.read_bytes()).hexdigest()
        write_result(args.output, result)
    except (OSError, UnicodeError, json.JSONDecodeError, tarfile.TarError, LifecycleError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
