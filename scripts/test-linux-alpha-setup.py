#!/usr/bin/env python3
"""Offline security and lifecycle tests for Linux Alpha 2 managed setup."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import urllib.request
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "linux_alpha_setup", ROOT / "scripts/linux_alpha_setup.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(function, code: str) -> None:
    try:
        function()
    except MODULE.SetupError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"Expected {code}")


def plan() -> dict:
    model = MODULE.load_catalog()["models"][0]
    component = MODULE.load_registry()["components"][0]
    return {
        "schemaVersion": 1,
        "kind": "linux-alpha-setup-plan",
        "planId": "abcdefghijklmnop",
        "version": "0.4.0-alpha.2",
        "components": ["ollama-linux-core"],
        "modelId": model["id"],
        "backendMode": "cpu",
        "gpuAccelerationRequired": False,
        "requiredStorageBytes": MODULE._required_storage(model, component),
        "effects": [
            "network-download", "portable-folder-files", "owned-process",
            "local-model-validation",
        ],
        "forbiddenEffects": MODULE.load_contract()["forbiddenEffects"],
        "approvalRequired": True,
        "rememberApprovalAllowed": False,
        "driverAutomationAllowed": False,
    }


def main() -> None:
    checks = 0
    value = plan()
    assert MODULE.validate_setup_plan(value) == value
    checks += 1
    for field, replacement in (
        ("kind", "windows-alpha-setup-plan"),
        ("components", ["ollama-linux-amd-rocm"]),
        ("backendMode", "rocm"),
        ("requiredStorageBytes", 1),
        ("approvalRequired", False),
        ("driverAutomationAllowed", True),
    ):
        hostile = dict(value)
        hostile[field] = replacement
        refused(lambda candidate=hostile: MODULE.validate_setup_plan(candidate), "invalid-setup-plan")
        checks += 1

    approvals = MODULE._ApprovalStore("a" * 32)
    token = approvals.issue(value)
    approvals.consume(token, value)
    refused(lambda: approvals.consume(token, value), "invalid-or-expired-approval")
    checks += 2

    redirects = MODULE._Redirects()
    request = urllib.request.Request("https://github.com/ollama/ollama/releases/download/v0.32.5/a")
    refused(
        lambda: redirects.redirect_request(
            request, None, 302, "Found", {}, "http://github.com/unsafe"
        ),
        "unsafe-download-redirect",
    )
    redirects = MODULE._Redirects()
    refused(
        lambda: redirects.redirect_request(
            request, None, 302, "Found", {}, "https://example.com/unsafe"
        ),
        "unsafe-download-redirect",
    )
    redirects = MODULE._Redirects()
    redirects.count = MODULE.MAX_REDIRECTS
    refused(
        lambda: redirects.redirect_request(
            request, None, 302, "Found", {},
            "https://release-assets.githubusercontent.com/too-many",
        ),
        "unsafe-download-redirect",
    )
    checks += 3

    with tempfile.TemporaryDirectory() as directory:
        # macOS exposes /var through /private/var. Resolve the temporary root
        # so the portable-root guard evaluates the actual directory tree.
        base = Path(directory).resolve()
        managed = base / "Haven42-Data"
        root = MODULE._owned_root(managed, create=True)
        assert root == managed.resolve() and (root / MODULE.OWNER_MARKER_NAME).is_file()
        assert MODULE._owned_root(managed, create=False) == root
        checks += 2

        unknown = base / "unknown"
        unknown.mkdir()
        refused(lambda: MODULE._owned_root(unknown, create=False), "unowned-portable-data-root")
        checks += 1

        coordinator = MODULE.SetupCoordinator("b" * 32, state_root=base / "portable")
        status = coordinator.register_plan(value)
        assert status["kind"] == "linux-alpha-setup-progress"
        assert status["storageScope"] == "inside-extracted-folder"
        assert status["driverChanges"] is False and status["serviceChanges"] is False
        approval = coordinator.approve(value["planId"], value["effects"])
        assert isinstance(approval, str) and len(approval) >= 32
        refused(lambda: coordinator.approve(value["planId"], []), "approval-does-not-match-plan")
        checks += 4

        ordering_root = MODULE._owned_root(base / "ordering", create=True)
        runtime_version = MODULE.load_registry()["components"][0]["version"]
        (ordering_root / "runtime" / runtime_version).mkdir(parents=True)
        ordering = MODULE.SetupCoordinator(
            "9" * 32, state_root=ordering_root,
        )
        ordering.register_plan(value)
        events: list[tuple[str, str]] = []

        def record_journal(_root: Path, receipt: dict) -> None:
            events.append(("receipt", receipt["phase"]))

        original_set = ordering._set

        def record_status(phase: str, percent: int, error: str | None = None) -> None:
            events.append(("status", phase))
            original_set(phase, percent, error)

        with (
            mock.patch.object(MODULE, "_journal", side_effect=record_journal),
            mock.patch.object(MODULE, "_verify_integrity"),
            mock.patch.object(MODULE, "_model_record", return_value=True),
            mock.patch.object(MODULE, "_validate_inference"),
            mock.patch.object(MODULE, "_wait_provider"),
            mock.patch.object(ordering, "_start_runtime"),
            mock.patch.object(ordering, "_set", side_effect=record_status),
        ):
            ordering._run(dict(value))
        assert events.index(("receipt", "complete")) < events.index(
            ("status", "complete")
        )
        checks += 1

        receipt_root = MODULE._owned_root(base / "receipt", create=True)
        hostile_receipt = {
            "schemaVersion": 1,
            "transactionId": "q" * 24,
            "planId": value["planId"],
            "version": value["version"],
            "phase": "complete",
            "componentIds": ["ollama-linux-amd-rocm"],
            "modelId": value["modelId"],
        }
        MODULE._journal(receipt_root, hostile_receipt)
        receipt_coordinator = MODULE.SetupCoordinator(
            "f" * 32, state_root=receipt_root,
        )
        receipt_coordinator.register_plan(value)
        assert receipt_coordinator.completed_setup_identity() is None
        refused(
            receipt_coordinator.resume_completed,
            "managed-setup-not-complete",
        )
        checks += 2

        valid_receipt = dict(hostile_receipt)
        valid_receipt["componentIds"] = ["ollama-linux-core"]
        MODULE._journal(receipt_root, valid_receipt)
        alternate = dict(value)
        alternate_model = MODULE.load_catalog()["models"][1]
        alternate["modelId"] = alternate_model["id"]
        alternate["requiredStorageBytes"] = MODULE._required_storage(
            alternate_model, MODULE.load_registry()["components"][0],
        )
        receipt_coordinator.register_plan(alternate)
        refused(
            receipt_coordinator.resume_completed,
            "managed-setup-not-complete",
        )
        checks += 1

        empty = MODULE.SetupCoordinator("c" * 32, state_root=base / "empty")
        assert empty.remove_managed_components()["removed"] is False
        owned = MODULE._owned_root(base / "owned", create=True)
        (owned / "file").write_text("managed", encoding="utf-8")
        remover = MODULE.SetupCoordinator("d" * 32, state_root=owned)
        assert remover.remove_managed_components()["removed"] is True
        assert not owned.exists()
        checks += 3

        if hasattr(Path, "symlink_to"):
            linked_root = MODULE._owned_root(base / "linked", create=True)
            outside = base / "outside"
            outside.write_text("keep", encoding="utf-8")
            try:
                (linked_root / "escape").symlink_to(outside)
            except OSError:
                pass
            else:
                linked = MODULE.SetupCoordinator("e" * 32, state_root=linked_root)
                refused(linked.remove_managed_components, "unsafe-portable-data-entry")
                assert outside.read_text(encoding="utf-8") == "keep"
                checks += 2

    model = MODULE.load_catalog()["models"][0]
    with mock.patch.object(MODULE, "_provider_json", return_value={"models": []}):
        assert MODULE._model_record(model) is False
    with mock.patch.object(MODULE, "_provider_json", return_value={"models": [{"name": model["name"], "digest": "0" * 64}]}):
        refused(lambda: MODULE._model_record(model), "model-manifest-digest-mismatch")
    checks += 2

    process = MODULE._OwnedProcess()
    refused(lambda: process.start(Path("missing"), {}, "cpu"), "invalid-runtime-executable")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        executable = root / "runtime" / "0.32.5" / "bin" / "ollama"
        executable.parent.mkdir(parents=True)
        executable.write_bytes(b"not executed")
        for name in ("models", "home", "temp"):
            (root / name).mkdir()
        environment = {
            "OLLAMA_HOST": MODULE.MANAGED_OLLAMA_HOST,
            "OLLAMA_MODELS": str(root / "models"),
            "OLLAMA_ORIGINS": "http://127.0.0.1",
            "OLLAMA_NO_CLOUD": "1",
            "OLLAMA_NOHISTORY": "1",
            "HOME": str(root / "home"),
            "TMPDIR": str(root / "temp"),
            "OLLAMA_LLM_LIBRARY": "cpu",
            "CUDA_VISIBLE_DEVICES": "-1",
        }
        refused(
            lambda: process.start(executable, environment, "rocm"),
            "invalid-runtime-backend",
        )
        with mock.patch.object(MODULE.subprocess, "Popen") as popen:
            popen.return_value.pid = 12345
            assert process.start(executable, environment, "cpu") == 12345
            launched = popen.call_args
            assert launched.args[0] == [str(executable.resolve()), "serve"]
            assert launched.kwargs["shell"] is False
            assert launched.kwargs["start_new_session"] is True
        process.process = None
        environment["HOME"] = str(root.parent)
        refused(
            lambda: process.start(executable, environment, "cpu"),
            "invalid-runtime-environment",
        )
    checks += 4
    print(f"Linux Alpha setup passed {checks} security and lifecycle checks.")


if __name__ == "__main__":
    main()
