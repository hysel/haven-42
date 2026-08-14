#!/usr/bin/env python3
"""Fail-closed checks for the shared Alpha platform adapter boundary."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
ADAPTER = importlib.import_module("alpha_platform")


def rejected(function, value, expected: str) -> None:
    try:
        function(value)
    except ADAPTER.PlatformAdapterError as error:
        assert str(error) == expected
    else:
        raise AssertionError(f"accepted unsafe adapter value: {value!r}")


def main() -> int:
    fixture = json.loads(
        (ROOT / "examples/fixtures/alpha-platform-adapter-cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture["schemaVersion"] == 1
    required_shared = {"readiness.inspect", "provider.metrics.validate"}
    required_managed = {
        "component-registry.load", "driver.guidance", "hardware.evaluate",
        "model-catalog.load", "model.select", "setup.approve", "setup.execute",
        "setup.plan", "setup.remove", "setup.resume",
    }
    for case in fixture["supported"]:
        adapter = ADAPTER.resolve_platform_adapter(case["platformId"])
        summary = adapter.public_summary()
        assert summary["schemaVersion"] == 1
        assert summary["platformId"] == case["platformId"]
        assert summary["platformFamily"] == case["platformFamily"]
        assert summary["managedSetupSupported"] is case["managedSetupSupported"]
        assert set(summary["supportedOperations"]) == required_shared | required_managed
        for operation_id in summary["supportedOperations"]:
            assert adapter.require(operation_id) is None

    for platform_id in fixture["rejectedPlatformIds"]:
        rejected(
            ADAPTER.resolve_platform_adapter,
            platform_id,
            "unsupported-platform-adapter",
        )
    linux = ADAPTER.resolve_platform_adapter("linux-x64")
    for operation_id in fixture["rejectedOperationIds"]:
        rejected(linux.require, operation_id, "unsupported-platform-operation")

    summary = ADAPTER.ACTIVE_PLATFORM_ADAPTER.public_summary()
    assert summary["platformId"] in {"windows-x64", "linux-x64", "shared-ui-only"}
    assert "command" not in json.dumps(summary).casefold()
    assert "path" not in json.dumps(summary).casefold()
    assert "environment" not in json.dumps(summary).casefold()
    if os.name == "nt":
        windows_alpha = importlib.import_module("windows_alpha")
        windows_setup = importlib.import_module("windows_alpha_setup")
        assert ADAPTER.evaluate_hardware is windows_alpha.evaluate_hardware
        assert ADAPTER.select_model is windows_alpha.select_model
        assert ADAPTER.driver_guidance is windows_alpha.driver_guidance
        assert ADAPTER.SetupCoordinator is windows_setup.SetupCoordinator
        assert ADAPTER.build_plan is windows_setup.build_plan
    elif sys.platform.startswith("linux"):
        linux_alpha = importlib.import_module("linux_alpha")
        linux_setup = importlib.import_module("linux_alpha_setup")
        assert ADAPTER.evaluate_hardware is linux_alpha.evaluate_hardware
        assert ADAPTER.select_model is linux_alpha.select_model
        assert ADAPTER.driver_guidance is linux_alpha.driver_guidance
        assert ADAPTER.SetupCoordinator is linux_setup.SetupCoordinator
    print("Alpha platform adapter checks passed: exact platforms and operations only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
