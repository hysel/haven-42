#!/usr/bin/env python3
"""Fail-closed audit of reviewed Linux runtime artifacts and license evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from linux_alpha_runtime import LinuxRuntimeError, inspect_registered_archive


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "config" / "linux-runtime-artifact-review.json"
COMPATIBILITY_PATH = ROOT / "config" / "alpha-2-runtime-compatibility.json"
MODEL_REVIEW_PATH = ROOT / "config" / "linux-model-artifact-review.json"
MODEL_CATALOG_PATH = ROOT / "config" / "alpha-2-model-catalog.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EXPECTED_REVIEW_KEYS = {
    "schemaVersion", "reviewId", "defaultDecision",
    "managedRuntimeChangeApproved", "automaticDefaultChangeAllowed",
    "runtime", "review",
}
EXPECTED_RUNTIME_KEYS = {
    "engine", "version", "admissionState", "releasePage", "publishedAtUtc",
    "sourceRepository", "sourceRef", "license", "artifacts",
}
EXPECTED_ARTIFACT_KEYS = {
    "id", "platform", "backend", "role", "name", "byteLength", "sha256",
    "sourceUrl", "archiveFormat", "maximumArchiveMembers",
    "expectedRegularFiles", "expectedDirectories", "expectedInternalLinks",
    "expandedByteLength", "requiredExecutableRelativePath",
    "embeddedLicenseNotice", "managedInstallationAllowed",
}


class SupplyChainError(ValueError):
    """The reviewed supply-chain evidence was incomplete or inconsistent."""


def _load(path: Path, label: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise SupplyChainError(f"unsafe-{label}")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SupplyChainError(f"invalid-{label}") from error
    if not isinstance(value, dict):
        raise SupplyChainError(f"invalid-{label}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        if path.is_symlink() or not path.is_file():
            raise SupplyChainError("unsafe-license-evidence")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise SupplyChainError("invalid-license-evidence") from error
    return digest.hexdigest()


def validate_review(
    review_path: Path = REVIEW_PATH,
    compatibility_path: Path = COMPATIBILITY_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    value = _load(review_path, "linux-runtime-artifact-review")
    if (
        set(value) != EXPECTED_REVIEW_KEYS
        or value.get("schemaVersion") != 1
        or value.get("reviewId") != "haven42.alpha2.linux-runtime-artifact-review"
        or value.get("defaultDecision") != "deny"
        or value.get("managedRuntimeChangeApproved") is not False
        or value.get("automaticDefaultChangeAllowed") is not False
    ):
        raise SupplyChainError("invalid-linux-runtime-artifact-review")
    runtime = value.get("runtime")
    if (
        not isinstance(runtime, dict)
        or set(runtime) != EXPECTED_RUNTIME_KEYS
        or runtime.get("engine") != "ollama"
        or runtime.get("version") != "0.32.9"
        or runtime.get("sourceRef") != "v0.32.9"
        or runtime.get("admissionState")
        != "candidate-native-lifecycle-evidence-required"
        or runtime.get("releasePage")
        != "https://github.com/ollama/ollama/releases/tag/v0.32.9"
        or runtime.get("sourceRepository") != "https://github.com/ollama/ollama"
    ):
        raise SupplyChainError("invalid-reviewed-runtime")

    license_record = runtime.get("license")
    expected_license_keys = {
        "expression", "sourcePath", "sourceBlobSha", "evidencePath",
        "appliesToReviewedVersions", "embeddedInReleaseArchives",
    }
    if (
        not isinstance(license_record, dict)
        or set(license_record) != expected_license_keys
        or license_record.get("expression") != "MIT"
        or license_record.get("sourcePath") != "LICENSE"
        or license_record.get("sourceBlobSha")
        != "8e3dc978a7ca8c53f56bbedc5b558116140fc02e"
        or license_record.get("appliesToReviewedVersions") != ["0.32.5", "0.32.9"]
        or license_record.get("embeddedInReleaseArchives") is not False
    ):
        raise SupplyChainError("invalid-runtime-license-record")
    evidence_path = root / str(license_record.get("evidencePath", ""))
    try:
        evidence_path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise SupplyChainError("unsafe-license-evidence") from error
    if _sha256(evidence_path) != "5934ed2ce0d15154bcdb9c85203210abac0da4314af34081e36df4599f90b226":
        raise SupplyChainError("license-evidence-mismatch")

    artifacts = runtime.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 2:
        raise SupplyChainError("invalid-reviewed-artifacts")
    seen: set[str] = set()
    for artifact in artifacts:
        if (
            not isinstance(artifact, dict)
            or set(artifact) != EXPECTED_ARTIFACT_KEYS
            or not SAFE_ID.fullmatch(str(artifact.get("id", "")))
            or artifact["id"] in seen
            or artifact.get("platform") != "linux-x64"
            or artifact.get("backend") not in {"core", "rocm"}
            or artifact.get("archiveFormat") != "tar.zst"
            or not HEX64.fullmatch(str(artifact.get("sha256", "")))
            or not isinstance(artifact.get("byteLength"), int)
            or not 1 <= artifact["byteLength"] <= 4 * 1024**3
            or not isinstance(artifact.get("expandedByteLength"), int)
            or not 1 <= artifact["expandedByteLength"] <= 4 * 1024**3
            or any(
                not isinstance(artifact.get(field), int) or artifact[field] < 0
                for field in (
                    "maximumArchiveMembers", "expectedRegularFiles",
                    "expectedDirectories", "expectedInternalLinks",
                )
            )
            or artifact.get("embeddedLicenseNotice") is not False
            or artifact.get("managedInstallationAllowed") is not False
            or artifact.get("sourceUrl")
            != f"https://github.com/ollama/ollama/releases/download/v0.32.9/{artifact.get('name')}"
        ):
            raise SupplyChainError("invalid-reviewed-artifact")
        seen.add(artifact["id"])
    by_backend = {artifact["backend"]: artifact for artifact in artifacts}
    if (
        set(by_backend) != {"core", "rocm"}
        or by_backend["core"].get("role") != "runtime"
        or by_backend["core"].get("requiredExecutableRelativePath") != "bin/ollama"
        or by_backend["rocm"].get("role") != "runtime-supplement"
        or by_backend["rocm"].get("requiredExecutableRelativePath") is not None
    ):
        raise SupplyChainError("invalid-reviewed-artifact-role")

    compatibility = _load(compatibility_path, "runtime-compatibility")
    matches = [
        candidate for candidate in compatibility.get("runtimes", [])
        if candidate.get("version") == runtime["version"]
    ]
    if len(matches) != 1 or matches[0].get("admissionState") != runtime["admissionState"]:
        raise SupplyChainError("runtime-review-compatibility-mismatch")
    registered = {
        (item.get("platform"), item.get("backend")): item
        for item in matches[0].get("artifacts", [])
    }
    for artifact in artifacts:
        peer = registered.get((artifact["platform"], artifact["backend"]))
        if peer is None or any(
            peer.get(peer_name) != artifact.get(review_name)
            for peer_name, review_name in (
                ("name", "name"), ("byteLength", "byteLength"),
                ("sha256", "sha256"), ("sourceUrl", "sourceUrl"),
            )
        ):
            raise SupplyChainError("runtime-review-artifact-mismatch")

    review = value.get("review")
    if review != {
        "officialReleaseMetadataMatched": True,
        "archiveHashesMatched": True,
        "archiveInventoriesRecorded": True,
        "hostileArchiveValidationRequired": True,
        "nativeLifecycleEvidenceRequired": True,
        "productionPromotionAllowed": False,
    }:
        raise SupplyChainError("invalid-runtime-review-decision")
    return value


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_model_review(
    review_path: Path = MODEL_REVIEW_PATH,
    catalog_path: Path = MODEL_CATALOG_PATH,
) -> dict[str, Any]:
    value = _load(review_path, "linux-model-artifact-review")
    expected_keys = {
        "schemaVersion", "reviewId", "defaultDecision", "selectionCatalogPath",
        "selectionCatalogCanonicalSha256", "selectionPolicyChangeAllowed",
        "automaticDefaultChangeAllowed", "source", "capabilities", "models",
        "review",
    }
    if (
        set(value) != expected_keys
        or value.get("schemaVersion") != 1
        or value.get("reviewId") != "haven42.alpha2.linux-model-artifact-review"
        or value.get("defaultDecision") != "deny"
        or value.get("selectionCatalogPath") != "config/alpha-2-model-catalog.json"
        or value.get("selectionPolicyChangeAllowed") is not False
        or value.get("automaticDefaultChangeAllowed") is not False
        or value.get("capabilities")
        != ["general.chat", "content.write", "content.summarize"]
    ):
        raise SupplyChainError("invalid-linux-model-artifact-review")
    source = value.get("source")
    if (
        not isinstance(source, dict)
        or source.get("registry") != "https://registry.ollama.ai"
        or source.get("repository") != "library/qwen3.5"
        or not re.fullmatch(
            r"2026-08-13T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z",
            str(source.get("retrievedAtUtc", "")),
        )
    ):
        raise SupplyChainError("invalid-model-artifact-source")
    catalog = _load(catalog_path, "alpha2-model-catalog")
    if _canonical_sha256(catalog) != value.get("selectionCatalogCanonicalSha256"):
        raise SupplyChainError("model-review-catalog-digest-mismatch")
    catalog_models = {
        item.get("id"): item for item in catalog.get("models", [])
        if isinstance(item, dict)
    }
    models = value.get("models")
    if not isinstance(models, list) or len(models) != 6:
        raise SupplyChainError("invalid-reviewed-model-artifacts")
    seen: set[str] = set()
    for model in models:
        if not isinstance(model, dict) or set(model) != {
            "modelId", "exactTag", "manifestSha256", "manifestBytes",
            "quantization", "minimumSystemMemoryGiB",
            "minimumUsableGpuMemoryGiB", "layers",
        }:
            raise SupplyChainError("invalid-reviewed-model-artifact")
        model_id = str(model.get("modelId", ""))
        catalog_model = catalog_models.get(model_id)
        if (
            catalog_model is None
            or model_id in seen
            or model.get("exactTag") != catalog_model.get("name")
            or model.get("manifestSha256") != catalog_model.get("manifestDigest")
            or model.get("quantization") != catalog_model.get("quantization")
            or model.get("minimumSystemMemoryGiB")
            != catalog_model.get("minimumSystemMemoryGiB")
            or model.get("minimumUsableGpuMemoryGiB")
            != catalog_model.get("minimumUsableGpuMemoryGiB")
            or model.get("manifestBytes") not in {709, 710}
        ):
            raise SupplyChainError("model-review-catalog-mismatch")
        seen.add(model_id)
        layers = model.get("layers")
        if not isinstance(layers, list) or len(layers) != 4:
            raise SupplyChainError("invalid-model-layer-set")
        by_role = {
            layer.get("role"): layer for layer in layers if isinstance(layer, dict)
        }
        if set(by_role) != {"config", "model", "license", "parameters"}:
            raise SupplyChainError("invalid-model-layer-set")
        for role, layer in by_role.items():
            expected_layer_keys = {"role", "sha256", "byteLength"}
            if role == "license":
                expected_layer_keys.add("license")
            if (
                set(layer) != expected_layer_keys
                or not HEX64.fullmatch(str(layer.get("sha256", "")))
                or not isinstance(layer.get("byteLength"), int)
                or isinstance(layer.get("byteLength"), bool)
                or layer["byteLength"] <= 0
                or (role == "license" and layer.get("license") != "Apache-2.0")
            ):
                raise SupplyChainError("invalid-model-layer")
        if (
            by_role["model"]["sha256"] != catalog_model.get("modelLayerDigest")
            or by_role["model"]["byteLength"] != catalog_model.get("modelBytes")
        ):
            raise SupplyChainError("model-layer-catalog-mismatch")
    if set(catalog_models) != seen:
        raise SupplyChainError("model-review-catalog-mismatch")
    if value.get("review") != {
        "officialManifestHashesRecomputed": True,
        "officialLicenseLayersRead": True,
        "prequantizedArtifactsOnly": True,
        "selectionPolicyChanged": False,
        "automaticDefaultChanged": False,
    }:
        raise SupplyChainError("invalid-model-review-decision")
    return value


def audit_archives(review: dict[str, Any], archives: dict[str, Path]) -> dict[str, Any]:
    expected = {item["backend"]: item for item in review["runtime"]["artifacts"]}
    if set(archives) != set(expected):
        raise SupplyChainError("incomplete-runtime-archive-set")
    results: dict[str, Any] = {}
    for backend, path in archives.items():
        component = dict(expected[backend])
        component["executableRelativePath"] = component.pop(
            "requiredExecutableRelativePath"
        )
        try:
            inspected = inspect_registered_archive(path, component)
        except LinuxRuntimeError as error:
            raise SupplyChainError(str(error)) from error
        results[backend] = {
            "sha256": component["sha256"],
            "regularFiles": inspected["regularFiles"],
            "directories": inspected["directories"],
            "internalLinks": inspected["internalLinks"],
            "expandedBytes": inspected["expandedBytes"],
        }
    return {
        "schemaVersion": 1,
        "decision": "candidate-review-passed",
        "managedRuntimeChanged": False,
        "modelSelectionChanged": False,
        "artifacts": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-archive", type=Path)
    parser.add_argument("--rocm-archive", type=Path)
    args = parser.parse_args()
    review = validate_review()
    validate_model_review()
    if (args.core_archive is None) != (args.rocm_archive is None):
        raise SystemExit("Both --core-archive and --rocm-archive are required together.")
    if args.core_archive is None:
        result = {
            "schemaVersion": 1,
            "decision": "candidate-record-validated",
            "managedRuntimeChanged": False,
            "modelSelectionChanged": False,
        }
    else:
        result = audit_archives(
            review, {"core": args.core_archive, "rocm": args.rocm_archive}
        )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
