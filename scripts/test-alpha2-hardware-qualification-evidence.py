#!/usr/bin/env python3
"""Offline tests for sanitized hardware qualification evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EVIDENCE = load("hardware_evidence", "scripts/alpha2-hardware-qualification-evidence.py")
COMPARE = load("hardware_compare", "scripts/alpha2-hardware-cross-os-report.py")
REPORT = load("hardware_report", "scripts/alpha2-hardware-qualification-report.py")


def write_binding(root: Path) -> Path:
    profile = json.loads((root / "profile.json").read_text(encoding="utf-8"))
    digest = EVIDENCE.canonical_sha256(profile)
    roles = sorted(EVIDENCE.REQUIRED_BINDING_ROLES)
    binding = {
        "schemaVersion": 1,
        "kind": "haven42-evidence-input-binding",
        "evidenceId": "fixture-hardware-evidence",
        "inputs": [
            {"role": role, "path": "profile.json", "hashMode": "canonical-json", "sha256": digest}
            for role in roles
        ],
    }
    path = root / "binding.json"
    path.write_text(json.dumps(binding), encoding="utf-8")
    return path


def complete_report(root: Path) -> dict:
    return EVIDENCE.build_report(root, binding_path=write_binding(root), repository_root=root)


def write_campaign(root: Path, complete: bool = False) -> None:
    (root / "telemetry").mkdir(parents=True)
    (root / "results/core").mkdir(parents=True)
    (root / "results/soak").mkdir(parents=True)
    profile = {
        "schemaVersion": 1,
        "release": "0.4.0-alpha.2",
        "operatingSystem": "Test Linux",
        "kernel": "1.2.3-test",
        "accelerator": "Test GPU 12 GB",
        "driverVersion": "1.0-test",
        "backend": "cuda",
        "systemMemoryGiB": 32,
        "runtimeProvider": "ollama",
        "runtimeVersion": "0.0-test",
        "runtimeArtifactSha256": "a" * 64,
        "qualificationProfileId": "test-12gib",
        "inventoryCanonicalSha256": "b" * 64,
        "matrixCanonicalSha256": "c" * 64,
        "expectedModelIds": ["model-a", "model-b"],
        "telemetryUtcOffset": "+00:00",
    }
    (root / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    events = [
        "2026-08-18T00:00:00Z\tcampaign\tcore-start",
        "2026-08-18T00:01:00Z\tmodel-a\tpassed",
    ]
    core = "model_id\tstatus\tfailure_cell\nmodel-a\tpassed\t\n"
    soak = "model_id\tstatus\n"
    if complete:
        events.extend([
            "2026-08-18T00:02:00Z\tmodel-b\tfailed-validation",
            "2026-08-18T00:03:00Z\tcampaign\tcore-complete",
            "2026-08-18T00:04:00Z\tcampaign\tsoak-complete",
            "2026-08-18T00:09:00Z\tcampaign\tpost-idle-complete",
        ])
        core += "model-b\tfailed-validation\tcontent.write-2\n"
        soak += "model-a\tpassed\n"
    (root / "telemetry/events.tsv").write_text("\n".join(events) + "\n", encoding="utf-8")
    (root / "telemetry/nvidia-smi.csv").write_text(
        "timestamp,power.draw [W],temperature.gpu\n"
        "2026-08-18T00:00:00Z,20.0 W,40\n"
        "2026-08-18T00:00:01Z,50.0 W,41\n",
        encoding="utf-8",
    )
    (root / "results/core/summary.tsv").write_text(core, encoding="utf-8")
    (root / "results/soak/summary.tsv").write_text(soak, encoding="utf-8")


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root)
        partial = EVIDENCE.build_report(root)
        assert partial["status"] == "in-progress-local-review-only"
        assert partial["counts"]["exactArtifactsChecked"] == 1
        assert partial["power"]["averageWatts"] == 35.0
        assert partial["power"]["perModelCore"] == {}
        assert partial["automaticSupportChangeAllowed"] is False
        checks += 5

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        complete = complete_report(root)
        assert complete["status"] == "exact-profile-engineering-evidence-complete"
        assert complete["coreTaskGate"]["failed"] == {"model-b": ["content.write-2"]}
        assert complete["soak"]["passed"] == ["model-a"]
        assert len(complete["campaignCanonicalSha256"]) == 64
        checks += 4

        other = json.loads(json.dumps(complete))
        other["environment"]["operatingSystem"] = "Test Windows"
        other["coreTaskGate"] = {"passed": ["model-a", "model-b"], "failed": {}}
        comparison = COMPARE.build_comparison(complete, other)
        assert comparison["status"] == "complete"
        assert comparison["commonPasses"] == ["model-a"]
        assert comparison["divergences"] == [{
            "modelId": "model-b", "first": "failed", "second": "passed",
            "comparable": True, "divergent": True,
        }]
        assert comparison["crossOperatingSystemInheritanceAllowed"] is False
        checks += 4
        triage = REPORT.build_triage(complete, other, comparison)
        assert next(item for item in triage["entries"] if item["modelId"] == "model-b")["classification"] == "cross-os-outcome-divergence"
        rendered = REPORT.render_report(complete, other, comparison, triage)
        assert "GPU-board telemetry is not a whole-system electricity measurement" in rendered
        checks += 2
        forged = json.loads(json.dumps(comparison))
        forged["commonPasses"] = []
        try:
            REPORT.build_triage(complete, other, forged)
        except ValueError as error:
            assert "does not match" in str(error)
            checks += 1
        else:
            raise AssertionError("forged comparison was accepted by the report renderer")

        drifted = json.loads(json.dumps(other))
        drifted["sourceBindings"]["matrixCanonicalSha256"] = "d" * 64
        try:
            COMPARE.build_comparison(complete, drifted)
        except ValueError as error:
            assert "source binding mismatch" in str(error)
            checks += 1
        else:
            raise AssertionError("different qualification matrices were compared")

        missing_freshness = json.loads(json.dumps(other))
        missing_freshness["sourceBindings"]["inputFreshness"] = None
        try:
            COMPARE.build_comparison(complete, missing_freshness)
        except ValueError as error:
            assert "lacks fresh exact input bindings" in str(error)
            checks += 1
        else:
            raise AssertionError("complete result without fresh bindings was compared")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        try:
            EVIDENCE.build_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "requires exact input bindings" in str(error)
            checks += 1
        else:
            raise AssertionError("completed evidence without input bindings was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        binding = write_binding(root)
        profile = json.loads((root / "profile.json").read_text(encoding="utf-8"))
        profile["kernel"] = "changed-after-run"
        (root / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
        try:
            EVIDENCE.build_report(root, binding_path=binding, repository_root=root)
        except EVIDENCE.EvidenceError as error:
            assert "inputs are stale" in str(error)
            checks += 1
        else:
            raise AssertionError("stale evidence input binding was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        binding_path = write_binding(root)
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["inputs"] = binding["inputs"][:-1]
        binding_path.write_text(json.dumps(binding), encoding="utf-8")
        try:
            EVIDENCE.build_report(root, binding_path=binding_path, repository_root=root)
        except EVIDENCE.EvidenceError as error:
            assert "roles mismatch" in str(error)
            checks += 1
        else:
            raise AssertionError("incomplete binding role set was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root)
        profile = json.loads((root / "profile.json").read_text(encoding="utf-8"))
        profile["hostname"] = "private-lab-host"
        (root / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
        try:
            complete_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "private identity fields" in str(error)
            checks += 1
        else:
            raise AssertionError("private identity field was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root)
        profile = json.loads((root / "profile.json").read_text(encoding="utf-8"))
        profile["accelerator"] = "Test GPU\nInjected heading"
        (root / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
        try:
            EVIDENCE.build_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "control characters" in str(error)
            checks += 1
        else:
            raise AssertionError("control characters were accepted in evidence profile")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        core = root / "results/core/summary.tsv"
        core.write_text(core.read_text(encoding="utf-8") + "model-b\tpassed\t\n", encoding="utf-8")
        try:
            complete_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "duplicate or unexpected" in str(error)
            checks += 1
        else:
            raise AssertionError("duplicate model result was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        (root / "results/core/summary.tsv").write_text(
            "model_id\tstatus\tfailure_cell\nmodel-a\tpassed\t\nmodel-b\tfailed-validation\t\n",
            encoding="utf-8",
        )
        try:
            complete_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "needs a failure cell" in str(error)
            checks += 1
        else:
            raise AssertionError("failure without an exact cell was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root, complete=True)
        (root / "results/soak/summary.tsv").write_text("model_id\tstatus\n", encoding="utf-8")
        try:
            EVIDENCE.build_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "claims completion" in str(error)
            checks += 1
        else:
            raise AssertionError("incomplete campaign claimed completion")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root)
        (root / "telemetry/events.tsv").write_text(
            "2026-08-18T00:01:00Z\tcampaign\tcore-start\n"
            "2026-08-18T00:00:00Z\tmodel-a\tpassed\n",
            encoding="utf-8",
        )
        try:
            EVIDENCE.build_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "ordered" in str(error)
            checks += 1
        else:
            raise AssertionError("out-of-order event log was accepted")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write_campaign(root)
        (root / "telemetry/nvidia-smi.csv").write_text(
            "timestamp,temperature\n2026-08-18T00:00:00Z,40\n", encoding="utf-8"
        )
        try:
            EVIDENCE.build_report(root)
        except EVIDENCE.EvidenceError as error:
            assert "timestamp and power" in str(error)
            checks += 1
        else:
            raise AssertionError("telemetry without power was accepted")

    mismatch = json.loads(json.dumps(complete))
    mismatch["environment"]["accelerator"] = "Different GPU"
    try:
        COMPARE.build_comparison(complete, mismatch)
    except ValueError as error:
        assert "accelerator" in str(error)
        checks += 1
    else:
        raise AssertionError("different hardware was compared as one cell")

    print(f"Hardware qualification evidence checks passed: {checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
