#!/usr/bin/env python3
"""Capture sanitized, fail-closed Ollama full-GPU-residency evidence.

The monitor is deliberately passive: it only reads ``/api/ps`` while another
reviewed runner owns inference.  It never loads, unloads, downloads, or prompts
a model.  One immutable record is written for each requested inventory ID.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


class ResidencyError(RuntimeError):
    """A fail-closed input or observation error."""


def _validate_origin(origin: str) -> str:
    try:
        parsed = urlsplit(origin)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ResidencyError("ollama-origin-invalid") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or port is None
        or not 1 <= port <= 65535
    ):
        raise ResidencyError("ollama-origin-invalid")
    return f"http://127.0.0.1:{port}"


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _inventory_candidates(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for family in document.get("families", []):
        for version in family.get("versions", []):
            for candidate in version.get("candidates", []):
                candidate_id = candidate.get("id")
                model = candidate.get("model")
                manifest = candidate.get("manifestDigest")
                if not all(isinstance(item, str) and item for item in (candidate_id, model, manifest)):
                    raise ResidencyError("invalid-inventory-candidate")
                if candidate_id in result:
                    raise ResidencyError("duplicate-inventory-candidate")
                result[candidate_id] = {
                    "model": model,
                    "manifestDigest": manifest,
                    "providerVersion": document.get("qualificationProvider", {}).get("exactVersion"),
                }
    return result


def _read_processes(origin: str) -> list[dict[str, Any]]:
    try:
        with urlopen(f"{origin.rstrip('/')}/api/ps", timeout=5) as response:
            document = json.load(response)
    except (OSError, URLError, ValueError, json.JSONDecodeError) as exc:
        raise ResidencyError("ollama-process-query-failed") from exc
    models = document.get("models")
    if not isinstance(models, list):
        raise ResidencyError("ollama-process-response-invalid")
    return [item for item in models if isinstance(item, dict)]


def _record(
    candidate_id: str, candidate: dict[str, Any], process: dict[str, Any], inventory_hash: str,
    *, operating_system_id: str, backend: str, hardware_profile_id: str,
) -> dict[str, Any]:
    size = process.get("size")
    size_vram = process.get("size_vram")
    if (
        isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or isinstance(size_vram, bool)
        or not isinstance(size_vram, int)
        or size_vram < 0
        or size_vram > size
    ):
        raise ResidencyError("ollama-residency-counters-invalid")
    ratio = size_vram / size
    if not math.isfinite(ratio):
        raise ResidencyError("ollama-residency-ratio-invalid")
    passed = size_vram == size
    return {
        "schemaVersion": 1,
        "kind": "alpha2-ollama-full-gpu-residency-evidence",
        "observedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "outcome": "passed" if passed else "failed",
        "errorCode": None if passed else "partial-gpu-residency",
        "evidence": {
            "provider": "ollama",
            "providerVersion": candidate["providerVersion"],
            "modelId": candidate_id,
            "operatingSystemId": operating_system_id,
            "backendMode": backend,
            "hardwareProfileId": hardware_profile_id,
            "manifestDigest": candidate["manifestDigest"],
            "qualificationInventoryCanonicalSha256": inventory_hash,
            "reportedModelBytes": size,
            "reportedGpuResidentBytes": size_vram,
            "gpuResidencyRatio": round(ratio, 9),
            "fullGpuResidencyObserved": passed,
            "passiveObservationOnly": True,
            "automaticPromotionAllowed": False,
        },
        "containsPrivateMachineIdentity": False,
        "containsRawPromptsOrResponses": False,
    }


def _write_once(path: Path, document: dict[str, Any]) -> None:
    if path.exists():
        raise ResidencyError(f"output-already-exists:{path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.new")
    temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def monitor(
    *, origin: str, inventory_path: Path, candidate_ids: list[str], output_dir: Path,
    output_prefix: str, operating_system_id: str, backend: str, hardware_profile_id: str,
    stop_marker: Path | None, poll_seconds: float, timeout_seconds: float,
) -> int:
    origin = _validate_origin(origin)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    candidates = _inventory_candidates(inventory)
    selected: dict[str, dict[str, Any]] = {}
    for candidate_id in candidate_ids:
        if candidate_id not in candidates:
            raise ResidencyError(f"candidate-not-in-inventory:{candidate_id}")
        selected[candidate_id] = candidates[candidate_id]
    inventory_hash = _canonical_sha256(inventory)
    remaining = set(selected)
    deadline = time.monotonic() + timeout_seconds
    while remaining and time.monotonic() < deadline:
        if stop_marker is not None and stop_marker.exists():
            break
        try:
            processes = _read_processes(origin)
        except ResidencyError:
            time.sleep(poll_seconds)
            continue
        for candidate_id in sorted(remaining):
            candidate = selected[candidate_id]
            matches = [process for process in processes if process.get("name") == candidate["model"]]
            if len(matches) > 1:
                raise ResidencyError(f"duplicate-running-model:{candidate_id}")
            if len(matches) == 1:
                output = output_dir / f"{output_prefix}{candidate_id}-full-residency.json"
                _write_once(output, _record(
                    candidate_id, candidate, matches[0], inventory_hash,
                    operating_system_id=operating_system_id,
                    backend=backend,
                    hardware_profile_id=hardware_profile_id,
                ))
                remaining.remove(candidate_id)
        if remaining:
            time.sleep(poll_seconds)
    if remaining:
        raise ResidencyError("models-not-observed:" + ",".join(sorted(remaining)))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--model-id", action="append", dest="model_ids", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--output-prefix", default="")
    parser.add_argument("--operating-system-id", required=True)
    parser.add_argument("--backend", choices=("cuda", "vulkan", "rocm", "sycl"), required=True)
    parser.add_argument("--hardware-profile-id", required=True)
    parser.add_argument("--stop-marker", type=Path)
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("--timeout-seconds", type=float, default=7200)
    args = parser.parse_args()
    if args.poll_seconds <= 0 or args.timeout_seconds <= 0:
        raise ResidencyError("monitor-timing-invalid")
    return monitor(
        origin=args.origin,
        inventory_path=args.inventory,
        candidate_ids=args.model_ids,
        output_dir=args.output_dir,
        output_prefix=args.output_prefix,
        operating_system_id=args.operating_system_id,
        backend=args.backend,
        hardware_profile_id=args.hardware_profile_id,
        stop_marker=args.stop_marker,
        poll_seconds=args.poll_seconds,
        timeout_seconds=args.timeout_seconds,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, ResidencyError) as exc:
        print(f"Refused: {exc}", file=sys.stderr)
        raise SystemExit(1)
