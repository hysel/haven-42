#!/usr/bin/env python3
"""Hostile, effect-free tests for the Windows Alpha setup broker."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import tempfile
import types
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("windows_alpha_setup", ROOT / "scripts/windows_alpha_setup.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(code, function, *arguments):
    try:
        function(*arguments)
    except MODULE.SetupError as error:
        assert str(error) == code, (str(error), code)
        return
    raise AssertionError(f"unsafe setup input accepted: {code}")


def make_zip(path: Path, entries: list[tuple[str, bytes, int | None]]) -> None:
    with zipfile.ZipFile(path, "w") as handle:
        for name, data, mode in entries:
            info = zipfile.ZipInfo(name)
            if mode is not None:
                info.external_attr = mode << 16
            handle.writestr(info, data)


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory() as directory:
        trusted_local = Path(directory).resolve()
        with mock.patch.object(MODULE, "portable_data_root", return_value=trusted_local / "Haven42-Data"):
            with mock.patch.dict(os.environ, {"LOCALAPPDATA": str(trusted_local / "attacker")}, clear=False):
                assert MODULE.default_state_root() == trusted_local / "Haven42-Data"
                checks += 1
        redirected_parent = trusted_local / "redirected"
        redirected_parent.mkdir()
        with mock.patch.object(
            MODULE,
            "_is_reparse_point",
            side_effect=lambda path: Path(path).name == "redirected",
        ):
            rejected(
                "unsafe-reparse-root",
                MODULE._assert_safe_root,
                redirected_parent / "Haven42-Data",
            )
            checks += 1
    model = MODULE.load_model_catalog()["models"][0]
    base = {"accelerators": []}
    cpu = MODULE.build_plan(base, model)
    assert cpu["components"] == ["ollama-windows-core"]
    assert cpu["backendMode"] == "cpu" and cpu["gpuAccelerationRequired"] is False
    amd = MODULE.build_plan({"accelerators": [{"vendor": "AMD"}]}, model)
    assert amd["components"] == ["ollama-windows-core", "ollama-windows-amd-rocm"]
    assert amd["backendMode"] == "rocm" and amd["gpuAccelerationRequired"] is True
    intel = MODULE.build_plan({"accelerators": [{"vendor": "Intel"}]}, model)
    assert intel["components"] == ["ollama-windows-core"]
    assert intel["backendMode"] == "vulkan" and intel["gpuAccelerationRequired"] is True
    nvidia = MODULE.build_plan({"accelerators": [{"vendor": "NVIDIA"}]}, model)
    assert nvidia["backendMode"] == "cuda" and nvidia["gpuAccelerationRequired"] is True
    assert cpu["driverAutomationAllowed"] is False
    assert cpu["effects"] == [
        "network-download", "portable-folder-files", "owned-process",
        "local-model-validation",
    ]
    assert isinstance(cpu["requiredStorageBytes"], int) and cpu["requiredStorageBytes"] > model["modelBytes"]
    assert amd["requiredStorageBytes"] > cpu["requiredStorageBytes"]
    mixed = MODULE.build_plan({"accelerators": [
        {"vendor": "NVIDIA", "memoryGiB": 4},
        {"vendor": "AMD", "memoryGiB": 16},
    ]}, model)
    assert mixed["backendMode"] == "rocm"
    assert mixed["components"] == ["ollama-windows-core", "ollama-windows-amd-rocm"]
    checks += 13
    rejected("invalid-hardware-snapshot", MODULE.build_plan, {"accelerators": "Intel"}, model)
    checks += 1

    digest = model["manifestDigest"]
    for representation in (digest, "sha256:" + digest):
        verified_record = MODULE.verify_registered_model_record(
            model, [{"name": model["name"], "digest": representation}],
        )
        assert verified_record["manifestDigest"] == digest
        checks += 1
    rejected(
        "model-manifest-digest-mismatch",
        MODULE.verify_registered_model_record,
        model,
        [{"name": model["name"], "digest": "0" * 64}],
    )
    rejected(
        "model-manifest-digest-mismatch",
        MODULE.verify_registered_model_record,
        model,
        [{"name": model["name"], "digest": "SHA256:" + digest}],
    )
    checks += 2

    with mock.patch.object(MODULE, "_provider_json", return_value={
        "models": [{"name": model["name"], "digest": model["manifestDigest"]}],
    }) as local_tags:
        assert MODULE.registered_model_present(model) is True
        local_tags.assert_called_once_with("/api/tags")
    with mock.patch.object(MODULE, "_provider_json", return_value={"models": []}):
        assert MODULE.registered_model_present(model) is False
    with mock.patch.object(MODULE, "_provider_json", return_value={"models": "invalid"}):
        rejected("invalid-managed-model-record", MODULE.registered_model_present, model)
    checks += 3

    original_provider_json = MODULE._provider_json
    try:
        def provider_ok(path, body=None, timeout=30):
            if path == "/api/generate":
                assert body["model"] == model["name"]
                assert body["prompt"] == "Reply with only the word ready."
                return {"done": True, "response": "ready", "eval_count": 1}
            if path == "/api/ps":
                return {"models": [{"name": model["name"], "size_vram": 1024}]}
            raise AssertionError(path)

        MODULE._provider_json = provider_ok
        result = MODULE.validate_managed_inference(model, True)
        assert result["gpuAccelerationVerified"] is True

        def provider_thinking(path, body=None, timeout=30):
            if path == "/api/generate":
                return {"done": True, "response": "", "thinking": "working", "eval_count": 8}
            return {"models": [{"name": model["name"], "size_vram": 1024}]}

        MODULE._provider_json = provider_thinking
        assert MODULE.validate_managed_inference(model, True)["modelValidated"] is True

        def provider_cpu_fallback(path, body=None, timeout=30):
            if path == "/api/generate":
                return {"done": True, "response": "ready", "eval_count": 1}
            return {"models": [{"name": model["name"], "size_vram": 0}]}

        MODULE._provider_json = provider_cpu_fallback
        rejected("managed-accelerator-not-active", MODULE.validate_managed_inference, model, True)
        cpu_result = MODULE.validate_managed_inference(model, False)
        assert cpu_result["gpuAccelerationVerified"] is False
        checks += 4
    finally:
        MODULE._provider_json = original_provider_json

    class PullResponse:
        def __init__(self, records):
            self.records = iter(records)

        def __enter__(self):
            return self

        def __exit__(self, *_arguments):
            return False

        def readline(self, _limit):
            try:
                return next(self.records)
            except StopIteration:
                return b""

    pull_records = [
        (json.dumps({
            "status": "downloading", "digest": "sha256:" + "1" * 64,
            "total": 100, "completed": 25,
        }) + "\n").encode("utf-8"),
        (json.dumps({
            "status": "downloading", "digest": "sha256:" + "1" * 64,
            "total": 100, "completed": 100,
        }) + "\n").encode("utf-8"),
        (json.dumps({
            "status": "downloading", "digest": "sha256:" + "2" * 64,
            "total": 50, "completed": 50,
        }) + "\n").encode("utf-8"),
        b'{"status":"success"}\n',
    ]
    original_urlopen = MODULE.urllib.request.urlopen
    original_provider_json = MODULE._provider_json
    observed_progress = []
    try:
        MODULE.urllib.request.urlopen = lambda *_args, **_kwargs: PullResponse(pull_records)
        MODULE._provider_json = lambda path, *_args, **_kwargs: {
            "models": [{"name": model["name"], "digest": model["manifestDigest"]}],
        } if path == "/api/tags" else {}
        pulled = MODULE.pull_registered_model(
            model, progress=lambda completed, total: observed_progress.append((completed, total)),
        )
        assert pulled["downloaded"] is True
        assert observed_progress == [
            (25, model["modelBytes"]),
            (100, model["modelBytes"]),
            (150, model["modelBytes"]),
        ]
        checks += 2
    finally:
        MODULE.urllib.request.urlopen = original_urlopen
        MODULE._provider_json = original_provider_json

    approvals = MODULE.ApprovalStore("a" * 16)
    token = approvals.issue(cpu)
    approvals.consume(token, cpu)
    rejected("invalid-or-expired-approval", approvals.consume, token, cpu)
    token = approvals.issue(cpu)
    hostile = dict(cpu, effects=["driver-install"])
    rejected("invalid-or-expired-approval", approvals.consume, token, hostile)
    rejected("invalid-approval-plan", approvals.issue, dict(cpu, requiredStorageBytes=cpu["requiredStorageBytes"] - 1))
    checks += 4

    with tempfile.TemporaryDirectory() as directory:
        coordinator = MODULE.SetupCoordinator("b" * 16, Path(directory) / "state")
        registered = coordinator.register_plan(cpu)
        assert registered["phase"] == "idle" and registered["planId"] == cpu["planId"]
        assert [item["kind"] for item in registered["components"]] == ["runtime", "model"]
        assert registered["components"][0]["displayName"] == "Ollama local runtime"
        assert registered["components"][1]["displayName"] == model["name"]
        assert all(item["state"] == "pending" and item["progressPercent"] == 0 for item in registered["components"])
        coordinator._download_progress("ollama-windows-core", 1, 4)
        progress_status = coordinator.status()
        assert progress_status["components"][0]["state"] == "downloading"
        assert progress_status["components"][0]["progressPercent"] == 18
        rejected("invalid-component-progress", coordinator._download_progress, "ollama-windows-core", 5, 4)
        rejected("invalid-component-progress", coordinator._set_component, "unknown", "ready", 100)
        rejected("approval-does-not-match-plan", coordinator.approve, "wrong", cpu["effects"])
        approval = coordinator.approve(cpu["planId"], cpu["effects"])
        assert isinstance(approval, str) and len(approval) >= 32
        coordinator.approvals.consume(approval, cpu)
        rejected("invalid-or-expired-approval", coordinator.approvals.consume, approval, cpu)
        status = coordinator.status()
        assert status["driverChanges"] is False and status["serviceChanges"] is False
        assert status["firewallChanges"] is False and status["elevationRequested"] is False
        rejected(
            "invalid-setup-plan",
            coordinator.register_plan,
            dict(cpu, requiredStorageBytes=cpu["requiredStorageBytes"] - 1),
        )
        checks += 15

    with tempfile.TemporaryDirectory() as directory:
        state_root = Path(directory) / "Haven42-Data"
        owned = MODULE._owned_state_root(state_root, create=True)
        runtime_version = MODULE.load_component_registry()["components"][0]["version"]
        (owned / "runtime" / runtime_version).mkdir(parents=True)
        (owned / "runtime" / runtime_version / "ollama.exe").write_bytes(b"signed-runtime")
        (owned / f"{MODULE.RUNTIME_INTEGRITY_PREFIX}{runtime_version}.json").write_text(
            "{}", encoding="utf-8",
        )
        (owned / "models").mkdir()
        for relative in ("home", "appdata/local", "appdata/roaming", "temp"):
            (owned / relative).mkdir(parents=True, exist_ok=True)
        MODULE.write_journal(owned, {
            "schemaVersion": 1, "transactionId": "t" * 24,
            "planId": "p" * 24, "version": cpu["version"], "phase": "complete",
            "componentIds": cpu["components"], "modelId": cpu["modelId"],
        })
        expected_present = {*cpu["components"], cpu["modelId"]}
        assert MODULE.completed_setup_components(state_root, cpu) == expected_present
        coordinator = MODULE.SetupCoordinator("p" * 16, state_root)
        status = coordinator.register_plan(cpu)
        assert coordinator.completed_setup_candidate() is True
        assert {item["componentId"] for item in status["components"] if item["state"] == "present"} == expected_present
        assert all(item["progressPercent"] == 100 for item in status["components"])
        fake_process = mock.Mock()
        fake_process.is_running.return_value = False
        coordinator.process = fake_process
        with (
            mock.patch.object(MODULE, "verify_runtime_integrity") as verify_inventory,
            mock.patch.object(MODULE, "verify_authenticode") as verify_publisher,
            mock.patch.object(MODULE, "wait_for_managed_provider") as wait_provider,
            mock.patch.object(MODULE, "registered_model_present", return_value=True),
        ):
            resumed = coordinator.resume_completed()
        assert resumed["receiptVerified"] is True
        assert resumed["downloadPerformed"] is False
        assert resumed["installationPerformed"] is False
        assert resumed["endpoint"] == MODULE.MANAGED_OLLAMA_URL
        verify_inventory.assert_called_once()
        verify_publisher.assert_called_once()
        wait_provider.assert_called_once_with(runtime_version)
        fake_process.start.assert_called_once()
        assert coordinator.status()["phase"] == "complete"
        checks += 13

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        state_root = base / "Haven42-Data"
        owned = MODULE._owned_state_root(state_root, create=True)
        (owned / "models").mkdir()
        (owned / "models" / "blob").write_bytes(b"model")
        sibling = base / "keep.txt"
        sibling.write_text("keep", encoding="utf-8")
        coordinator = MODULE.SetupCoordinator("c" * 16, state_root)
        assert coordinator.storage_status()["managedComponentsPresent"] is True
        with mock.patch.object(
            MODULE, "_stop_windows_processes_beneath", return_value=[1234],
        ) as stop_owned:
            removed = coordinator.remove_managed_components()
        stop_owned.assert_called_once_with([owned])
        assert removed["removed"] is True and not state_root.exists()
        assert sibling.read_text(encoding="utf-8") == "keep"
        assert coordinator.remove_managed_components()["removed"] is False
        checks += 6

        blocked_root = MODULE._owned_state_root(base / "blocked-process-root", create=True)
        (blocked_root / "runtime").mkdir()
        coordinator = MODULE.SetupCoordinator("c" * 16, blocked_root)
        with mock.patch.object(
            MODULE,
            "_stop_windows_processes_beneath",
            side_effect=MODULE.SetupError("managed-process-stop-failed"),
        ):
            rejected("managed-process-stop-failed", coordinator.remove_managed_components)
        assert blocked_root.is_dir()
        checks += 2

        state_root.mkdir()
        (state_root / "unrelated.txt").write_text("do not delete", encoding="utf-8")
        coordinator = MODULE.SetupCoordinator("d" * 16, state_root)
        assert coordinator.storage_status()["managedComponentsState"] == "blocked-unrecognized"
        rejected("unowned-portable-data-root", coordinator.remove_managed_components)
        assert (state_root / "unrelated.txt").is_file()
        checks += 3

        owned = MODULE._owned_state_root(base / "audit-root", create=True)
        linked = owned / "linked"
        linked.write_text("blocked", encoding="utf-8")
        with mock.patch.object(
            MODULE,
            "_is_reparse_point",
            side_effect=lambda path: Path(path).name == "linked",
        ):
            rejected("unsafe-portable-data-entry", MODULE._audit_removal_tree, owned)
        with mock.patch.object(MODULE, "MAX_MANAGED_TREE_ENTRIES", 1):
            rejected("portable-data-entry-limit", MODULE._audit_removal_tree, owned)
        assert linked.is_file()
        checks += 3

    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        legacy = base / "legacy-alpha"
        legacy.mkdir()
        (legacy / "models").mkdir()
        (legacy / "models" / "blob").write_bytes(b"legacy-model")
        (legacy / MODULE.JOURNAL_NAME).write_text(json.dumps({
            "schemaVersion": 1,
            "transactionId": "t" * 24,
            "planId": cpu["planId"],
            "version": "0.4.0-alpha.1",
            "phase": "complete",
            "componentIds": cpu["components"],
            "modelId": model["id"],
        }), encoding="utf-8")
        assert MODULE._legacy_owned_state_root(legacy) == legacy.resolve()
        coordinator = MODULE.SetupCoordinator("e" * 16, base / "portable")
        coordinator.legacy_root = legacy
        assert coordinator.storage_status()["managedComponentsState"] == "legacy-managed"
        removed = coordinator.remove_managed_components()
        assert removed["legacyManagedComponentsRemoved"] is True
        assert not legacy.exists()
        checks += 4

        legacy.mkdir()
        (legacy / MODULE.JOURNAL_NAME).write_text("{}", encoding="utf-8")
        coordinator.legacy_root = legacy
        rejected("unrecognized-legacy-data-root", coordinator.remove_managed_components)
        assert legacy.exists()
        checks += 2

    original_disk_usage = MODULE.shutil.disk_usage
    try:
        MODULE.shutil.disk_usage = lambda _path: types.SimpleNamespace(
            total=cpu["requiredStorageBytes"], used=1,
            free=cpu["requiredStorageBytes"] - 1,
        )
        with tempfile.TemporaryDirectory() as directory:
            coordinator = MODULE.SetupCoordinator("d" * 16, Path(directory) / "state")
            coordinator._run(cpu)
            assert coordinator.status()["phase"] == "failed"
            assert coordinator.status()["error"] == "insufficient-managed-storage"
            checks += 2
    finally:
        MODULE.shutil.disk_usage = original_disk_usage

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        good = root / "good.zip"
        make_zip(good, [("ollama.exe", b"safe", stat.S_IFREG | 0o644), ("lib/runtime.dll", b"safe", stat.S_IFREG | 0o644)])
        assert len(MODULE.validate_zip(good)) == 2
        result = MODULE.extract_validated_zip(good, root / "output")
        assert result["memberCount"] == 2
        checks += 2

        fake_ollama = root / "ollama.exe"
        fake_ollama.write_bytes(b"signature-fixture")
        original_run = MODULE.subprocess.run
        captured = {}
        try:
            def signed_run(*arguments, **keywords):
                captured.update(keywords)
                captured["command"] = arguments[0]
                return types.SimpleNamespace(
                    returncode=0,
                    stdout=(
                        b'{"Status":"Valid","Subject":"CN=Ollama Inc.",'
                        b'"Thumbprint":"716CD3BC8C02361431A18F56F98C72DE88066103"}'
                    ),
                )

            MODULE.subprocess.run = signed_run
            signature = MODULE.verify_authenticode(fake_ollama)
            assert signature["status"] == "Valid"
            assert captured["shell"] is False
            assert captured["env"]["PSModulePath"].endswith(
                "System32\\WindowsPowerShell\\v1.0\\Modules"
            )
            assert captured["env"]["HAVEN42_AUTHENTICODE_TARGET"] == str(fake_ollama.resolve())
            assert set(captured["env"]) == {
                "SYSTEMROOT", "PATH", "PSModulePath", "HAVEN42_AUTHENTICODE_TARGET",
            }
            assert str(fake_ollama.resolve()) not in captured["command"]
            checks += 5
        finally:
            MODULE.subprocess.run = original_run

        managed_root = root / "managed-process"
        models = managed_root / "models"
        models.mkdir(parents=True)
        process_environment = {
            "OLLAMA_HOST": MODULE.MANAGED_OLLAMA_HOST,
            "OLLAMA_MODELS": str(models.resolve()),
            "OLLAMA_ORIGINS": "http://127.0.0.1",
            "OLLAMA_NO_CLOUD": "1",
            "OLLAMA_NOHISTORY": "1",
            "HOME": str((managed_root / "home").resolve()),
            "USERPROFILE": str((managed_root / "home").resolve()),
            "LOCALAPPDATA": str((managed_root / "appdata" / "local").resolve()),
            "APPDATA": str((managed_root / "appdata" / "roaming").resolve()),
            "TEMP": str((managed_root / "temp").resolve()),
            "TMP": str((managed_root / "temp").resolve()),
        }
        original_popen = MODULE.subprocess.Popen
        popen_capture = {}
        try:
            class FakeProcess:
                pid = 4242

            def fake_popen(*arguments, **keywords):
                popen_capture["command"] = arguments[0]
                popen_capture.update(keywords)
                return FakeProcess()

            MODULE.subprocess.Popen = fake_popen
            owned = MODULE.OwnedProcess()
            with (
                mock.patch.object(MODULE, "_create_windows_kill_job", return_value=99) as create_job,
                mock.patch.object(MODULE, "_assign_windows_kill_job") as assign_job,
                mock.patch.object(MODULE, "_resume_windows_process") as resume_process,
            ):
                assert owned.start(fake_ollama, ("serve",), process_environment, "cpu") == 4242
            create_job.assert_called_once_with()
            assign_job.assert_called_once_with(99, owned._process)
            resume_process.assert_called_once_with(owned._process)
            assert popen_capture["creationflags"] & MODULE.CREATE_SUSPENDED
            assert popen_capture["shell"] is False
            assert popen_capture["env"]["OLLAMA_NO_CLOUD"] == "1"
            assert popen_capture["env"]["OLLAMA_NOHISTORY"] == "1"
            assert popen_capture["env"]["USERPROFILE"] == str((managed_root / "home").resolve())
            rejected(
                "invalid-runtime-environment",
                MODULE.OwnedProcess().start,
                fake_ollama,
                ("serve",),
                {**process_environment, "OLLAMA_NO_CLOUD": "0"},
                "cpu",
            )
            checks += 10
        finally:
            MODULE.subprocess.Popen = original_popen

        cases = (
            ("traversal.zip", [("../escape", b"x", stat.S_IFREG | 0o644)]),
            ("absolute.zip", [("/escape", b"x", stat.S_IFREG | 0o644)]),
            ("drive.zip", [("C:/escape", b"x", stat.S_IFREG | 0o644)]),
            ("collision.zip", [("A.dll", b"x", stat.S_IFREG | 0o644), ("a.DLL", b"y", stat.S_IFREG | 0o644)]),
            ("link.zip", [("link", b"target", stat.S_IFLNK | 0o777)]),
        )
        for name, entries in cases:
            archive = root / name
            make_zip(archive, entries)
            rejected("unsafe-archive-member", MODULE.validate_zip, archive)
            checks += 1

        journal = {
            "schemaVersion": 1, "transactionId": "tx", "planId": "plan",
            "version": "0.4.0-alpha.1", "phase": "approved",
            "componentIds": ["ollama-windows-core"], "modelId": model["id"],
        }
        target = MODULE.write_journal(root / "state", journal)
        value = json.loads(target.read_text(encoding="ascii"))
        assert value == journal and target.stat().st_size < 4096
        rejected("invalid-transaction-journal", MODULE.write_journal, root / "state", {**journal, "url": "secret"})
        checks += 2

        stale = root / "state" / ".setup-transaction.json.0123456789abcdef.tmp"
        stale.write_text("stale", encoding="ascii")
        unrelated = root / "state" / "keep.tmp"
        unrelated.write_text("keep", encoding="ascii")
        assert MODULE.clean_stale_journal_temps(root / "state") == 1
        assert not stale.exists() and unrelated.read_text(encoding="ascii") == "keep"
        checks += 2

        runtime = root / "runtime" / "0.32.5"
        runtime.mkdir(parents=True)
        (runtime / "ollama.exe").write_bytes(b"signed-fixture")
        (runtime / "runtime.dll").write_bytes(b"runtime-fixture")
        MODULE.write_runtime_integrity(root / "managed", "0.32.5", runtime)
        verified = MODULE.verify_runtime_integrity(root / "managed", "0.32.5", runtime)
        assert verified == {"verified": True, "fileCount": 2, "version": "0.32.5"}
        (runtime / "runtime.dll").write_bytes(b"tampered")
        rejected("managed-runtime-integrity-mismatch", MODULE.verify_runtime_integrity, root / "managed", "0.32.5", runtime)
        checks += 2

    with tempfile.TemporaryDirectory() as directory:
        blocked_root = Path(directory) / "not-a-directory"
        blocked_root.write_text("blocked", encoding="utf-8")
        coordinator = MODULE.SetupCoordinator("c" * 16, blocked_root / "state")
        coordinator._run(cpu)
        assert coordinator.status()["phase"] == "failed"
        assert coordinator.status()["error"] == "setup-internal-failure"
        assert coordinator.process.stop() is True
        checks += 3

    registry = MODULE.load_component_registry()
    hostile_component = dict(registry["components"][0], sourceUrl="https://evil.example/a.zip")
    with tempfile.TemporaryDirectory() as directory:
        rejected("unregistered-component", MODULE.download_registered_component, hostile_component, Path(directory) / "a.zip")
    checks += 1
    print(f"Windows alpha setup hostile tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
