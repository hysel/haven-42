#!/usr/bin/env python3
"""Run the approved Linux managed-runtime lifecycle in an isolated folder."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import linux_alpha_setup as setup  # noqa: E402


TERMINAL_PHASES = {"complete", "failed", "cancelled"}


class LifecycleError(RuntimeError):
    """The native lifecycle did not satisfy its fail-closed contract."""


def _port_open() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 11435), timeout=0.5):
            return True
    except OSError:
        return False


def _wait_port_closed(timeout_seconds: float = 15) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _port_open():
            return
        time.sleep(0.25)
    raise LifecycleError("managed-port-remained-open")


def _process_group_exists(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError as error:
        raise LifecycleError("managed-process-group-not-owned") from error


def _wait_setup(coordinator: setup.SetupCoordinator, timeout_seconds: int) -> dict:
    deadline = time.monotonic() + timeout_seconds
    prior: tuple[str, int] | None = None
    while time.monotonic() < deadline:
        status = coordinator.status()
        current = (status["phase"], status["progressPercent"])
        if current != prior:
            print(f"{current[0]} {current[1]}%", flush=True)
            prior = current
        if status["phase"] in TERMINAL_PHASES:
            return status
        time.sleep(1)
    coordinator.cancel()
    raise LifecycleError("managed-setup-timeout")


def _plan(backend: str) -> dict:
    if backend not in {"cpu", "cuda"}:
        raise LifecycleError("unsupported-backend")
    model = setup.load_catalog()["models"][0]
    component = setup.load_registry()["components"][0]
    return {
        "schemaVersion": 1,
        "kind": "linux-alpha-setup-plan",
        "planId": "native-lifecycle-validation",
        "version": "0.4.0-alpha.2",
        "components": [component["id"]],
        "modelId": model["id"],
        "backendMode": backend,
        "gpuAccelerationRequired": backend == "cuda",
        "requiredStorageBytes": setup._required_storage(model, component),
        "effects": [
            "network-download",
            "portable-folder-files",
            "owned-process",
            "local-model-validation",
        ],
        "forbiddenEffects": setup.load_contract()["forbiddenEffects"],
        "approvalRequired": True,
        "rememberApprovalAllowed": False,
        "driverAutomationAllowed": False,
    }


def _require_safe_paths(
    state_root: Path, evidence: Path, *, recover_existing: bool,
) -> None:
    if state_root.name != "Haven42-Data" or state_root.is_symlink():
        raise LifecycleError("unsafe-state-root")
    if state_root.exists():
        if not recover_existing:
            raise LifecycleError("state-root-already-exists")
        try:
            owned = setup._owned_root(state_root, create=False)
            receipt = owned / setup.JOURNAL_NAME
            transaction = json.loads(receipt.read_text(encoding="ascii"))
        except (OSError, UnicodeError, json.JSONDecodeError, setup.SetupError) as error:
            raise LifecycleError("existing-state-not-recoverable") from error
        if (
            not isinstance(transaction, dict)
            or transaction.get("phase") != "failed"
            or transaction.get("version") != "0.4.0-alpha.2"
        ):
            raise LifecycleError("existing-state-not-recoverable")
    if not state_root.parent.is_dir() or state_root.parent.is_symlink():
        raise LifecycleError("unsafe-state-parent")
    if evidence.exists() or evidence.is_symlink() or not evidence.parent.is_dir():
        raise LifecycleError("unsafe-evidence-path")


def run(
    state_root: Path,
    evidence: Path,
    timeout_seconds: int,
    *,
    backend: str = "cpu",
    recover_existing: bool = False,
) -> dict:
    _require_safe_paths(
        state_root, evidence, recover_existing=recover_existing,
    )
    if _port_open():
        raise LifecycleError("managed-port-already-occupied")
    coordinator = setup.SetupCoordinator("a" * 32, state_root=state_root)
    plan = _plan(backend)
    first_pid = 0
    resumed_pid = 0
    try:
        coordinator.register_plan(plan)
        token = coordinator.approve(plan["planId"], plan["effects"])
        coordinator.start(token)
        status = _wait_setup(coordinator, timeout_seconds)
        if status["phase"] != "complete" or status["error"] is not None:
            raise LifecycleError(f"managed-setup-{status['phase']}:{status['error']}")
        if not coordinator.process.is_running() or coordinator.process.process is None:
            raise LifecycleError("managed-process-not-running-after-setup")
        first_pid = coordinator.process.process.pid
        identity = coordinator.completed_setup_identity()
        if identity is None or identity["modelId"] != plan["modelId"]:
            raise LifecycleError("completed-identity-mismatch")
        model = setup.load_catalog()["models"][0]
        if not setup._model_record(model):
            raise LifecycleError("managed-model-identity-mismatch")
        coordinator.close()
        _wait_port_closed()
        if _process_group_exists(first_pid):
            raise LifecycleError("managed-process-survived-close")

        coordinator.register_plan(plan)
        resumed = coordinator.resume_completed()
        if resumed != {
            "resumed": True,
            "modelId": plan["modelId"],
            "backendMode": backend,
        }:
            raise LifecycleError("managed-resume-result-mismatch")
        if not coordinator.process.is_running() or coordinator.process.process is None:
            raise LifecycleError("managed-process-not-running-after-resume")
        resumed_pid = coordinator.process.process.pid
        coordinator.close()
        _wait_port_closed()
        if _process_group_exists(resumed_pid):
            raise LifecycleError("resumed-process-survived-close")

        removal = coordinator.remove_managed_components()
        if removal.get("removed") is not True or state_root.exists():
            raise LifecycleError("marker-owned-uninstall-incomplete")
        result = {
            "schemaVersion": 1,
            "kind": "haven42-linux-managed-lifecycle-evidence",
            "applicationVersion": "0.4.0-alpha.2",
            "runtimeVersion": setup.load_registry()["components"][0]["version"],
            "modelId": plan["modelId"],
            "backendMode": backend,
            "checks": {
                "freshSetup": "passed",
                "interruptedSetupRecovery": (
                    "passed" if recover_existing else "not-exercised"
                ),
                "exactRuntimeAndModel": "passed",
                "inference": "passed",
                "normalShutdown": "passed",
                "portClosure": "passed",
                "processTreeClosure": "passed",
                "zeroDownloadResume": "passed",
                "markerOwnedUninstall": "passed",
            },
            "containsMachineIdentity": False,
            "containsUserContent": False,
        }
        evidence.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return result
    finally:
        try:
            coordinator.close()
        except setup.SetupError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--backend", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--recover-existing-owned-state", action="store_true")
    args = parser.parse_args()
    if not 60 <= args.timeout_seconds <= 7200:
        raise LifecycleError("invalid-timeout")
    result = run(
        args.state_root.resolve(),
        args.evidence.resolve(),
        args.timeout_seconds,
        backend=args.backend,
        recover_existing=args.recover_existing_owned_state,
    )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
