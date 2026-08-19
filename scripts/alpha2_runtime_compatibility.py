#!/usr/bin/env python3
"""Resolve an Alpha 2 model to a pinned, engine-specific local runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
INVENTORY = ROOT / "config" / "alpha-2-model-version-inventory.json"
CATALOG = ROOT / "config" / "alpha-2-model-catalog.json"
RUNTIMES = ROOT / "config" / "alpha-2-runtime-compatibility.json"
REQUIREMENTS = ROOT / "config" / "alpha-2-model-runtime-requirements.json"
VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
LLAMA_VERSION = re.compile(r"^b([1-9][0-9]*)$")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,99}$")
PLATFORMS = {"windows-x64", "linux-x64"}
ENGINE_BACKENDS = {
    "ollama": {"core", "rocm"},
    "llama.cpp": {"cpu", "cuda", "cuda-12.4", "rocm", "sycl", "sycl-fp16", "vulkan"},
}


class CompatibilityError(ValueError):
    """A fail-closed runtime compatibility decision."""


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompatibilityError("invalid-compatibility-registry")
    return value


def _version(value: object) -> tuple[int, int, int]:
    match = VERSION.fullmatch(str(value))
    if not match:
        raise CompatibilityError("invalid-runtime-version")
    return tuple(int(part) for part in match.groups())


def _llama_version(value: object) -> int:
    match = LLAMA_VERSION.fullmatch(str(value))
    if not match:
        raise CompatibilityError("invalid-runtime-version")
    return int(match.group(1))


def _registered_candidate(
    inventory: dict[str, Any], catalog: dict[str, Any], model_id: str,
) -> dict[str, Any]:
    matches = [
        candidate
        for family in inventory.get("families", [])
        for release in family.get("versions", [])
        for candidate in release.get("candidates", [])
        if candidate.get("id") == model_id
    ]
    matches.extend(
        candidate
        for candidate in catalog.get("models", [])
        if candidate.get("id") == model_id
    )
    if not matches:
        raise CompatibilityError("model-not-registered")
    identities = {
        (
            candidate.get("model", candidate.get("name")),
            candidate.get("manifestDigest"),
        )
        for candidate in matches
    }
    if len(identities) != 1 or None in next(iter(identities)):
        raise CompatibilityError("conflicting-model-registration")
    merged: dict[str, Any] = {}
    for candidate in matches:
        merged.update(candidate)
    return merged


def _model_route(requirements: dict[str, Any], model_id: str, engine: str) -> dict[str, Any]:
    if requirements.get("defaultDecision") != "deny":
        raise CompatibilityError("invalid-model-runtime-requirements")
    matches = [
        route
        for model in requirements.get("models", [])
        if model.get("modelId") == model_id
        for route in model.get("routes", [])
        if route.get("engine") == engine
    ]
    if len(matches) != 1:
        raise CompatibilityError("no-model-runtime-route")
    return matches[0]


def _route_allowed(route: dict[str, Any], include_candidate: bool) -> bool:
    state = str(route.get("admissionState", ""))
    return state == "admitted" or (include_candidate and state.startswith("candidate-"))


def _selected_components(model_artifact: dict[str, Any], capability: str | None) -> list[dict[str, Any]]:
    components = model_artifact.get("components", [])
    if not isinstance(components, list):
        raise CompatibilityError("invalid-model-artifact")
    selected = [
        component for component in components
        if component.get("role") == "text-model"
        or (capability is not None and capability in component.get("requiredForCapabilities", []))
    ]
    if not selected or any(
        not re.fullmatch(r"[0-9a-f]{64}", str(component.get("sha256", "")))
        or not isinstance(component.get("byteLength"), int)
        or component["byteLength"] <= 0
        for component in selected
    ):
        raise CompatibilityError("invalid-model-artifact")
    return selected


def validate_managed_setup_binding(
    resolution: object,
    managed_plan: object,
    component_registry: object,
) -> dict[str, Any]:
    """Prove that the legacy installer will fetch the resolved Ollama artifacts."""
    if (
        not isinstance(resolution, dict)
        or resolution.get("decision") != "install"
        or resolution.get("engine") != "ollama"
        or not isinstance(managed_plan, dict)
        or not isinstance(component_registry, dict)
    ):
        raise CompatibilityError("invalid-managed-setup-binding")
    kind = managed_plan.get("kind")
    expected_platform = {
        "windows-alpha-setup-plan": "windows-x64",
        "linux-alpha-setup-plan": "linux-x64",
    }.get(kind)
    backend_mode = managed_plan.get("backendMode")
    expected_backend = "rocm" if backend_mode == "rocm" else "core"
    if (
        expected_platform is None
        or resolution.get("platform") != expected_platform
        or resolution.get("backend") != expected_backend
        or resolution.get("modelId") != managed_plan.get("modelId")
    ):
        raise CompatibilityError("managed-plan-runtime-route-mismatch")
    component_ids = managed_plan.get("components")
    registry_components = component_registry.get("components")
    if (
        not isinstance(component_ids, list)
        or not component_ids
        or len(component_ids) != len(set(component_ids))
        or not isinstance(registry_components, list)
    ):
        raise CompatibilityError("invalid-managed-component-binding")
    by_id = {
        component.get("id"): component
        for component in registry_components
        if isinstance(component, dict) and isinstance(component.get("id"), str)
    }
    if any(identifier not in by_id for identifier in component_ids):
        raise CompatibilityError("managed-component-not-registered")
    selected = [by_id[identifier] for identifier in component_ids]
    runtime_artifacts = resolution.get("runtimeArtifacts")
    if not isinstance(runtime_artifacts, list) or not runtime_artifacts:
        raise CompatibilityError("invalid-runtime-artifact-binding")

    def artifact_identity(value: dict[str, Any], *, registry: bool) -> tuple[object, ...]:
        return (
            value.get("artifactName" if registry else "name"),
            value.get("byteLength"),
            value.get("sha256"),
            value.get("sourceUrl"),
        )

    if (
        any(component.get("version") != resolution.get("selectedRuntimeVersion") for component in selected)
        or sorted(artifact_identity(component, registry=True) for component in selected)
        != sorted(artifact_identity(artifact, registry=False) for artifact in runtime_artifacts)
    ):
        raise CompatibilityError("managed-component-runtime-artifact-mismatch")
    return {
        "schemaVersion": 1,
        "decision": "install",
        "planId": managed_plan.get("planId"),
        "modelId": resolution["modelId"],
        "engine": "ollama",
        "runtimeVersion": resolution["selectedRuntimeVersion"],
        "platform": expected_platform,
        "backend": expected_backend,
        "componentIds": list(component_ids),
        "artifactSha256": sorted(artifact["sha256"] for artifact in runtime_artifacts),
    }


def resolve(
    model_id: str,
    platform: str,
    backend: str,
    *,
    engine: str = "ollama",
    capability: str | None = None,
    include_candidate: bool = False,
    inventory_path: Path = INVENTORY,
    catalog_path: Path = CATALOG,
    runtime_path: Path = RUNTIMES,
    requirements_path: Path = REQUIREMENTS,
) -> dict[str, Any]:
    """Choose the newest admitted exact runtime satisfying one model route."""
    if (
        not SAFE_ID.fullmatch(model_id)
        or platform not in PLATFORMS
        or engine not in ENGINE_BACKENDS
        or backend not in ENGINE_BACKENDS[engine]
        or (capability is not None and not SAFE_ID.fullmatch(capability))
    ):
        raise CompatibilityError("invalid-runtime-request")
    inventory = _load(inventory_path)
    catalog = _load(catalog_path)
    registry = _load(runtime_path)
    requirements = _load(requirements_path)
    if registry.get("defaultDecision") != "deny":
        raise CompatibilityError("invalid-compatibility-registry")
    candidate = _registered_candidate(inventory, catalog, model_id)
    route = _model_route(requirements, model_id, engine)
    if not _route_allowed(route, include_candidate):
        raise CompatibilityError("no-admitted-compatible-runtime")
    minimum = str(route.get("minimumRuntimeVersion"))
    allowed_states = {"admitted"}
    if include_candidate:
        allowed_states.add("candidate-native-lifecycle-evidence-required")
    candidates: list[tuple[Any, dict[str, Any], list[dict[str, Any]]]] = []
    if engine == "ollama":
        minimum_value: Any = _version(minimum)
        candidate_tag = candidate.get("model", candidate.get("name"))
        candidate_minimum = candidate.get("minimumOllamaVersion")
        if (
            (candidate_minimum is not None and candidate_minimum != minimum)
            or route.get("modelArtifact", {}).get("exactTag") != candidate_tag
            or route.get("modelArtifact", {}).get("manifestSha256") != candidate.get("manifestDigest")
        ):
            raise CompatibilityError("model-runtime-requirement-mismatch")
        required_backends = {"core"} if backend == "core" else {"core", "rocm"}
        for runtime in registry.get("runtimes", []):
            version = _version(runtime.get("version"))
            if version < minimum_value or runtime.get("admissionState") not in allowed_states:
                continue
            artifacts = [
                artifact for artifact in runtime.get("artifacts", [])
                if artifact.get("platform") == platform
                and artifact.get("backend") in required_backends
            ]
            if {artifact.get("backend") for artifact in artifacts} == required_backends:
                candidates.append((version, runtime, artifacts))
    else:
        minimum_value = _llama_version(minimum)
        requested_backend = {"cuda": "cuda-12.4", "sycl": "sycl-fp16"}.get(backend, backend)
        for runtime in registry.get("llamaCppRuntimes", []):
            version = _llama_version(runtime.get("version"))
            if version < minimum_value or runtime.get("admissionState") not in allowed_states:
                continue
            artifacts = [
                artifact for artifact in runtime.get("artifacts", [])
                if artifact.get("platform") == platform
                and artifact.get("backend") == requested_backend
            ]
            roles = {artifact.get("role") for artifact in artifacts}
            required_roles = {"runtime", "runtime-support"} if requested_backend.startswith("cuda-") else {"runtime"}
            if required_roles.issubset(roles):
                candidates.append((version, runtime, artifacts))
    if not candidates:
        raise CompatibilityError("no-admitted-compatible-runtime")
    _, runtime, artifacts = max(candidates, key=lambda item: item[0])
    result = {
        "schemaVersion": 1,
        "decision": "candidate" if (
            runtime["admissionState"] != "admitted" or route["admissionState"] != "admitted"
        ) else "install",
        "modelId": model_id,
        "engine": engine,
        "minimumRuntimeVersion": minimum,
        "selectedRuntimeVersion": runtime["version"],
        "platform": platform,
        "backend": backend,
        "runtimeAdmissionState": runtime["admissionState"],
        "modelRouteAdmissionState": route["admissionState"],
        "runtimeArtifacts": artifacts,
        "modelArtifact": route["modelArtifact"],
        "installationRoot": registry["policy"]["installationRoot"],
        "systemRuntimeModificationAllowed": False,
        "silentEngineFallbackAllowed": False,
    }
    if engine == "ollama":
        result["minimumOllamaVersion"] = minimum
        result["selectedOllamaVersion"] = runtime["version"]
        result["artifacts"] = artifacts
    else:
        result["modelArtifact"] = dict(route["modelArtifact"])
        result["modelArtifact"]["selectedComponents"] = _selected_components(
            route["modelArtifact"], capability
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--engine", choices=sorted(ENGINE_BACKENDS), default="ollama")
    parser.add_argument("--platform", choices=sorted(PLATFORMS), required=True)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--capability")
    parser.add_argument("--include-candidate", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        result = resolve(
            args.model_id, args.platform, args.backend,
            engine=args.engine,
            capability=args.capability,
            include_candidate=args.include_candidate,
        )
    except CompatibilityError as error:
        print(json.dumps({"schemaVersion": 1, "decision": "deny", "reason": str(error)}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
