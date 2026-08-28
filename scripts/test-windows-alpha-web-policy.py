#!/usr/bin/env python3
"""Verify the Windows Alpha server boundary cannot be broadened by the UI."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("alpha_web", ROOT / "web/server.py")
WEB = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(WEB)


def main() -> int:
    expected_version = "0.4.0-alpha.2" if WEB.LINUX_ALPHA else "0.4.0-alpha.1"
    expected_label = "Haven 42 0.4 Alpha 2" if WEB.LINUX_ALPHA else "Haven 42 0.4 Alpha 1"
    assert WEB.APP_VERSION == expected_version
    assert WEB.ALPHA_TEXT_ONLY is True
    assert WEB.ALPHA_TEXT_CAPABILITIES == {
        "general.chat", "content.write", "content.summarize",
    }
    isolated_state = tempfile.TemporaryDirectory()
    state = WEB.HavenState(
        readiness_provider=lambda: {},
        model_catalog_provider=lambda _query: [],
        managed_setup_state_root=Path(isolated_state.name) / "Haven42-Data",
        assurance_provider=lambda: {
            "kind": "read-only-assurance-summary", "status": "ready",
            "effects": {
                "networkAccess": False, "processCreation": False,
                "filesystemWrite": False, "repositoryRead": False,
                "providerInvocation": False, "machineModification": False,
            },
        },
    )
    status = state.public_status()
    assert status["alpha"] == {
        "label": expected_label, "windowsOnly": not WEB.LINUX_ALPHA,
        "chatOnly": False, "textOnly": True,
        "unsigned": True, "productionReady": False,
        "managedSetupRuntimeAdmitted": False,
        "managedSetupCandidateAvailable": WEB.MANAGED_SETUP_SUPPORTED,
        "managedSetupCompletedCandidate": False,
    }
    for capability in ("content.write", "content.summarize"):
        try:
            state.run_text_capability(capability, "model", [], [], [], False)
        except WEB.WebRequestError as error:
            assert error.code == "ollama-not-connected"
        else:
            raise AssertionError(f"Alpha unexpectedly executed without a provider: {capability}")
    try:
        state.run_text_capability("media.image.create", "model", [], [], [], False)
    except WEB.WebRequestError as error:
        assert error.code == "alpha-text-only"
    else:
        raise AssertionError("Alpha accepted a forbidden non-text capability")
    state.alpha_tokens.add({
        "inputTokens": 1, "outputTokens": 2, "totalTokens": 3,
        "tokensPerSecond": 4, "totalDurationMs": 5,
        "loadDurationMs": 1, "promptDurationMs": 1,
        "providerReported": True,
    })
    assert state.alpha_tokens.summary()["totalTokens"] == 3
    state.alpha_tokens.reset()
    assert state.alpha_tokens.summary()["totalTokens"] == 0

    class SetupStub:
        def __init__(self) -> None:
            self.registered = []

        def register_plan(self, plan) -> None:
            self.registered.append(plan)

        def resume_completed(self):
            return {
                "endpoint": WEB.MANAGED_OLLAMA_URL,
                "receiptVerified": True,
                "integrityVerified": True,
                "publisherVerified": True,
                "downloadPerformed": False,
                "installationPerformed": False,
            }

        def completed_setup_identity(self):
            return {
                "version": "0.4.0-alpha.1",
                "componentIds": ["ollama-windows-core"],
                "modelId": "model-1",
            }

        def close(self):
            return True

    setup = SetupStub()
    state.alpha_setup = setup
    state.readiness_snapshot = {"snapshotId": "snapshot-1"}
    state.readiness_created = WEB.time.monotonic()
    WEB.build_setup_plan = lambda _snapshot, _intent: {"kind": "setup-plan"}
    # This unit test replaces every platform-specific operation with inert
    # stubs. Exercise the server policy consistently on all CI hosts without
    # weakening the real active-platform adapter.
    WEB.require_platform_operation = lambda _operation_id: None
    WEB.evaluate_hardware = lambda _snapshot: {"decision": "candidate"}
    WEB.driver_guidance = lambda _snapshot: []
    WEB.load_model_catalog = lambda: {"models": [{
        "id": "model-1",
        "name": "qwen3.5:0.8b",
        "manifestDigest": "a" * 64,
        "windowsEvidenceStatus": "validated-exact-windows-cell",
        "minimumSystemMemoryGiB": 8,
        "minimumUsableGpuMemoryGiB": 0,
    }]}
    WEB.build_windows_alpha_plan = lambda _snapshot, _selected: {
        "planId": "plan-1", "components": ["ollama-windows-core"],
        "backendMode": "cpu",
    }
    WEB.build_resume_plan = WEB.build_windows_alpha_plan
    WEB.automatic_setup_admitted = lambda _selected, _snapshot: True
    WEB.resume_setup_admitted = lambda _selected, _snapshot: True
    WEB.resolve_alpha2_runtime = lambda *_args, **_kwargs: {"decision": "install"}
    WEB.validate_managed_setup_binding = lambda *_args, **_kwargs: None
    WEB.load_alpha_component_registry = lambda: {}
    WEB.select_model = lambda _snapshot: {
        "selected": {"id": "model-1"}, "automaticExecutionAllowed": False,
    }
    blocked = state.setup_plan("snapshot-1", "guided")
    assert blocked["alphaCandidate"]["managedSetupCandidateAvailable"] is False
    assert "managedPlan" not in blocked["alphaCandidate"]
    assert setup.registered == []

    WEB.select_model = lambda _snapshot: {
        "selected": {"id": "model-1"}, "automaticExecutionAllowed": True,
    }
    admitted = state.setup_plan("snapshot-1", "guided")
    assert admitted["alphaCandidate"]["managedSetupCandidateAvailable"] is True
    expected_plan = {
        "planId": "plan-1", "components": ["ollama-windows-core"],
        "backendMode": "cpu",
    }
    assert admitted["alphaCandidate"]["managedPlan"] == expected_plan
    assert setup.registered == [expected_plan]

    state.inspect_readiness = lambda _force: state.readiness_snapshot
    WEB.evaluate_hardware = lambda _snapshot: {
        "decision": "candidate", "blockers": [], "systemMemoryGiB": 16,
        "maximumUsableGpuMemoryGiB": 0,
    }
    original_connect = state.connect
    state.connect = lambda endpoint, timeout, idle, mode, key: {
        "connected": endpoint == WEB.MANAGED_OLLAMA_URL,
        "recommendations": {},
        "modelOptions": [{
            "name": "qwen3.5:0.8b", "digestVerified": False,
            "capabilityStatus": {},
        }],
        "evidenceBoundary": {
            "recommendationBinding": "model-name-digest-and-capability-evidence",
            "immutableDigestBound": False,
            "hardwareFitMeasured": False,
            "unknownModelsGainAuthority": False,
        },
    }
    state.model_digests = {"qwen3.5:0.8b": "a" * 64}
    try:
        resumed = state.resume_managed_provider()
        state.base_url = WEB.MANAGED_OLLAMA_URL
        resumed_again = state.resume_managed_provider()
    finally:
        state.base_url = None
        state.connect = original_connect
    assert resumed["connected"] is True
    assert resumed["managedResume"]["downloadPerformed"] is False
    assert resumed_again["connected"] is True
    assert resumed_again["managedResume"]["downloadPerformed"] is False
    assert setup.registered[-2:] == [expected_plan, expected_plan]

    app = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
    setup_renderer = app[app.index("function renderSetupPlan"):app.index("async function runManagedAlphaSetup")]
    assert "Recommended setup for this computer" in setup_renderer
    assert "Haven 42 checked your computer" in setup_renderer
    assert "cannot safely set it up automatically yet" in setup_renderer
    assert "processor compatibility mode" in setup_renderer
    assert "detected graphics hardware is not required" in setup_renderer
    assert "stop safely unless processor compatibility mode works" in setup_renderer
    assert "${storageText} required · stored beside the app" in setup_renderer
    assert "What Haven 42 will do · details" in setup_renderer
    assert "Drivers and Windows settings are not changed automatically" in setup_renderer
    assert "Download and safety details" in app
    assert "Your permission is required" in setup_renderer
    assert "I understand the list above and allow Haven 42" in setup_renderer
    assert "Try starting local AI" in setup_renderer
    assert "Nothing will be downloaded, installed, or replaced" in app
    assert 'api("/api/alpha/connect-managed-provider", {})' in setup_renderer
    assert "summary.textContent = plan.summary" not in setup_renderer
    assert "if (!managed || button.disabled || !consent.checked) return" in app
    assert 'api("/api/alpha/connect-managed-provider", {})' in app
    assert 'selection.mode === "none"' in app
    assert "managedSetupCompletedCandidate === true" in app
    assert "Finish the local setup above" in app
    assert 'byId("alpha-setup-review")?.focus()' in app
    assert 'id="wizard-provider-back"' in (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert 'showWizardStep(state.readinessSnapshot ? "readiness" : "welcome")' in app
    assert 'byId("wizard-readiness-next").disabled = true' in app
    assert "receiptVerified !== true" in app
    assert 'state.platformFamily === "linux"' in app
    assert "registeredDigestVerified === true" in app
    assert "publisherVerified === false" in app
    setup_progress_renderer = app[app.index("function validAlphaSetupProgress"):app.index("async function runManagedAlphaSetup")]
    assert ".innerHTML" not in setup_progress_renderer
    assert ".innerHTML" not in setup_renderer
    removal = app[app.index('byId("remove-managed-components")'):]
    assert "window.confirm" in removal
    assert '/api/alpha/remove-managed-components' in removal
    assert "applicationFilesRemoved !== false" in removal
    assert "showPostRemovalExperience()" in removal
    assert 'id="removed-guided"' in (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert 'id="removed-existing"' in (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert 'id="removed-close"' in (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert 'api("/api/shutdown", {})' in removal
    assert "Haven42-Logs" in removal
    assert ".innerHTML" not in removal
    html = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
    assert 'href="https://github.com/hysel/haven-42/issues/new?template=alpha-bug-report.yml"' in html
    assert 'referrerpolicy="no-referrer"' in html
    assert "prompts, responses, file names, addresses" in html
    assert 'id="local-ai-maintenance-title">Local AI on this computer' in html
    assert 'id="setup-local-components"' in html
    assert 'id="remove-managed-components"' in html
    assert html.index('id="setup-local-components"') < html.index('id="remove-managed-components"')
    assert html.index('id="remove-managed-components"') < html.index('id="cleanup-policy-form"')
    assert "Set up local AI on this computer" in app
    assert "Use local AI on this computer" in app
    assert "Your current AI connection was kept unchanged" in app
    assert "Guided setup is open so you can review or repair" in app
    assert "Local AI is installed and connected on this computer" in app
    managed_ready = app[app.index("async function showManagedLocalReady"):app.index("async function runManagedAlphaSetup")]
    assert "const storage = await refreshManagedStorageStatus()" in managed_ready
    assert 'managedComponentsPresent !== true' in managed_ready
    setup_execution = app[app.index("async function runManagedAlphaSetup"):app.index("async function runReadiness")]
    assert "await showManagedLocalReady()" in setup_execution
    local_setup = app[
        app.index('byId("setup-local-components").addEventListener'):
        app.index('byId("remove-managed-components").addEventListener')
    ]
    assert '/api/alpha/connect-managed-provider' in local_setup
    assert 'byId("setup-wizard").classList.remove("hidden")' in local_setup
    assert "window.confirm" not in local_setup
    assert "It does not remove drivers, another Ollama installation" in html
    assert "Uninstall local AI components" in app
    assert "No local AI components installed" in app
    assert "Retry model download" in app
    assert "retry only the missing local AI model" in app
    assert "installation-component-check" in app
    assert "did not start within 2 minutes" in app
    assert "System → Troubleshooting logs" in app
    assert "View troubleshooting logs" in app
    assert "Cancel model download" in app
    assert "Calculating speed" in app
    assert "Existing local download data was kept" in app
    assert "Model download complete. The local test stopped" in app
    assert "Retry local AI test" in app
    assert 'id="diagnostics-control"' in html
    assert "never recorded or uploaded" in html
    assert all(path in app for path in (
        "/api/alpha/diagnostics",
        "/api/alpha/diagnostics/report",
        "/api/alpha/diagnostics/clear",
        "/api/alpha/diagnostics/remove",
    ))
    diagnostic_ui = app[app.index("const DIAGNOSTIC_EVENT_FIELDS"):app.index('byId("removed-guided")')]
    assert ".innerHTML" not in diagnostic_ui
    assert "replaceChildren" in diagnostic_ui and "textContent" in diagnostic_ui
    assert "promptsRecorded" in diagnostic_ui and "automaticUpload" in diagnostic_ui
    assert "Haven42-Logs" in diagnostic_ui
    print("Windows alpha web policy tests passed: 57 checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
