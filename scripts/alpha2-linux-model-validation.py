#!/usr/bin/env python3
"""Run one bounded, sanitized Alpha 2 model/capability validation cell.

The tool contacts only an IPv4-loopback Ollama endpoint, accepts only reviewed
model and capability identifiers, never prints model output, and unloads the
model after every sample. It does not download models or change a machine.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "config/alpha-2-model-catalog.json"
POLICY_PATH = ROOT / "config/alpha-2-model-selection-policy.json"
COMPARISON_CONTRACT_PATH = ROOT / "config/alpha-2-model-comparison-contract.json"
QUALIFICATION_INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
MANAGED_PROVIDER_VERSION = "0.32.5"
QUALIFICATION_PROVIDER_VERSION = "0.32.14"
CAPABILITIES = {
    "general.chat": "Answer with one short sentence confirming that a local service is responding.",
    "content.write": "Write one concise sentence encouraging careful software testing.",
    "content.summarize": (
        "Summarize this in one short sentence: A portable application keeps its "
        "managed runtime and model beside the application so removal is clear."
    ),
}
SAFE_PROFILE = re.compile(r"^[a-z0-9][a-z0-9.-]{0,79}$")
SAFE_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}$")
SAFE_MODEL_NAME = re.compile(
    r"^[a-z0-9][a-z0-9._/-]{0,79}:[0-9A-Za-z][0-9A-Za-z._-]{0,79}$"
)
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
ACCELERATED_BACKENDS = {"cuda", "rocm", "vulkan"}


class ValidationError(ValueError):
    """The provider or requested evidence cell failed closed."""


def _load(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise ValidationError("unsafe-reviewed-metadata")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError("invalid-reviewed-metadata") from error
    if not isinstance(value, dict):
        raise ValidationError("invalid-reviewed-metadata")
    return value


def _canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _comparison_contract(policy: dict[str, Any]) -> dict[str, Any]:
    contract = _load(COMPARISON_CONTRACT_PATH)
    required = {
        "schemaVersion", "contractId", "release", "status",
        "selectionPolicyBinding", "provider", "candidates", "constraints",
    }
    expected_constraints = {
        "selectionEvidenceAllowed": False,
        "automaticDefaultChangeAllowed": False,
        "downloadsAllowed": False,
        "rawPromptsOrResponsesAllowed": False,
        "unloadAfterEverySampleRequired": True,
        "exactManifestDigestRequired": True,
        "exactProviderVersionRequired": True,
    }
    binding = contract.get("selectionPolicyBinding")
    provider = contract.get("provider")
    if (
        set(contract) != required
        or contract.get("schemaVersion") != 1
        or contract.get("contractId") != "haven42.alpha2.model-comparison"
        or contract.get("release") != "0.4.0-alpha.2"
        or contract.get("status") != "comparison-only-no-product-promotion"
        or binding != {
            "path": "config/alpha-2-model-selection-policy.json",
            "canonicalSha256": _canonical_sha256(policy),
        }
        or provider != {
            "name": "ollama",
            "exactVersion": "0.32.6",
            "transport": "verified-no-command-ipv4-loopback-tunnel",
        }
        or contract.get("constraints") != expected_constraints
        or contract.get("candidates") != policy.get("comparisonCandidates")
    ):
        raise ValidationError("invalid-comparison-contract")
    return contract


def reviewed_model(model_id: str) -> tuple[dict[str, Any], str, str]:
    catalog = _load(CATALOG_PATH)
    policy = _load(POLICY_PATH)
    models = catalog.get("models")
    fit_matches = [
        item for item in models if item.get("id") == model_id
    ] if isinstance(models, list) else []
    comparisons = policy.get("comparisonCandidates")
    comparison_matches = [
        item for item in comparisons if item.get("id") == model_id
    ] if isinstance(comparisons, list) else []
    if policy.get("policyId") != "haven42.alpha2.model-selection":
        raise ValidationError("unreviewed-model-cell")
    if len(fit_matches) == 1 and model_id in policy.get("fitLadder", [])[:3]:
        model = dict(fit_matches[0])
        model["automaticEvidenceCandidate"] = True
        return model, _canonical_sha256(policy), MANAGED_PROVIDER_VERSION
    comparison_contract = _comparison_contract(policy)
    contract_matches = [
        item for item in comparison_contract["candidates"] if item.get("id") == model_id
    ]
    if len(comparison_matches) == 1 and len(contract_matches) == 1:
        comparison = contract_matches[0]
        if comparison.get("automaticPromotionAllowed") is not False:
            raise ValidationError("unreviewed-model-cell")
        return {
            "id": comparison["id"],
            "name": comparison["model"],
            "manifestDigest": comparison["digest"],
            "automaticEvidenceCandidate": False,
        }, _canonical_sha256(policy), comparison_contract["provider"]["exactVersion"]
    raise ValidationError("unreviewed-model-cell")


def reviewed_qualification_model(model_id: str) -> tuple[dict[str, Any], str, str]:
    """Resolve one exact candidate without granting selector-evidence status."""

    inventory = _load(QUALIFICATION_INVENTORY_PATH)
    rules = inventory.get("rules")
    provider = inventory.get("qualificationProvider")
    if (
        inventory.get("schemaVersion") != 1
        or inventory.get("inventoryId") != "haven42.alpha2.model-family-versions"
        or inventory.get("release") != "0.4.0-alpha.2"
        or inventory.get("status") != "qualification-inventory-not-selection-policy"
        or not isinstance(rules, dict)
        or rules.get("officialPrimarySourcesOnly") is not True
        or rules.get("exactManifestDigestRequiredBeforeExecution") is not True
        or rules.get("mutableLatestTagsAllowed") is not False
        or rules.get("automaticPromotionAllowed") is not False
        or rules.get("rawPromptsOrResponsesAllowed") is not False
        or rules.get("unloadAfterEverySampleRequired") is not True
        or provider != {
            "name": "ollama",
            "exactVersion": QUALIFICATION_PROVIDER_VERSION,
            "transport": "ipv4-loopback-only",
        }
    ):
        raise ValidationError("invalid-qualification-inventory")
    families = inventory.get("families")
    if not isinstance(families, list):
        raise ValidationError("invalid-qualification-inventory")
    matches: list[dict[str, Any]] = []
    for family in families:
        versions = family.get("versions") if isinstance(family, dict) else None
        if not isinstance(versions, list):
            raise ValidationError("invalid-qualification-inventory")
        for version in versions:
            candidates = version.get("candidates", []) if isinstance(version, dict) else None
            if not isinstance(candidates, list):
                raise ValidationError("invalid-qualification-inventory")
            matches.extend(
                candidate for candidate in candidates
                if isinstance(candidate, dict) and candidate.get("id") == model_id
            )
    if len(matches) != 1:
        raise ValidationError("unreviewed-qualification-model")
    candidate = matches[0]
    name = candidate.get("model")
    digest = candidate.get("manifestDigest")
    model_bytes = candidate.get("modelBytes")
    download_bytes = candidate.get("downloadBytes")
    if (
        not isinstance(name, str)
        or not SAFE_MODEL_NAME.fullmatch(name)
        or name.endswith(":latest")
        or not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        or isinstance(model_bytes, bool)
        or not isinstance(model_bytes, int)
        or model_bytes <= 0
        or (
            download_bytes is not None
            and (
                isinstance(download_bytes, bool)
                or not isinstance(download_bytes, int)
                or download_bytes < model_bytes
            )
        )
    ):
        raise ValidationError("invalid-qualification-inventory")
    return {
        "id": model_id,
        "name": name,
        "manifestDigest": digest,
        "modelBytes": model_bytes,
        "downloadBytes": download_bytes,
        "automaticEvidenceCandidate": False,
        "qualificationOnly": True,
    }, _canonical_sha256(inventory), provider["exactVersion"]


def validate_origin(origin: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError as error:
        raise ValidationError("invalid-loopback-origin") from error
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.port is None
        or not 1024 <= parsed.port <= 65535
    ):
        raise ValidationError("invalid-loopback-origin")
    return f"http://127.0.0.1:{parsed.port}"


def _json_request(
    origin: str, route: str, body: dict[str, Any] | None = None, timeout: int = 300,
) -> dict[str, Any]:
    if route not in {"/api/version", "/api/tags", "/api/generate", "/api/ps"}:
        raise ValidationError("invalid-provider-route")
    encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        origin + route,
        data=encoded,
        headers={"Content-Type": "application/json", "User-Agent": "Haven42-Alpha2-Validation/1"},
        method="GET" if encoded is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise ValidationError("provider-request-failed") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValidationError("provider-response-too-large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError("invalid-provider-response") from error
    if not isinstance(value, dict) or value.get("error"):
        raise ValidationError("invalid-provider-response")
    return value


def verify_provider(
    origin: str, model: dict[str, Any], expected_version: str,
) -> None:
    version = _json_request(origin, "/api/version", timeout=10)
    if version != {"version": expected_version}:
        raise ValidationError("provider-version-mismatch")
    tags = _json_request(origin, "/api/tags", timeout=30)
    records = tags.get("models")
    matches = [item for item in records if isinstance(item, dict) and item.get("name") == model["name"]] if isinstance(records, list) else []
    if len(matches) != 1:
        raise ValidationError("registered-model-not-installed")
    digest = matches[0].get("digest")
    if isinstance(digest, str) and digest.startswith("sha256:"):
        digest = digest[7:]
    if digest != model["manifestDigest"]:
        raise ValidationError("model-manifest-digest-mismatch")


def _validate_generate(value: dict[str, Any]) -> tuple[int, int, float]:
    response = value.get("response")
    eval_count = value.get("eval_count")
    prompt_count = value.get("prompt_eval_count")
    eval_duration = value.get("eval_duration")
    if (
        value.get("done") is not True
        or not isinstance(response, str)
        or not response.strip()
        or len(response.encode("utf-8")) > 64 * 1024
        or isinstance(eval_count, bool)
        or not isinstance(eval_count, int)
        or not 1 <= eval_count <= 256
        or isinstance(prompt_count, bool)
        or not isinstance(prompt_count, int)
        or not 1 <= prompt_count <= 100_000
        or isinstance(eval_duration, bool)
        or not isinstance(eval_duration, int)
        or eval_duration <= 0
    ):
        raise ValidationError("inference-response-contract-failed")
    tokens_per_second = eval_count / (eval_duration / 1_000_000_000)
    if not math.isfinite(tokens_per_second) or not 0 < tokens_per_second <= 1_000_000:
        raise ValidationError("inference-metrics-invalid")
    return prompt_count, eval_count, tokens_per_second


def _verify_residency(origin: str, model: dict[str, Any], backend: str) -> int:
    processes = _json_request(origin, "/api/ps", timeout=10).get("models")
    matches = [item for item in processes if isinstance(item, dict) and item.get("name") == model["name"]] if isinstance(processes, list) else []
    if len(matches) != 1:
        raise ValidationError("model-residency-not-observed")
    size = matches[0].get("size")
    size_vram = matches[0].get("size_vram")
    if (
        isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or isinstance(size_vram, bool)
        or not isinstance(size_vram, int)
        or size_vram < 0
        or size_vram > size
    ):
        raise ValidationError("model-residency-invalid")
    if backend in ACCELERATED_BACKENDS and size_vram != size:
        raise ValidationError(f"{backend}-full-residency-not-observed")
    if backend == "cpu" and size_vram != 0:
        raise ValidationError("cpu-cell-used-gpu")
    return size_vram


def _unload(origin: str, model: dict[str, Any]) -> None:
    _json_request(
        origin,
        "/api/generate",
        {"model": model["name"], "keep_alive": 0, "stream": False},
        timeout=30,
    )
    for _ in range(40):
        records = _json_request(origin, "/api/ps", timeout=10).get("models")
        if isinstance(records, list) and not any(
            isinstance(item, dict) and item.get("name") == model["name"]
            for item in records
        ):
            return
        time.sleep(0.25)
    raise ValidationError("model-unload-timeout")


def run_cell(
    *, origin: str, model_id: str, capability: str, operating_system_id: str,
    backend: str, system_memory_gib: float, usable_gpu_memory_gib: float,
    provider_version: str | None = None, repetitions: int = 3,
    qualification_inventory: bool = False, platform_family: str = "linux",
) -> dict[str, Any]:
    origin = validate_origin(origin)
    if not isinstance(qualification_inventory, bool):
        raise ValidationError("invalid-qualification-mode")
    resolver = reviewed_qualification_model if qualification_inventory else reviewed_model
    model, binding_sha, reviewed_provider_version = resolver(model_id)
    if provider_version is None:
        provider_version = reviewed_provider_version
    if capability not in CAPABILITIES:
        raise ValidationError("unreviewed-capability")
    if not SAFE_PROFILE.fullmatch(operating_system_id):
        raise ValidationError("invalid-operating-system-id")
    if platform_family not in {"linux", "windows"}:
        raise ValidationError("unreviewed-platform-family")
    if backend not in {"cpu", *ACCELERATED_BACKENDS}:
        raise ValidationError("unreviewed-backend")
    if (
        not isinstance(provider_version, str)
        or not SAFE_VERSION.fullmatch(provider_version)
        or provider_version != reviewed_provider_version
    ):
        raise ValidationError("unreviewed-provider-version")
    if repetitions != 3:
        raise ValidationError("invalid-repetition-count")
    for value in (system_memory_gib, usable_gpu_memory_gib):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1024:
            raise ValidationError("invalid-memory-measurement")
    if backend == "cpu" and usable_gpu_memory_gib != 0:
        raise ValidationError("cpu-cell-gpu-memory-mismatch")
    verify_provider(origin, model, provider_version)
    started = time.monotonic()
    prompt_tokens = output_tokens = unloads = 0
    rates: list[float] = []
    peak_vram = 0
    for _ in range(repetitions):
        cell_error: ValidationError | None = None
        try:
            generated = _json_request(
                origin,
                "/api/generate",
                {
                    "model": model["name"],
                    "prompt": CAPABILITIES[capability],
                    "stream": False,
                    "think": False,
                    "keep_alive": "5m",
                    "options": {"temperature": 0, "seed": 42, "num_predict": 64},
                },
                timeout=600,
            )
            prompt, output, rate = _validate_generate(generated)
            prompt_tokens += prompt
            output_tokens += output
            rates.append(rate)
            peak_vram = max(peak_vram, _verify_residency(origin, model, backend))
        except ValidationError as error:
            cell_error = error
        try:
            _unload(origin, model)
            unloads += 1
        except ValidationError as unload_error:
            if cell_error is not None:
                raise ValidationError(
                    "model-cell-failed-and-unload-unverified"
                ) from cell_error
            raise unload_error
        if cell_error is not None:
            raise cell_error
    duration = time.monotonic() - started
    evidence = {
        "modelId": model_id,
        "manifestDigest": model["manifestDigest"],
        "platformFamily": platform_family,
        "operatingSystemId": operating_system_id,
        "architecture": "x64",
        "backendMode": backend,
        "provider": "ollama",
        "providerVersion": provider_version,
        "systemMemoryGiB": system_memory_gib,
        "usableGpuMemoryGiB": usable_gpu_memory_gib,
        "storageAdmitted": True,
        "capability": capability,
        "capabilityPassed": True,
        "automaticEvidenceCandidate": model["automaticEvidenceCandidate"],
    }
    if qualification_inventory:
        evidence["qualificationInventoryCanonicalSha256"] = binding_sha
        evidence["qualificationOnly"] = True
    else:
        evidence["selectorPolicyCanonicalSha256"] = binding_sha
    return {
        "outcome": "passed",
        "errorCode": None,
        "durationSeconds": round(duration, 3),
        "metrics": {
            "promptTokens": prompt_tokens,
            "outputTokens": output_tokens,
            "tokensPerSecond": round(sum(rates) / len(rates), 3),
            "peakGpuMemoryBytes": peak_vram,
            "samplesAttempted": repetitions,
            "samplesPassed": repetitions,
            "samplesFailed": 0,
            "unloadPasses": unloads,
        },
        "evidence": evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:11435")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--capability", choices=sorted(CAPABILITIES), required=True)
    parser.add_argument("--operating-system-id", required=True)
    parser.add_argument(
        "--platform-family", choices=["linux", "windows"], default="linux"
    )
    parser.add_argument(
        "--backend", choices=["cpu", "cuda", "rocm", "vulkan"], required=True
    )
    parser.add_argument("--system-memory-gib", type=float, required=True)
    parser.add_argument("--usable-gpu-memory-gib", type=float, required=True)
    parser.add_argument("--qualification-inventory", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run_cell(
            origin=args.origin,
            model_id=args.model_id,
            capability=args.capability,
            operating_system_id=args.operating_system_id,
            backend=args.backend,
            system_memory_gib=args.system_memory_gib,
            usable_gpu_memory_gib=args.usable_gpu_memory_gib,
            qualification_inventory=args.qualification_inventory,
            platform_family=args.platform_family,
        ), indent=2, sort_keys=True))
    except ValidationError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
