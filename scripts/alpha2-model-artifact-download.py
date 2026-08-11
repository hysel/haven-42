#!/usr/bin/env python3
"""Plan or explicitly download one exact Alpha 2 qualification artifact."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, BinaryIO
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
RUNNER_PATH = ROOT / "scripts/alpha2-linux-model-validation.py"
MATRIX_PATH = ROOT / "config/alpha-2-model-qualification-matrix.json"
INVENTORY_PATH = ROOT / "config/alpha-2-model-version-inventory.json"
MAX_STREAM_BYTES = 16 * 1024 * 1024
MAX_LINE_BYTES = 64 * 1024
MAX_STREAM_RECORDS = 100_000


class DownloadError(ValueError):
    """The exact-artifact plan or download failed closed."""


def _load_runner():
    if RUNNER_PATH.is_symlink() or not RUNNER_PATH.is_file():
        raise DownloadError("unsafe-model-runner")
    specification = importlib.util.spec_from_file_location(
        "alpha2_model_validation_for_download", RUNNER_PATH
    )
    if specification is None or specification.loader is None:
        raise DownloadError("invalid-model-runner")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


RUNNER = _load_runner()


def _canonical_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_metadata(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise DownloadError("invalid-qualification-metadata")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DownloadError("invalid-qualification-metadata") from error
    if not isinstance(value, dict):
        raise DownloadError("invalid-qualification-metadata")
    return value


def _require_ready_candidate(model_id: str) -> None:
    inventory = _load_metadata(INVENTORY_PATH)
    matrix = _load_metadata(MATRIX_PATH)
    if (
        matrix.get("status") != "qualification-only-no-product-promotion"
        or matrix.get("inventoryBinding") != {
            "path": "config/alpha-2-model-version-inventory.json",
            "canonicalSha256": _canonical_sha256(inventory),
        }
    ):
        raise DownloadError("invalid-qualification-metadata")
    matches = [
        candidate
        for candidate in matrix.get("candidates", [])
        if isinstance(candidate, dict) and candidate.get("modelId") == model_id
    ]
    if (
        len(matches) != 1
        or matches[0].get("state") != "ready-for-qualification"
        or not matches[0].get("requiredProfiles")
    ):
        raise DownloadError("candidate-not-ready-for-qualification")


def _installed_digest(origin: str, name: str) -> str | None:
    records = RUNNER._json_request(origin, "/api/tags", timeout=30).get("models")
    if not isinstance(records, list):
        raise DownloadError("invalid-provider-response")
    matches = [
        item for item in records
        if isinstance(item, dict) and item.get("name") == name
    ]
    if len(matches) > 1:
        raise DownloadError("duplicate-installed-model")
    if not matches:
        return None
    digest = matches[0].get("digest")
    if isinstance(digest, str) and digest.startswith("sha256:"):
        digest = digest[7:]
    if not isinstance(digest, str):
        raise DownloadError("invalid-installed-model-digest")
    return digest


def _consume_pull_stream(stream: BinaryIO) -> tuple[int, int]:
    total_bytes = 0
    records = 0
    completed = 0
    expected_total = 0
    success = False
    while True:
        line = stream.readline(MAX_LINE_BYTES + 1)
        if not line:
            break
        total_bytes += len(line)
        records += 1
        if (
            len(line) > MAX_LINE_BYTES
            or total_bytes > MAX_STREAM_BYTES
            or records > MAX_STREAM_RECORDS
        ):
            raise DownloadError("provider-progress-response-too-large")
        try:
            value = json.loads(line.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise DownloadError("invalid-provider-progress-response") from error
        if not isinstance(value, dict) or value.get("error"):
            raise DownloadError("provider-download-failed")
        current = value.get("completed")
        total = value.get("total")
        if current is not None:
            if isinstance(current, bool) or not isinstance(current, int) or current < 0:
                raise DownloadError("invalid-provider-progress-response")
            completed = max(completed, current)
        if total is not None:
            if isinstance(total, bool) or not isinstance(total, int) or total < 0:
                raise DownloadError("invalid-provider-progress-response")
            expected_total = max(expected_total, total)
        if value.get("status") == "success":
            success = True
    if not success:
        raise DownloadError("provider-download-incomplete")
    return completed, expected_total


def _pull(origin: str, name: str) -> tuple[int, int]:
    body = json.dumps(
        {"model": name, "stream": True}, separators=(",", ":")
    ).encode("utf-8")
    request = urllib.request.Request(
        origin + "/api/pull",
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Haven42-Alpha2-Qualification/1",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=7200) as response:
            return _consume_pull_stream(response)
    except DownloadError:
        raise
    except (OSError, urllib.error.URLError) as error:
        raise DownloadError("provider-download-request-failed") from error


def prepare_artifact(
    *, origin: str, model_id: str, apply_download: bool = False,
) -> dict[str, Any]:
    if not isinstance(apply_download, bool):
        raise DownloadError("invalid-apply-mode")
    try:
        checked_origin = RUNNER.validate_origin(origin)
        _require_ready_candidate(model_id)
        model, inventory_sha, provider_version = RUNNER.reviewed_qualification_model(
            model_id
        )
        version = RUNNER._json_request(checked_origin, "/api/version", timeout=10)
    except RUNNER.ValidationError as error:
        raise DownloadError(str(error)) from error
    if version != {"version": provider_version}:
        raise DownloadError("provider-version-mismatch")
    expected_download_bytes = model.get("downloadBytes")
    if (
        isinstance(expected_download_bytes, bool)
        or not isinstance(expected_download_bytes, int)
        or expected_download_bytes < model.get("modelBytes", expected_download_bytes + 1)
        or expected_download_bytes > 64 * 1024 * 1024 * 1024
    ):
        raise DownloadError("invalid-expected-download-size")
    before = _installed_digest(checked_origin, model["name"])
    if before is not None and before != model["manifestDigest"]:
        raise DownloadError("installed-model-digest-mismatch")
    if before == model["manifestDigest"]:
        action = "reused"
        completed = expected_total = 0
    elif not apply_download:
        action = "planned"
        completed = expected_total = 0
    else:
        completed, expected_total = _pull(checked_origin, model["name"])
        after = _installed_digest(checked_origin, model["name"])
        if after != model["manifestDigest"]:
            raise DownloadError("downloaded-model-digest-mismatch")
        action = "downloaded"
    return {
        "schemaVersion": 1,
        "kind": "alpha2-exact-model-artifact-preparation",
        "outcome": "passed",
        "containsPrivateMachineIdentity": False,
        "containsRawProviderOutput": False,
        "action": action,
        "modelId": model_id,
        "model": model["name"],
        "manifestDigest": model["manifestDigest"],
        "expectedDownloadBytes": expected_download_bytes,
        "provider": "ollama",
        "providerVersion": provider_version,
        "qualificationInventoryCanonicalSha256": inventory_sha,
        "progress": {
            "completedBytes": completed,
            "reportedTotalBytes": expected_total,
        },
        "automaticPromotionAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--apply-download", action="store_true")
    args = parser.parse_args()
    try:
        result = prepare_artifact(
            origin=args.origin,
            model_id=args.model_id,
            apply_download=args.apply_download,
        )
    except DownloadError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
