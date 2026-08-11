#!/usr/bin/env python3
"""Contract checks for the sanitized Linux application-level smoke tool."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "alpha2_linux_web_smoke", ROOT / "scripts/alpha2-linux-web-smoke.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def reply() -> dict:
    return {
        "capabilityId": "general.chat",
        "content": "Local response.",
        "modelDigestVerified": True,
        "modelUnloaded": True,
        "context": {
            "providerTrustScope": "loopback",
            "persisted": False,
            "filesystemAccessAllowed": False,
            "toolInvocationAllowed": False,
        },
        "runDetails": {
            "providerReported": True,
            "inputTokens": 10,
            "outputTokens": 5,
            "totalTokens": 15,
            "tokensPerSecond": 20.0,
        },
    }


def refused(value: dict, code: str) -> None:
    try:
        MODULE._metrics(value, "general.chat")
    except MODULE.SmokeError as error:
        assert str(error) == code, (str(error), code)
    else:
        raise AssertionError(f"Expected {code}")


def main() -> int:
    valid = reply()
    assert MODULE._metrics(valid, "general.chat")["modelUnloaded"] is True
    contract_mutations = [
        ("content", ""),
        ("modelDigestVerified", False),
        ("modelUnloaded", False),
    ]
    for key, value in contract_mutations:
        hostile = copy.deepcopy(valid)
        hostile[key] = value
        refused(hostile, "haven-text-contract-failed")
    for key, value in (
        ("providerTrustScope", "lan"),
        ("persisted", True),
        ("filesystemAccessAllowed", True),
        ("toolInvocationAllowed", True),
    ):
        hostile = copy.deepcopy(valid)
        hostile["context"][key] = value
        refused(hostile, "haven-text-contract-failed")
    for key, value in (
        ("inputTokens", 0), ("outputTokens", False), ("totalTokens", -1),
        ("tokensPerSecond", 0), ("tokensPerSecond", float("nan")),
    ):
        hostile = copy.deepcopy(valid)
        hostile["runDetails"][key] = value
        refused(hostile, "haven-text-metrics-invalid")
    try:
        MODULE.run(
            private_root=Path("."), model="invented:latest",
            operating_system_id="bazzite-44",
        )
    except MODULE.SmokeError as error:
        assert str(error) == "unreviewed-smoke-profile"
    else:
        raise AssertionError("Unreviewed model was accepted")
    print("Alpha 2 Linux web smoke checks passed: 15")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
