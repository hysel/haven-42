#!/usr/bin/env python3
"""Hostile tests for the effect-free quantized-artifact lifecycle."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("quant_lifecycle", ROOT / "scripts/simulate-quantized-artifact-lifecycle.py")
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
BASE = json.loads((ROOT / "examples/fixtures/quantized-artifact-lifecycle-request.json").read_text(encoding="utf-8"))


def rejected(mutate) -> None:
    value = copy.deepcopy(BASE); mutate(value)
    try: MODULE.evaluate(value)
    except MODULE.LifecycleError: return
    raise AssertionError("unsafe quantized-artifact request accepted")


def main() -> None:
    result = MODULE.evaluate(copy.deepcopy(BASE))
    assert result["status"] == "exact-cell-eligible" and result["catalogAdmissionAllowed"]
    assert not any(result["effects"].values())
    mutations = [
        lambda x: x["source"].__setitem__("revision", "main"),
        lambda x: x["source"].__setitem__("repository", "../escape"),
        lambda x: x["source"].__setitem__("sha256", "0" * 63),
        lambda x: x["derivative"].__setitem__("sha256", x["source"]["sha256"]),
        lambda x: x["source"].__setitem__("derivativeAllowed", False),
        lambda x: x["derivative"].__setitem__("license", "different"),
        lambda x: x["derivative"].__setitem__("provenanceComplete", False),
        lambda x: x["recipe"].__setitem__("bits", 7),
        lambda x: x["compatibility"].__setitem__("driver", ""),
        lambda x: x["compatibility"].__setitem__("fullOffloadRequired", False),
        lambda x: x["storage"].__setitem__("availableBytes", 1),
        lambda x: x["validation"].__setitem__("silentFallbackObserved", True),
        lambda x: x.__setitem__("path", "forbidden"),
    ]
    for mutate in mutations: rejected(mutate)

    activation = copy.deepcopy(BASE); activation["operation"] = "plan-activation"; activation["state"]["phase"] = "staged"
    assert MODULE.evaluate(activation)["status"] == "activation-plan-only"
    rollback = copy.deepcopy(BASE); rollback["operation"] = "plan-rollback"; rollback["state"].update({"phase": "rollback-required", "previousArtifactId": "model-known-good"})
    assert MODULE.evaluate(rollback)["status"] == "rollback-plan-only"
    interrupted = copy.deepcopy(BASE); interrupted["operation"] = "recover-interrupted"; interrupted["state"]["phase"] = "converting"
    assert MODULE.evaluate(interrupted)["status"] == "recovery-plan-only"
    cleanup = copy.deepcopy(BASE); cleanup["operation"] = "plan-partial-cleanup"; cleanup["state"].update({"phase": "partial-cleanup", "partialArtifactId": "partial-one"})
    assert MODULE.evaluate(cleanup)["status"] == "partial-cleanup-plan-only"
    print("Quantized artifact lifecycle passed 5 valid and 13 hostile cases.")


if __name__ == "__main__": main()
