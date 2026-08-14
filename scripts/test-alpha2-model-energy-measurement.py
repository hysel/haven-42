#!/usr/bin/env python3
"""Deterministic checks for the Alpha 2 model energy measurement tool."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/alpha2-model-energy-measurement.py"
CONTRACT = ROOT / "config/alpha-2-model-energy-evidence-contract.json"
COST_SCRIPT = ROOT / "scripts/calculate-model-energy-cost.py"
CAMPAIGN_SCRIPT = ROOT / "scripts/alpha2-model-energy-campaign.py"


def load_path(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def refused(callback, message: str) -> None:
    try:
        callback()
    except Exception as error:
        assert str(error) == message, (str(error), message)
    else:
        raise AssertionError(f"expected refusal: {message}")


def main() -> int:
    module = load_path("alpha2_energy", SCRIPT)

    idle = [module.PowerSample(float(index), 20.0) for index in range(3)]
    active = [
        module.PowerSample(float(index), watts, 80.0, 4096.0, 65.0, "general.chat")
        for index, watts in enumerate((100.0, 120.0, 140.0))
    ]
    metrics = module.summarize_samples(idle, active, 300, 6000)
    assert metrics == {
        "idleAverageWatts": 20.0,
        "loadAverageWatts": 120.0,
        "loadPeakWatts": 140.0,
        "idleAdjustedAverageWatts": 100.0,
        "measuredGpuEnergyWh": 10.0,
        "idleAdjustedGpuEnergyWh": 8.333333,
        "outputTokens": 6000,
        "outputTokensPerSecond": 20.0,
        "outputTokensPerWh": 600.0,
        "averageGpuUtilizationPercent": 80.0,
        "peakMemoryUsedMiB": 4096.0,
        "peakTemperatureCelsius": 65.0,
    }
    assert module.estimate_monthly_cost(120, 0.20, 2, 30) == {
        "electricityRatePerKwh": 0.2,
        "currency": "USD",
        "usageHoursPerDay": 2.0,
        "billingDays": 30,
        "estimatedGpuOnlyKwh": 7.2,
        "estimatedGpuOnlyCost": 1.44,
        "notWholeComputerCost": True,
    }
    task_samples = []
    task_seconds = {}
    task_tokens = {}
    for index, (task, _) in enumerate(module.TASKS):
        task_samples.append(module.PowerSample(float(index), 100 + index * 10, task=task))
        task_seconds[task] = 10
        task_tokens[task] = 100
    by_task = module.task_energy_metrics(task_samples, task_seconds, task_tokens)
    assert set(by_task) == {"general.chat", "content.write", "content.summarize"}
    assert by_task["general.chat"]["averageWatts"] == 100
    assert by_task["content.summarize"]["peakWatts"] == 120
    refused(
        lambda: module.summarize_samples([], active, 300, 6000),
        "insufficient-energy-evidence",
    )
    refused(
        lambda: module.estimate_monthly_cost(120, 0.20, 25, 30),
        "invalid-telemetry-value",
    )

    assert module.validate_origin("http://127.0.0.1:11434") == "http://127.0.0.1:11434"
    assert module.validate_origin("http://[::1]:11434") == "http://[::1]:11434"
    assert module.normalize_digest("a" * 64) == "a" * 64
    assert module.normalize_digest("sha256:" + "a" * 64) == "a" * 64
    refused(
        lambda: module.validate_origin("https://example.com"),
        "unsafe-provider-origin",
    )
    refused(
        lambda: module.validate_origin("http://" + "user:pass@" + "127.0.0.1:11434"),
        "unsafe-provider-origin",
    )

    with mock.patch.object(module.shutil, "which", return_value="nvidia-smi"), mock.patch.object(
        module, "_run", return_value="125.5, 87, 6144, 68\n"
    ):
        sample = module.NvidiaSampler("0").sample(task="general.chat")
    assert sample.watts == 125.5
    assert sample.utilization_percent == 87
    assert sample.memory_used_mib == 6144
    assert sample.temperature_celsius == 68
    assert sample.task == "general.chat"

    amd_payload = json.dumps([{
        "gpu": 0,
        "power": {"socket_power": {"value": 173, "unit": "W"}},
        "usage": {"gfx_activity": {"value": 91, "unit": "%"}},
        "memory": {"vram_used": {"value": 8192, "unit": "MiB"}},
        "temperature": {"edge_temperature": {"value": 71, "unit": "C"}},
    }])
    with mock.patch.object(module.shutil, "which", return_value="amd-smi"), mock.patch.object(
        module, "_run", return_value=amd_payload
    ):
        sample = module.AmdSampler("0").sample()
    assert (sample.watts, sample.utilization_percent, sample.memory_used_mib) == (173, 91, 8192)

    intel_payload = json.dumps({
        "device_level": {
            "GPU Power (W)": {"value": 109, "unit": "W"},
            "GPU Utilization (%)": {"value": 76, "unit": "%"},
            "GPU Memory Used (MiB)": {"value": 7168, "unit": "MiB"},
            "GPU Core Temperature (C)": {"value": 62, "unit": "C"},
        }
    })
    with mock.patch.object(module.shutil, "which", return_value="xpu-smi"), mock.patch.object(
        module, "_run", return_value=intel_payload
    ):
        sample = module.IntelSampler("0").sample()
    assert (sample.watts, sample.utilization_percent, sample.memory_used_mib) == (109, 76, 7168)

    class FixedSampler(module.TelemetrySampler):
        vendor = "nvidia"
        source = "nvidia-smi"

        def __init__(self, watts: float) -> None:
            self.watts = watts

        def sample(self, *, task=None):
            return module.PowerSample(1.0, self.watts, 80, 1024, 60, task)

    composite = module.CompositeSampler([FixedSampler(100), FixedSampler(125)])
    combined = composite.sample(task="content.write")
    assert combined.watts == 225
    assert combined.device_watts == (100, 125)
    assert combined.memory_used_mib == 2048
    multi_metrics = module.summarize_samples(
        idle,
        [
            module.PowerSample(1, 225, task="general.chat", device_watts=(100, 125)),
            module.PowerSample(2, 235, task="content.write", device_watts=(110, 125)),
        ],
        300,
        6000,
    )
    assert multi_metrics["perDeviceLoadAverageWatts"] == [105.0, 125.0]
    assert multi_metrics["perDeviceLoadPeakWatts"] == [110, 125]

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schemaVersion"] == 1
    assert contract["interpretation"]["wholeComputerEstimateAllowed"] is False
    assert contract["interpretation"]["automaticModelPromotionAllowed"] is False
    assert contract["interpretation"]["deviceIdentifiersMayBePersisted"] is False
    assert contract["measurementFloor"] == {
        "idleBaselineSeconds": 120,
        "activeMeasurementSeconds": 300,
        "maximumSamplingIntervalSeconds": 10,
        "minimumSamplingCompletenessPercent": 80,
    }

    source = SCRIPT.read_text(encoding="utf-8")
    assert "shell=False" in source
    assert '"containsProviderEndpoint": False' in source
    assert '"automaticPromotionAllowed": False' in source
    assert "HSA_OVERRIDE_GFX_VERSION" not in source
    assert "CUDA_VISIBLE_DEVICES" not in source

    with tempfile.TemporaryDirectory() as directory:
        cost_module = load_path("alpha2_energy_cost", COST_SCRIPT)
        path = Path(directory) / "evidence.json"
        evidence = {
            "schemaVersion": 1,
            "kind": "haven42-model-energy-measurement",
            "outcome": "passed",
            "identity": {"model": "fixture:1b"},
            "environment": {"acceleratorModel": "Fixture GPU"},
            "metrics": {"loadAverageWatts": 120},
            "evidence": {
                "containsRawPromptsOrResponses": False,
                "containsPrivateMachineIdentity": False,
                "containsProviderEndpoint": False,
                "automaticPromotionAllowed": False,
            },
        }
        path.write_text(json.dumps(evidence), encoding="utf-8")
        loaded = cost_module.load_evidence(path)
        estimate = cost_module.calculate(
            loaded, rate=0.20, hours=2, days=30, currency="USD",
            additional_system_watts=80,
        )
        assert estimate["estimatedGpuOnlyCost"] == 1.44
        assert estimate["estimatedCombinedCost"] == 2.40
        assert estimate["combinedEstimateUsesOperatorProvidedSystemOverhead"] is True

    with tempfile.TemporaryDirectory() as directory:
        campaign_module = load_path("alpha2_energy_campaign", CAMPAIGN_SCRIPT)
        directory_path = Path(directory)
        digest = "a" * 64
        specs_path = directory_path / "models.json"
        specs_path.write_text(json.dumps([{
            "id": "fixture-1b-q4",
            "model": "fixture:1b-q4",
            "manifestDigest": digest,
        }]), encoding="utf-8")
        specs = campaign_module.load_specs(specs_path, set())
        assert specs == [{
            "id": "fixture-1b-q4",
            "model": "fixture:1b-q4",
            "manifestDigest": digest,
        }]
        refused(
            lambda: campaign_module.load_specs(specs_path, {"missing-model"}),
            "requested-model-not-in-specs",
        )
        campaign_args = argparse.Namespace(
            origin="http://127.0.0.1:11434",
            runtime_version="fixture-runtime",
            vendor="nvidia",
            device="0",
            accelerator_model="Fixture GPU",
            driver_version="fixture-driver",
            operating_system="Fixture OS",
            idle_seconds=120,
            active_seconds=300,
            sample_interval=1,
            electricity_rate=None,
            currency="USD",
            usage_hours_per_day=2,
            billing_days=30,
        )
        command = campaign_module.build_command(
            campaign_args, specs[0], directory_path / "fixture.json",
        )
        assert command[0] == sys.executable
        assert "--expected-digest" in command
        assert digest in command
        assert "--electricity-rate" not in command

    campaign_source = CAMPAIGN_SCRIPT.read_text(encoding="utf-8")
    assert "shell=False" in campaign_source
    assert "automaticPromotionAllowed\": False" in campaign_source
    assert "subprocess.run" in campaign_source

    print("alpha2 model energy measurement checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
