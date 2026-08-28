#!/usr/bin/env python3
"""Validate one exact Linux Alpha 2 package through its loopback API.

Plan-only is the default.  ``--apply-managed-setup`` consumes the package's
single-use approval and may download the admitted Ollama runtime and model.
The emitted result is sanitized and never contains a host name, user name,
address, local path, prompt, response, approval token, or plan identifier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


EXPECTED_VERSION = "0.4.0-alpha.2"
TERMINAL_PHASES = {"complete", "failed", "cancelled"}


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def request_json(
    origin: str,
    path: str,
    *,
    token: str = "",
    body: dict | None = None,
    timeout: int = 30,
) -> dict:
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Host": urllib.parse.urlsplit(origin).netloc}
    if body is not None:
        headers.update({"Origin": origin, "Content-Type": "application/json"})
    if token:
        headers["X-Haven-Token"] = token
    with urllib.request.urlopen(
        urllib.request.Request(origin + path, data=data, headers=headers),
        timeout=timeout,
    ) as response:
        value = json.load(response)
    require(isinstance(value, dict), "response-not-an-object")
    return value


def launch(executable: Path) -> tuple[subprocess.Popen[str], str]:
    process = subprocess.Popen(
        [str(executable), "--port", "0", "--no-open"],
        cwd=executable.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    deadline = time.monotonic() + 30
    require(process.stdout is not None, "runtime-output-unavailable")
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("runtime-exited-before-loopback-ready")
            remaining = max(0.0, deadline - time.monotonic())
            if not selector.select(timeout=min(0.5, remaining)):
                continue
            line = process.stdout.readline()
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                return process, match.group(0)
    process.kill()
    process.wait(timeout=10)
    raise RuntimeError("runtime-loopback-announcement-timeout")


def package_sha256(executable: Path) -> str:
    digest = hashlib.sha256()
    with executable.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--apply-managed-setup", action="store_true")
    parser.add_argument("--require-managed-setup", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=7200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve()
    require(executable.is_file(), "package-executable-missing")
    require(platform.system() == "Linux", "native-linux-required")
    require(platform.machine() in {"x86_64", "AMD64"}, "native-x64-required")
    require(60 <= args.timeout_seconds <= 14400, "timeout-out-of-range")

    process, origin = launch(executable)
    result: dict = {
        "schemaVersion": 1,
        "kind": "haven42-alpha2-linux-native-package-validation",
        "release": EXPECTED_VERSION,
        "packageExecutableSha256": package_sha256(executable),
        "platform": {"operatingSystem": "Linux", "architecture": "x86_64"},
        "packageIntegrityVerified": False,
        "readinessNoEffectVerified": False,
        "managedSetupPlanned": False,
        "managedSetupApplied": False,
        "managedSetupCompleted": False,
        "managedProviderConnected": False,
        "capabilityResults": [],
        "modelUnloadVerified": False,
        "shutdownVerified": False,
        "productionReady": False,
        "publicationAuthorized": False,
    }
    token = ""
    shutdown_requested = False
    try:
        bootstrap = request_json(origin, "/api/bootstrap")
        token = bootstrap.pop("sessionToken")
        require(bootstrap.get("version") == EXPECTED_VERSION, "release-mismatch")
        require(bootstrap.get("runtime", {}).get("bindScope") == "loopback-only", "non-loopback-bind")
        package = bootstrap.get("package", {})
        require(
            package.get("required") is True and package.get("verified") is True,
            "package-integrity-unverified",
        )
        alpha = bootstrap.get("alpha", {})
        require(alpha.get("unsigned") is True and alpha.get("productionReady") is False, "alpha-label-invalid")
        result["packageIntegrityVerified"] = True

        readiness = request_json(
            origin, "/api/readiness", token=token, body={"force": True}, timeout=60,
        )
        effects = readiness.get("effects", {})
        require(effects and all(value is False for value in effects.values()), "readiness-had-effects")
        result["readinessNoEffectVerified"] = True

        plan = request_json(
            origin,
            "/api/setup-plan",
            token=token,
            body={"snapshotId": readiness.get("snapshotId"), "intent": "guided-setup"},
            timeout=60,
        )
        candidate = plan.get("alphaCandidate", {})
        managed = candidate.get("managedPlan")
        require(candidate.get("version") == EXPECTED_VERSION, "setup-version-mismatch")
        model_selection = candidate.get("modelSelection", {})
        selected = model_selection.get("selected")
        result.update({
            "managedSetupRuntimeAdmitted": candidate.get("managedSetupRuntimeAdmitted") is True,
            "managedSetupCandidateAvailable": candidate.get("managedSetupCandidateAvailable") is True,
            "hardwareDecision": candidate.get("hardware", {}).get("decision"),
            "hardwareBlockers": candidate.get("hardware", {}).get("blockers", []),
            "modelDecision": model_selection.get("decision"),
            "automaticExecutionAllowed": model_selection.get("automaticExecutionAllowed") is True,
        })
        if args.require_managed_setup:
            require(result["managedSetupRuntimeAdmitted"], "managed-runtime-not-admitted")
            require(result["managedSetupCandidateAvailable"], "managed-setup-unavailable")
        if managed is not None:
            require(isinstance(managed, dict), "managed-plan-invalid")
            require(managed.get("kind") == "linux-alpha-setup-plan", "managed-plan-kind-invalid")
            require(managed.get("version") == EXPECTED_VERSION, "managed-plan-version-mismatch")
            require(isinstance(managed.get("effects"), list) and managed["effects"], "managed-effects-missing")
            require(model_selection.get("automaticExecutionAllowed") is True, "automatic-selection-not-evidence-admitted")
            require(isinstance(selected, dict) and isinstance(selected.get("name"), str), "selected-model-missing")
            result.update({
                "managedSetupPlanned": True,
                "backendMode": managed.get("backendMode"),
                "runtimeVersion": managed.get("runtimeVersion"),
                "model": selected["name"],
                "modelDigest": selected.get("manifestDigest"),
                "declaredEffects": list(managed["effects"]),
            })

        if args.apply_managed_setup:
            require(isinstance(managed, dict), "managed-plan-missing")
            approval = request_json(
                origin,
                "/api/alpha/setup-approve",
                token=token,
                body={
                    "planId": managed["planId"],
                    "effects": managed["effects"],
                    "confirmed": True,
                },
            )
            require(approval.get("singleUse") is True, "approval-not-single-use")
            require(approval.get("persisted") is False, "approval-persisted")
            request_json(
                origin,
                "/api/alpha/setup-execute",
                token=token,
                body={"approvalToken": approval["approvalToken"]},
            )
            result["managedSetupApplied"] = True
            deadline = time.monotonic() + args.timeout_seconds
            previous_phase = ""
            status = {}
            while time.monotonic() < deadline:
                time.sleep(2)
                status = request_json(origin, "/api/alpha/setup-status", timeout=30)
                phase = status.get("phase")
                if phase != previous_phase:
                    print(
                        f"managed setup: {phase} ({status.get('progressPercent')}%)",
                        file=sys.stderr,
                        flush=True,
                    )
                    previous_phase = str(phase)
                if phase in TERMINAL_PHASES:
                    break
            require(status.get("phase") == "complete", f"managed-setup-{status.get('phase')}-{status.get('error')}")
            require(status.get("driverChanges") is False, "managed-setup-changed-driver")
            require(status.get("serviceChanges") is False, "managed-setup-changed-service")
            require(status.get("firewallChanges") is False, "managed-setup-changed-firewall")
            require(status.get("elevationRequested") is False, "managed-setup-requested-elevation")
            result["managedSetupCompleted"] = True

            connected = request_json(
                origin,
                "/api/alpha/connect-managed-provider",
                token=token,
                body={},
                timeout=330,
            )
            require(connected.get("connected") is True, "managed-provider-connect-failed")
            managed_resume = connected.get("managedResume", {})
            require(managed_resume.get("receiptVerified") is True, "managed-receipt-unverified")
            require(managed_resume.get("integrityVerified") is True, "managed-integrity-unverified")
            require(managed_resume.get("registeredDigestVerified") is True, "managed-registered-digest-unverified")
            require(managed_resume.get("publisherVerified") is False, "managed-linux-publisher-overclaimed")
            require(managed_resume.get("downloadPerformed") is False, "managed-resume-downloaded")
            require(managed_resume.get("installationPerformed") is False, "managed-resume-installed")
            require(connected.get("trustScope") == "loopback", "managed-provider-not-loopback")
            result["managedProviderConnected"] = True

            prompts = {
                "general.chat": "Reply with only NATIVE_ALPHA_OK.",
                "content.write": "Write exactly one sentence explaining that local AI runs on this computer.",
                "content.summarize": "Summarize in one sentence: Haven 42 is local-first, keeps its web interface on loopback, and requires approval before managed downloads.",
            }
            expected_kinds = {
                "general.chat": "chat-message",
                "content.write": "markdown-document",
                "content.summarize": "markdown-document",
            }
            for capability_id, prompt in prompts.items():
                reply = request_json(
                    origin,
                    "/api/text",
                    token=token,
                    body={
                        "capabilityId": capability_id,
                        "model": selected["name"],
                        "messages": [{"role": "user", "content": prompt}],
                        "attachments": [],
                        "images": [],
                        "contextConsent": False,
                    },
                    timeout=600,
                )
                require(reply.get("kind") == expected_kinds[capability_id], f"{capability_id}-kind-invalid")
                require(isinstance(reply.get("content"), str) and reply["content"].strip(), f"{capability_id}-empty")
                require(reply.get("modelDigestVerified") is True, f"{capability_id}-model-digest-unverified")
                result["capabilityResults"].append({
                    "capabilityId": capability_id,
                    "status": "passed-nonempty-native-response",
                    "modelDigestVerified": reply.get("modelDigestVerified") is True,
                })

            unloaded = request_json(origin, "/api/unload", token=token, body={})
            require(unloaded.get("modelUnloaded") is True, "managed-model-unload-failed")
            result["modelUnloadVerified"] = True

        shutdown = request_json(origin, "/api/shutdown", token=token, body={})
        shutdown_requested = True
        require(shutdown.get("shutdownAccepted") is True, "shutdown-not-accepted")
        require(shutdown.get("modelCleanupVerified") is True, "shutdown-cleanup-unverified")
        process.wait(timeout=20)
        result["shutdownVerified"] = True
    finally:
        if process.poll() is None and token and not shutdown_requested:
            try:
                if result["managedSetupApplied"]:
                    request_json(origin, "/api/unload", token=token, body={}, timeout=30)
                cleanup = request_json(
                    origin, "/api/shutdown", token=token, body={}, timeout=30,
                )
                if cleanup.get("shutdownAccepted") is True:
                    process.wait(timeout=20)
            except (OSError, RuntimeError, urllib.error.URLError, subprocess.TimeoutExpired):
                pass
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
