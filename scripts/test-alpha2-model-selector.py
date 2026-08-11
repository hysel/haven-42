#!/usr/bin/env python3
"""Hostile offline tests for the Alpha 2 model selector."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
SELECTOR = ROOT / "scripts" / "alpha2_model_selector.py"
POLICY = ROOT / "config" / "alpha-2-model-selection-policy.json"
CASES = ROOT / "examples" / "fixtures" / "alpha-2-model-selection-cases.json"
SPEC = importlib.util.spec_from_file_location("alpha2_model_selector", SELECTOR)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
WINDOWS_SPEC = importlib.util.spec_from_file_location(
    "alpha2_selector_windows_baseline", ROOT / "scripts" / "windows_alpha.py"
)
WINDOWS = importlib.util.module_from_spec(WINDOWS_SPEC)
assert WINDOWS_SPEC.loader is not None
sys.modules[WINDOWS_SPEC.name] = WINDOWS
WINDOWS_SPEC.loader.exec_module(WINDOWS)


def imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".", 1)[0])
    return result


def profile(**updates: object) -> dict:
    value = {
        "platformFamily": "linux",
        "operatingSystemId": "ubuntu-26-04",
        "architecture": "x64",
        "backendMode": "cuda",
        "systemMemoryGiB": 24,
        "usableGpuMemoryGiB": 16,
        "storageAdmittedModelIds": [
            "qwen35-08b-q8", "qwen35-2b-q8", "qwen35-4b-q4", "qwen35-9b-q4"
        ],
        "requestedCapabilities": [
            "general.chat", "content.write", "content.summarize"
        ],
        "provider": "ollama",
        "providerVersion": "0.32.5",
    }
    value.update(updates)
    return value


def evidence(model_id: str, digest: str, **updates: object) -> dict:
    policy, _ = MODULE.load_policy()
    value = {
        "evidenceId": f"linux-cuda-{model_id}",
        "modelId": model_id,
        "manifestDigest": digest,
        "platformFamily": "linux",
        "operatingSystemId": "ubuntu-26-04",
        "architecture": "x64",
        "backendMode": "cuda",
        "provider": "ollama",
        "providerVersion": "0.32.5",
        "selectorPolicyCanonicalSha256": MODULE.canonical_sha256(policy),
        "minimumTestedSystemMemoryGiB": 16,
        "minimumTestedUsableGpuMemoryGiB": 16,
        "capabilities": ["general.chat", "content.write", "content.summarize"],
        "status": "passed",
    }
    value.update(updates)
    return value


def windows_snapshot(ram: float, gpu: float | None) -> dict:
    accelerators = [] if gpu is None else [{
        "vendor": "NVIDIA",
        "model": "Synthetic GPU",
        "memoryGiB": gpu,
        "memoryType": "dedicated",
        "state": "detected",
        "source": "synthetic",
        "confidence": "high",
    }]
    return {
        "platform": {
            "operatingSystem": "windows",
            "productName": "Windows 11 Pro",
            "architecture": "AMD64",
            "logicalProcessors": 8,
            "systemMemoryGiB": ram,
            "availableStorageGiB": 100,
        },
        "accelerators": accelerators,
    }


def refused(action, text: str) -> None:
    try:
        action()
    except MODULE.SelectionError as error:
        assert text in str(error), str(error)
    else:
        raise AssertionError("Unsafe input was accepted.")


def main() -> int:
    policy, catalog = MODULE.load_policy()
    by_id = {item["id"]: item for item in catalog["models"]}
    checks = 2
    assert policy["status"] == "evidence-collection-no-new-product-promotion"
    assert len(policy["comparisonCandidates"]) == 4
    checks += 2

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    assert set(cases) == {
        "schemaVersion", "kind", "productAdmission", "description", "cases"
    }
    assert cases["schemaVersion"] == 1
    assert cases["kind"] == "alpha2-model-selection-synthetic-fixtures"
    assert cases["productAdmission"] is False
    assert isinstance(cases["cases"], list) and len(cases["cases"]) == 9
    for case in cases["cases"]:
        case_profile = case["profile"]
        records = [
            evidence(
                model_id,
                by_id[model_id]["manifestDigest"],
                evidenceId=f"{case['id']}-{model_id}",
                platformFamily=case_profile["platformFamily"],
                operatingSystemId=case_profile["operatingSystemId"],
                architecture=case_profile["architecture"],
                backendMode=case_profile["backendMode"],
                providerVersion=case_profile["providerVersion"],
                minimumTestedSystemMemoryGiB=case_profile["systemMemoryGiB"],
                minimumTestedUsableGpuMemoryGiB=case_profile["usableGpuMemoryGiB"],
                capabilities=case_profile["requestedCapabilities"],
            )
            for model_id in case["evidencedModelIds"]
        ]
        result = MODULE.select_model(case_profile, records)
        assert result["selectedModelId"] == case["expectedModelId"], case["id"]
        assert result["downloadsPerformed"] is False
        assert result["fallbackPerformed"] is False
    checks += 4 + len(cases["cases"]) * 3

    crlf_catalog = json.loads(json.dumps(catalog, indent=2).replace("\n", "\r\n"))
    canonical = json.dumps(
        crlf_catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == policy["sourceCatalog"]["canonicalSha256"]
    checks += 1

    windows_qwen9 = WINDOWS.select_model(windows_snapshot(24, 16))
    assert windows_qwen9["selected"]["id"] == "qwen35-9b-q4"
    assert windows_qwen9["automaticExecutionAllowed"] is True
    qwen9_model = by_id["qwen35-9b-q4"]
    shared_windows_qwen9 = MODULE.select_model(
        profile(platformFamily="windows", operatingSystemId="windows-11"),
        [
            evidence(
                qwen9_model["id"],
                qwen9_model["manifestDigest"],
                platformFamily="windows",
                operatingSystemId="windows-11",
            )
        ],
    )
    assert shared_windows_qwen9["selectedModelId"] == windows_qwen9["selected"]["id"]
    windows_qwen4 = WINDOWS.select_model(windows_snapshot(16, 8))
    assert windows_qwen4["selected"]["id"] == "qwen35-4b-q4"
    assert windows_qwen4["automaticExecutionAllowed"] is False
    assert MODULE.select_model(
        profile(
            platformFamily="windows",
            operatingSystemId="windows-11",
            systemMemoryGiB=16,
            usableGpuMemoryGiB=8,
            storageAdmittedModelIds=["qwen35-08b-q8", "qwen35-2b-q8", "qwen35-4b-q4"],
        ),
        [],
    )["selectedModelId"] is None
    checks += 7

    forbidden = {"asyncio", "http", "os", "requests", "socket", "subprocess", "urllib"}
    assert imports(SELECTOR).isdisjoint(forbidden)
    source = SELECTOR.read_text(encoding="utf-8")
    assert all(item not in source for item in ("shell=True", "os.system", "Popen("))
    checks += 2

    no_evidence = MODULE.select_model(profile(), [])
    assert no_evidence["decision"] == "no-validated-model"
    assert no_evidence["selectedModelId"] is None
    assert no_evidence["automaticExecutionAllowed"] is False
    assert no_evidence["downloadsPerformed"] is False
    assert no_evidence["fallbackPerformed"] is False
    checks += 5

    qwen4 = by_id["qwen35-4b-q4"]
    qwen9 = by_id["qwen35-9b-q4"]
    admitted = MODULE.select_model(
        profile(),
        [
            evidence(qwen4["id"], qwen4["manifestDigest"]),
            evidence(qwen9["id"], qwen9["manifestDigest"]),
        ],
    )
    assert admitted["selectedModelId"] == "qwen35-9b-q4"
    assert admitted["automaticExecutionAllowed"] is True
    checks += 2

    insufficient_ram = MODULE.select_model(
        profile(systemMemoryGiB=16),
        [evidence(qwen9["id"], qwen9["manifestDigest"])],
    )
    assert insufficient_ram["selectedModelId"] is None
    checks += 1
    insufficient_gpu = MODULE.select_model(
        profile(usableGpuMemoryGiB=8),
        [evidence(qwen9["id"], qwen9["manifestDigest"])],
    )
    assert insufficient_gpu["selectedModelId"] is None
    checks += 1
    qwen08 = by_id["qwen35-08b-q8"]
    below_tested_ram = MODULE.select_model(
        profile(
            systemMemoryGiB=15,
            storageAdmittedModelIds=["qwen35-08b-q8"],
        ),
        [evidence(qwen08["id"], qwen08["manifestDigest"])],
    )
    assert below_tested_ram["selectedModelId"] is None
    checks += 1
    storage_denied = MODULE.select_model(
        profile(storageAdmittedModelIds=["qwen35-08b-q8"]),
        [evidence(qwen9["id"], qwen9["manifestDigest"])],
    )
    assert storage_denied["selectedModelId"] is None
    checks += 1

    wrong_platform = evidence(qwen9["id"], qwen9["manifestDigest"], platformFamily="windows")
    assert MODULE.select_model(profile(), [wrong_platform])["selectedModelId"] is None
    wrong_os = evidence(
        qwen9["id"], qwen9["manifestDigest"], operatingSystemId="fedora-44"
    )
    assert MODULE.select_model(profile(), [wrong_os])["selectedModelId"] is None
    wrong_backend = evidence(qwen9["id"], qwen9["manifestDigest"], backendMode="rocm")
    assert MODULE.select_model(profile(), [wrong_backend])["selectedModelId"] is None
    wrong_version = evidence(qwen9["id"], qwen9["manifestDigest"], providerVersion="0.32.6")
    assert MODULE.select_model(profile(), [wrong_version])["selectedModelId"] is None
    partial = evidence(
        qwen9["id"], qwen9["manifestDigest"], capabilities=["general.chat", "content.write"]
    )
    assert MODULE.select_model(profile(), [partial])["selectedModelId"] is None
    checks += 5

    bad_digest = evidence(qwen9["id"], "0" * 64)
    refused(lambda: MODULE.select_model(profile(), [bad_digest]), "Invalid exact-profile evidence")
    stale_policy = evidence(
        qwen9["id"], qwen9["manifestDigest"], selectorPolicyCanonicalSha256="0" * 64
    )
    refused(
        lambda: MODULE.select_model(profile(), [stale_policy]),
        "Invalid exact-profile evidence",
    )
    bad_memory_floor = evidence(
        qwen9["id"], qwen9["manifestDigest"], minimumTestedSystemMemoryGiB=0
    )
    refused(
        lambda: MODULE.select_model(profile(), [bad_memory_floor]),
        "Invalid exact-profile evidence",
    )
    checks += 2
    bad_cpu = profile(backendMode="cpu", usableGpuMemoryGiB=1)
    refused(lambda: MODULE.select_model(bad_cpu, []), "CPU profile")
    unknown_storage = profile(storageAdmittedModelIds=["unknown"])
    refused(lambda: MODULE.select_model(unknown_storage, []), "Invalid profile admission")
    duplicate_capability = profile(requestedCapabilities=["general.chat", "general.chat"])
    refused(lambda: MODULE.select_model(duplicate_capability, []), "Invalid profile admission")
    checks += 4

    changed_policy = copy.deepcopy(policy)
    changed_policy["selectionPolicy"]["silentCpuFallbackAllowed"] = True
    refused(lambda: MODULE.validate_policy(changed_policy), "Invalid Alpha 2")
    changed_policy = copy.deepcopy(policy)
    changed_policy["comparisonCandidates"][0]["automaticPromotionAllowed"] = True
    refused(lambda: MODULE.validate_policy(changed_policy), "Invalid comparison")
    checks += 2

    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "policy.json"
        changed_policy = copy.deepcopy(policy)
        changed_policy["sourceCatalog"]["canonicalSha256"] = "0" * 64
        path.write_text(json.dumps(changed_policy), encoding="utf-8")
        refused(lambda: MODULE.load_policy(path), "Source catalog")
    checks += 1

    combined = json.dumps(policy) + source
    assert "192.168." not in combined
    assert "SHA256:" not in combined
    assert "QuadroRTX5000" not in combined
    checks += 3
    print(f"Alpha 2 model selector passed {checks} hostile offline checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
