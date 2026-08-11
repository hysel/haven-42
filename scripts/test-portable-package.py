#!/usr/bin/env python3
"""Source/packaged parity and native one-folder smoke test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import os
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent.parent


def remove_test_diagnostics(parent: Path) -> None:
    root = parent / "Haven42-Logs"
    if not root.exists():
        return
    from diagnostic_logging import DiagnosticLogger
    logger = DiagnosticLogger("0.4.0-alpha.1", root)
    logger.remove_all()
    logger.close()


def request(url: str, method: str = "GET", token: str = "", body: bytes | None = None):
    parsed = urllib.parse.urlsplit(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    headers = {"Host": parsed.netloc}
    if method == "POST":
        headers.update({
            "Origin": origin,
            "Content-Type": "application/json",
            "X-Haven-Token": token,
        })
    return urllib.request.urlopen(
        urllib.request.Request(url, method=method, data=body, headers=headers),
        timeout=5,
    )


def launch(
    command: list[str],
    cwd: Path = ROOT,
    environment: dict[str, str] | None = None,
) -> tuple[subprocess.Popen[str], str]:
    process = subprocess.Popen(
        command + ["--port", "0", "--no-open"],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={
            **os.environ,
            "PYTHONUNBUFFERED": "1",
            **(environment or {}),
        },
    )
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        line = process.stdout.readline() if process.stdout else ""
        match = re.search(r"http://127\.0\.0\.1:\d+", line)
        if match:
            return process, match.group(0)
        if process.poll() is not None:
            raise AssertionError(f"runtime exited early: {line}")
    process.kill()
    raise AssertionError("runtime did not announce its loopback URL")


def expect_http_error(
    url: str,
    headers: dict[str, str],
    body: bytes,
    expected_status: int,
    expected_code: str,
) -> None:
    try:
        urllib.request.urlopen(
            urllib.request.Request(url, method="POST", data=body, headers=headers),
            timeout=5,
        )
    except urllib.error.HTTPError as error:
        assert error.code == expected_status
        assert json.load(error)["error"] == expected_code
        return
    raise AssertionError(f"request unexpectedly succeeded: {expected_code}")


def probe(
    command: list[str],
    packaged: bool,
    cwd: Path = ROOT,
    environment: dict[str, str] | None = None,
) -> dict:
    process, origin = launch(command, cwd, environment)
    try:
        with request(origin + "/api/bootstrap") as response:
            bootstrap = json.load(response)
            assert response.headers["X-Frame-Options"] == "DENY"
            assert "default-src 'self'" in response.headers["Content-Security-Policy"]
        with request(origin + "/app.js") as response:
            app_digest = __import__("hashlib").sha256(response.read()).hexdigest()
        with request(origin + "/accessibility") as response:
            accessibility_bytes = response.read()
            assert response.headers["Content-Type"] == "text/html; charset=utf-8"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert b"(WCAG) 2.1 Level AA" in accessibility_bytes
            assert b"not a claim of third-party certification" in accessibility_bytes
            accessibility_digest = __import__("hashlib").sha256(accessibility_bytes).hexdigest()
        try:
            urllib.request.urlopen(origin.replace("127.0.0.1", "localhost") + "/api/bootstrap", timeout=5)
            raise AssertionError("alternate Host was accepted")
        except urllib.error.HTTPError as error:
            assert error.code == 403
        assert bootstrap["runtime"]["bindScope"] == "loopback-only"
        assert bootstrap["updates"]["activationAllowed"] is False
        assert bootstrap["package"]["required"] is packaged
        assert bootstrap["package"]["verified"] is packaged
        linux_alpha = bootstrap["runtime"]["platform"] == "linux"
        expected_version = "0.4.0-alpha.2" if linux_alpha else "0.4.0-alpha.1"
        assert bootstrap["version"] == expected_version
        assert bootstrap["alpha"] == {
            "label": "Haven 42 0.4 Alpha 2" if linux_alpha else "Haven 42 0.4 Alpha 1",
            "windowsOnly": not linux_alpha,
            "chatOnly": False,
            "textOnly": True,
            "unsigned": True,
            "productionReady": False,
            "managedSetupRuntimeAdmitted": False,
            "managedSetupCandidateAvailable": bootstrap["runtime"]["platform"] in {"windows", "linux"},
            "managedSetupCompletedCandidate": False,
        }
        token = bootstrap.pop("sessionToken")
        authority = {
            "Origin": origin,
            "Content-Type": "application/json",
            "X-Haven-Token": token,
        }
        with request(
            origin + "/api/readiness", "POST", token, b'{"force":true}',
        ) as response:
            readiness = json.load(response)
            assert readiness["kind"] == "system-readiness"
            assert readiness["effects"] == {
                "networkUsed": False,
                "filesWritten": False,
                "installationPerformed": False,
                "elevationRequested": False,
                "servicesChanged": False,
                "driversChanged": False,
            }
        with request(
            origin + "/api/assurance", "POST", token, b"{}",
        ) as response:
            assurance = json.load(response)
            assert assurance["kind"] == "read-only-assurance-summary"
            assert assurance["status"] == "ready"
            assert assurance["sources"] == {
                "evidenceCatalog": "config/evidence-catalog.tsv",
                "surfaceMatrix": "config/agent-surface-capabilities.json",
                "surfaceSolutions": "config/agent-surface-solutions.json",
            }
            assert assurance["evidence"]["recordCount"] >= 1
            assert assurance["surfaces"]
            assert all(value is False for value in assurance["effects"].values())
        plan_body = json.dumps({
            "snapshotId": readiness["snapshotId"],
            "intent": "guided-setup",
        }).encode("utf-8")
        try:
            setup_response = request(
                origin + "/api/setup-plan", "POST", token, plan_body,
            )
        except urllib.error.HTTPError as error:
            detail = error.read(4096).decode("utf-8", errors="replace")
            raise AssertionError(
                f"setup-plan returned HTTP {error.code}: {detail}"
            ) from error
        with setup_response as response:
            plan = json.load(response)
            assert plan["kind"] == "setup-plan"
            assert len(plan["actions"]) >= 2
            assert plan["installationAllowed"] is False
            assert all(action["installControl"] == "disabled" for action in plan["actions"])
            alpha_plan = plan["alphaCandidate"]
            assert alpha_plan["version"] == expected_version
            assert alpha_plan["quantizationDecision"] == "use-pinned-prequantized-model"
            assert alpha_plan["managedSetupRuntimeAdmitted"] is False
            automatic_allowed = alpha_plan["modelSelection"]["automaticExecutionAllowed"] is True
            managed = alpha_plan.get("managedPlan")
            expected_managed = bootstrap["runtime"]["platform"] in {"windows", "linux"} and automatic_allowed
            assert alpha_plan["managedSetupCandidateAvailable"] is expected_managed
            if expected_managed:
                assert managed is not None
                assert managed["kind"] == (
                    "linux-alpha-setup-plan" if linux_alpha else "windows-alpha-setup-plan"
                )
                assert managed["effects"] == [
                    "network-download", "portable-folder-files", "owned-process",
                    "local-model-validation",
                ]
                assert managed["backendMode"] in {"cpu", "cuda", "rocm", "vulkan"}
                assert isinstance(managed["gpuAccelerationRequired"], bool)
                assert (
                    isinstance(managed["requiredStorageBytes"], int)
                    and not isinstance(managed["requiredStorageBytes"], bool)
                    and managed["requiredStorageBytes"] > 0
                )
                selected_storage = alpha_plan["modelSelection"]["selected"]["requiredStorageGiB"]
                assert isinstance(selected_storage, (int, float)) and selected_storage > 0
                assert managed["requiredStorageBytes"] <= int(selected_storage * (1024 ** 3))
                renderer_plan = json.dumps(managed, sort_keys=True)
                assert "http://" not in renderer_plan and "https://" not in renderer_plan
                assert "ollama.exe" not in renderer_plan and "\\\\" not in renderer_plan
            else:
                assert managed is None
        with request(origin + "/api/alpha/resources") as response:
            resources = json.load(response)
            assert resources["kind"] == (
                "linux-alpha-local-metrics" if linux_alpha else "windows-alpha-local-metrics"
            )
            assert resources["persisted"] is False
            assert resources["externalTelemetryUsed"] is False
            assert resources["sample"]["persisted"] is False
            assert resources["sample"]["externalTelemetryUsed"] is False
            assert resources["sessionTokens"]["persisted"] is False
        with request(
            origin + "/api/alpha/diagnostics", "POST", token, b"{}",
        ) as response:
            diagnostics = json.load(response)
            assert diagnostics["kind"] == "haven42-sanitized-diagnostics"
            assert diagnostics["storageDirectoryName"] == "Haven42-Logs"
            assert diagnostics["storageScope"] == "inside-extracted-folder"
            assert diagnostics["removedForSession"] is False
            assert all(value is False for value in diagnostics["privacy"].values())
            assert all(set(event) == {
                "schemaVersion", "timestamp", "eventId", "category", "code", "outcome", "appVersion",
            } for event in diagnostics["events"])
            if expected_managed:
                diagnostic_codes = {event["code"] for event in diagnostics["events"]}
                assert (
                    f"SETUP_BACKEND_{managed['backendMode'].upper()}_SELECTED"
                    in diagnostic_codes
                )
                assert len([
                    code for code in diagnostic_codes
                    if code.startswith("SETUP_COMPONENT_") and code.endswith("_SELECTED")
                ]) == len(managed["components"])
                assert len([
                    code for code in diagnostic_codes
                    if code.startswith("SETUP_MODEL_") and code.endswith("_SELECTED")
                ]) == 1
        expect_http_error(
            origin + "/api/workflows",
            authority,
            b"{}",
            404,
            "alpha-text-only",
        )
        if bootstrap["runtime"]["platform"] in {"windows", "linux"}:
            with request(origin + "/api/alpha/setup-status") as response:
                setup_status = json.load(response)
                assert setup_status["phase"] == "idle"
                assert setup_status["planId"] == (managed["planId"] if managed else None)
                assert setup_status["driverChanges"] is False
                assert setup_status["serviceChanges"] is False
                assert setup_status["firewallChanges"] is False
                assert setup_status["elevationRequested"] is False
            rejected_approval = json.dumps({
                "planId": setup_status["planId"] or ("0" * 32),
                "effects": ["driver-install"],
                "confirmed": True,
            }).encode("utf-8")
            expect_http_error(
                origin + "/api/alpha/setup-approve",
                authority,
                rejected_approval,
                409,
                "approval-does-not-match-plan",
            )
            with request(origin + "/api/alpha/setup-status") as response:
                assert json.load(response)["phase"] == "idle"
        expect_http_error(
            origin + "/api/shutdown",
            {"Origin": origin, "Content-Type": "application/json"},
            b"{}",
            403,
            "invalid-session-token",
        )
        expect_http_error(
            origin + "/api/shutdown",
            {**authority, "Origin": "http://127.0.0.1:1"},
            b"{}",
            403,
            "invalid-origin",
        )
        expect_http_error(
            origin + "/api/shutdown",
            {**authority, "Content-Type": "text/plain"},
            b"{}",
            415,
            "json-content-type-required",
        )
        expect_http_error(
            origin + "/api/shutdown",
            authority,
            b'{"unexpected":true}',
            400,
            "invalid-shutdown-fields",
        )
        with request(origin + "/api/bootstrap") as response:
            assert response.status == 200
        if diagnostics["available"]:
            with request(
                origin + "/api/alpha/diagnostics/remove", "POST", token, b'{"confirmed":true}',
            ) as response:
                assert json.load(response) == {
                    "removed": True, "directoryName": "Haven42-Logs",
                }
        with request(
            origin + "/api/shutdown", "POST", token, b"{}",
        ) as response:
            assert json.load(response) == {
                "shutdownAccepted": True, "modelCleanupVerified": True,
            }
        process.wait(timeout=10)
        assert process.returncode == 0
        return {
            "capabilities": bootstrap["capabilities"],
            "updates": bootstrap["updates"],
            "privacy": bootstrap["privacy"],
            "appDigest": app_digest,
            "accessibilityDigest": accessibility_digest,
            "assurance": assurance,
        }
    finally:
        if process.poll() is None:
            process.kill()


def assert_integrity_failure(executable: Path, mutate) -> None:
    package_dir = executable.parent
    with tempfile.TemporaryDirectory(prefix="haven42-hostile-package-") as temporary:
        copied = Path(temporary) / "haven42"
        shutil.copytree(package_dir, copied)
        copied_executable = copied / executable.name
        internal = copied / "_internal"
        mutate(internal)
        result = subprocess.run(
            [str(copied_executable), "--port", "0", "--no-open"],
            cwd=copied,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode != 0
        assert "Packaged resource integrity verification failed." in (result.stdout + result.stderr)


def test_hostile_packages(executable: Path) -> None:
    assert_integrity_failure(
        executable,
        lambda root: (root / "web/static/app.js").write_text("tampered", encoding="utf-8"),
    )
    assert_integrity_failure(
        executable,
        lambda root: (root / "web/static/styles.css").unlink(),
    )
    assert_integrity_failure(
        executable,
        lambda root: (root / "config/unexpected.json").write_text("{}", encoding="utf-8"),
    )

    def traversal(root: Path) -> None:
        path = root / "package/resource-integrity.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["resources"][0]["path"] = "../escape"
        path.write_text(json.dumps(value), encoding="utf-8")

    assert_integrity_failure(executable, traversal)

    def duplicate(root: Path) -> None:
        path = root / "package/resource-integrity.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["resources"].append(dict(value["resources"][0]))
        path.write_text(json.dumps(value), encoding="utf-8")

    assert_integrity_failure(executable, duplicate)

    def absolute(root: Path) -> None:
        path = root / "package/resource-integrity.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["resources"][0]["path"] = str((root / "web/static/app.js").resolve())
        path.write_text(json.dumps(value), encoding="utf-8")

    assert_integrity_failure(executable, absolute)

    if hasattr(os, "symlink"):
        def symlink(root: Path) -> None:
            target = root / "web/static/app.js"
            outside = root.parent / "external-app.js"
            outside.write_bytes(target.read_bytes())
            target.unlink()
            target.symlink_to(outside)

        try:
            assert_integrity_failure(executable, symlink)
        except OSError:
            # Unprivileged Windows runners may not permit symlink creation.
            pass


def test_relocation_and_hostile_environment(executable: Path, expected: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="haven42-relocated-package-") as temporary:
        relocated = Path(temporary) / "directory with spaces" / "haven42"
        shutil.copytree(executable.parent, relocated)
        relocated_executable = relocated / executable.name
        actual = probe(
            [str(relocated_executable)],
            True,
            cwd=Path(temporary),
            environment={
                "PYTHONPATH": str(Path(temporary) / "untrusted-python"),
                "HTTP_PROXY": "http://127.0.0.1:1",
                "HTTPS_PROXY": "http://127.0.0.1:1",
                "NO_PROXY": "",
                "BROWSER": "untrusted-browser-command",
            },
        )
        assert actual == expected


def restore_writable(root: Path) -> None:
    for path in [root, *root.rglob("*")]:
        try:
            path.chmod(path.stat().st_mode | stat.S_IWUSR)
        except OSError:
            pass


def test_read_only_package(executable: Path, expected: dict) -> None:
    with tempfile.TemporaryDirectory(prefix="haven42-read-only-package-") as temporary:
        copied = Path(temporary) / "haven42"
        shutil.copytree(executable.parent, copied)
        copied_executable = copied / executable.name
        try:
            for path in copied.rglob("*"):
                mode = path.stat().st_mode
                if path.is_dir():
                    path.chmod(mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
                else:
                    path.chmod(mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
            copied.chmod(copied.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
            assert probe([str(copied_executable)], True, cwd=copied) == expected
        finally:
            restore_writable(copied)


def test_abrupt_exit_recovery(executable: Path, expected: dict) -> None:
    process, origin = launch([str(executable)], executable.parent)
    try:
        with request(origin + "/api/bootstrap") as response:
            assert json.load(response)["package"]["verified"] is True
        process.kill()
        process.wait(timeout=10)
        assert process.returncode != 0
    finally:
        if process.poll() is None:
            process.kill()
    assert probe([str(executable)], True, cwd=executable.parent) == expected


def test_port_collision(command: list[str]) -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    try:
        result = subprocess.run(
            command + ["--port", str(port), "--no-open"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode != 0
        assert "Could not start Haven 42 local web server" in (result.stdout + result.stderr)
    finally:
        listener.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    args = parser.parse_args()
    source = probe([
        sys.executable,
        str(ROOT / "scripts/run-haven42-web-browser-test.py"),
    ], False)
    executable = Path(args.executable).resolve()
    packaged = probe([str(executable)], True)
    assert source == packaged, "source and packaged behavior diverged"
    assert probe([str(executable)], True) == packaged
    test_relocation_and_hostile_environment(executable, packaged)
    test_read_only_package(executable, packaged)
    test_abrupt_exit_recovery(executable, packaged)
    test_port_collision([str(executable)])
    test_hostile_packages(executable)
    remove_test_diagnostics(executable.parent)
    print(
        "Portable package parity, relocation, read-only startup, abrupt-exit recovery, "
        "repeated lifecycle, port collision, shutdown authority, hostile environment, "
        "and integrity tests passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
