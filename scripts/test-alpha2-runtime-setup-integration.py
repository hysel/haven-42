#!/usr/bin/env python3
"""Verify Alpha 2 setup is approval-bound to an exact runtime route."""

from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
os.environ["HAVEN42_PACKAGED_VERSION"] = "0.4.0-alpha.2"
sys.frozen = True
sys._MEIPASS = str(ROOT)
SPEC = importlib.util.spec_from_file_location(
    "alpha2_runtime_setup_web", ROOT / "web" / "server.py",
)
assert SPEC and SPEC.loader
WEB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WEB)


class SetupStub:
    def __init__(self) -> None:
        self.registered: list[dict] = []
        self.approved: list[tuple[str, list[str]]] = []
        self.started: list[str] = []
        self.identity: dict | None = None
        self.resumed = 0

    def register_plan(self, plan: dict) -> None:
        self.registered.append(plan)

    def approve(self, plan_id: str, effects: list[str]) -> str:
        self.approved.append((plan_id, effects))
        return "approval-token"

    def start(self, token: str) -> None:
        self.started.append(token)

    def completed_setup_candidate(self) -> bool:
        return False

    def completed_setup_identity(self) -> dict | None:
        return self.identity

    def resume_completed(self) -> dict:
        self.resumed += 1
        return {"resumed": True, "modelId": self.identity["modelId"]}


def main() -> None:
    assert WEB.APP_VERSION == "0.4.0-alpha.2"
    linux = WEB.ALPHA_PLATFORM_PREFIX == "linux-alpha"
    plan_kind = (
        "linux-alpha-setup-plan" if linux else "windows-alpha-setup-plan"
    )
    component_id = "ollama-linux-core" if linux else "ollama-windows-core"
    WEB.verify_packaged_resources = lambda: {
        "required": True, "verified": True, "resourceCount": 24,
    }
    with tempfile.TemporaryDirectory(prefix="haven42-alpha2-runtime-web-") as directory:
        state = WEB.HavenState(
            readiness_provider=lambda: {},
            model_catalog_provider=lambda _query: [],
            diagnostic_root=Path(directory),
        )
        setup = SetupStub()
        state.alpha_setup = setup
        state.readiness_snapshot = {"snapshotId": "snapshot-1"}
        state.readiness_created = WEB.time.monotonic()

        WEB.build_setup_plan = lambda _snapshot, _intent: {"kind": "setup-plan"}
        WEB.select_model = lambda _snapshot: {
            "selected": {
                "id": "qwen35-4b-q4", "name": "qwen3.5:4b",
                "quantization": "Q4_K_M", "modelBytes": 3389971840,
            },
            "hardware": {"managedBackendCandidate": "cuda"},
            "automaticExecutionAllowed": True,
        }
        WEB.evaluate_hardware = lambda _snapshot: {
            "decision": "candidate", "managedBackendCandidate": "cuda",
            "blockers": [], "systemMemoryGiB": 32,
            "maximumUsableGpuMemoryGiB": 16,
        }
        WEB.driver_guidance = lambda _snapshot: []
        WEB.load_model_catalog = lambda: {"models": [{
            "id": "qwen35-4b-q4", "name": "qwen3.5:4b",
            "minimumSystemMemoryGiB": 8,
            "minimumUsableGpuMemoryGiB": 4,
        }]}
        WEB.build_windows_alpha_plan = lambda _snapshot, _selected: {
            "kind": plan_kind,
            "planId": "alpha2-plan-1",
            "modelId": "qwen35-4b-q4",
            "components": [component_id],
            "effects": ["network-download"],
            "backendMode": "cuda",
        }

        plan = state.setup_plan("snapshot-1", "guided-setup")
        candidate = plan["alphaCandidate"]
        binding = candidate["runtimeCompatibility"]
        assert candidate["managedSetupRuntimeAdmitted"] is True
        assert candidate["managedSetupCandidateAvailable"] is True
        assert binding["decision"] == "install"
        assert binding["engine"] == "ollama"
        assert binding["selectedRuntimeVersion"] == "0.32.14"
        assert binding["modelArtifact"]["exactTag"] == "qwen3.5:4b"
        assert binding["installationRoot"] == "Haven42-Data"
        assert setup.registered == [candidate["managedPlan"]]

        effects = candidate["managedPlan"]["effects"]
        assert state.approve_alpha_setup("alpha2-plan-1", effects) == "approval-token"
        state.start_alpha_setup("approval-token")
        assert setup.approved == [("alpha2-plan-1", effects)]
        assert setup.started == ["approval-token"]

        original_component_registry = WEB.load_alpha_component_registry
        drifted_registry = copy.deepcopy(original_component_registry())
        drifted_registry["components"][0]["sha256"] = "0" * 64
        WEB.load_alpha_component_registry = lambda: drifted_registry
        try:
            try:
                state.setup_plan("snapshot-1", "guided-setup")
            except WEB.WebRequestError as error:
                assert str(error) == "managed-component-runtime-artifact-mismatch"
            else:
                raise AssertionError("Drifted installer registry produced a managed plan")
        finally:
            WEB.load_alpha_component_registry = original_component_registry

        restored_plan = state.setup_plan("snapshot-1", "guided-setup")
        binding = restored_plan["alphaCandidate"]["runtimeCompatibility"]
        state.alpha_runtime_binding = dict(binding, selectedRuntimeVersion="0.32.4")
        try:
            state.approve_alpha_setup("alpha2-plan-1", effects)
        except WEB.SetupError as error:
            assert str(error) == "alpha2-runtime-binding-changed"
        else:
            raise AssertionError("Changed runtime binding was approved")

        original_resolver = WEB.resolve_alpha2_runtime
        WEB.resolve_alpha2_runtime = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            WEB.RuntimeCompatibilityError("no-admitted-compatible-runtime")
        )
        try:
            denied = state.setup_plan("snapshot-1", "guided-setup")
        finally:
            WEB.resolve_alpha2_runtime = original_resolver
        denied_candidate = denied["alphaCandidate"]
        assert denied_candidate["managedSetupRuntimeAdmitted"] is False
        assert denied_candidate["managedSetupCandidateAvailable"] is False
        assert denied_candidate["runtimeCompatibility"]["decision"] == "deny"
        assert "managedPlan" not in denied_candidate

        setup.identity = {
            "componentIds": [component_id],
            "modelId": "qwen35-4b-q4",
        }
        original_automatic = WEB.automatic_setup_admitted
        original_binding = WEB.bind_managed_model_decisions
        WEB.automatic_setup_admitted = lambda _selected, _snapshot: True
        WEB.bind_managed_model_decisions = lambda *_args: None
        state.connect = lambda *_args: {"models": ["qwen3.5:4b"]}
        try:
            resumed = state.resume_managed_provider()
        finally:
            WEB.automatic_setup_admitted = original_automatic
            WEB.bind_managed_model_decisions = original_binding
        assert resumed["managedResume"]["resumed"] is True
        assert setup.resumed == 1
        assert state.alpha_runtime_binding["selectedRuntimeVersion"] == "0.32.14"
        assert state.alpha_runtime_plan_id == "alpha2-plan-1"

    print("Alpha 2 runtime/setup integration passed 26 fail-closed checks.")


if __name__ == "__main__":
    main()
