#!/usr/bin/env python3
"""Validate sanitized Apple M4 llama.cpp official-distribution evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts/alpha2-macos-llamacpp-distribution.py"


class ResultError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ResultError(code)


def load_runner():
    spec = importlib.util.spec_from_file_location("llamacpp_distribution", RUNNER_PATH)
    require(bool(spec and spec.loader), "runner-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(value: Any, runner: Any) -> None:
    require(isinstance(value, dict), "result-not-object")
    require(value.get("schemaVersion") == 1 and value.get("kind") == runner.KIND, "invalid-result-header")
    require(value.get("status") == "partial-pass", "invalid-result-status")
    profile = value.get("profile")
    require(profile == {"platformFamily": "macos", "architecture": "arm64", "hardware": "Apple M4", "memoryGiB": 16}, "profile-mismatch")
    release = value.get("officialRelease")
    require(
        release == {
            "project": runner.PROJECT,
            "tag": runner.TAG,
            "commit": runner.COMMIT,
            "releaseUrl": runner.RELEASE_URL,
            "asset": runner.ASSET,
            "assetUrl": runner.ASSET_URL,
            "assetBytes": runner.ASSET_BYTES,
            "assetSha256": runner.ASSET_SHA256,
        },
        "official-release-mismatch",
    )
    archive = value.get("archive")
    require(isinstance(archive, dict) and archive.get("memberCount") == 62, "archive-count-mismatch")
    require(all(archive.get(key) is True for key in ("safePaths", "safeInternalSymlinks", "exactOfficialDigest")), "archive-check-failed")
    runtime = value.get("runtime")
    require(isinstance(runtime, dict) and runtime.get("serverSha256") == runner.SERVER_SHA256, "runtime-mismatch")
    require(runtime.get("nativeArchitecture") == "arm64" and runtime.get("version") == runner.TAG and runtime.get("commit") == runner.COMMIT, "runtime-mismatch")
    require(runtime.get("relocatedLaunchPassed") is True, "relocation-not-proven")
    require(runtime.get("runtimeLaunchRequiresSystemPython") is False and runtime.get("runtimeLaunchRequiresPackageManager") is False, "runtime-not-self-contained")
    trust = value.get("platformTrust")
    require(isinstance(trust, dict) and trust.get("adHocSigned") is True, "signature-state-mismatch")
    require(all(trust.get(key) is False for key in ("developerIdSigned", "notarizationProven", "gatekeeperAdmitted", "publicDistributionTrusted")), "trust-overstated")
    require(value.get("open") == ["developer-id-signing", "notarization", "gatekeeper-public-admission", "maintained-coding-surface"], "open-gates-mismatch")
    privacy = value.get("privacy")
    authority = value.get("authority")
    require(isinstance(privacy, dict) and all(item is False for item in privacy.values()), "privacy-retention-present")
    require(isinstance(authority, dict) and all(item is False for item in authority.values()), "authority-overstated")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    runner = load_runner()
    try:
        require(args.result.is_file() and not args.result.is_symlink() and args.result.stat().st_size < 256 * 1024, "unsafe-json-input")
        value = json.loads(args.result.read_text(encoding="utf-8"))
        validate(value, runner)
    except (ResultError, OSError, UnicodeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    print(json.dumps({"status": "validated", "result": str(args.result)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
