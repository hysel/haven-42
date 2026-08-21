#!/usr/bin/env python3
"""Validate sanitized Apple M4 llama.cpp lifecycle evidence fail closed."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_CHECKS = {
    "loopbackOnly", "webUiDisabled", "authenticationRequired", "metalDetected",
    "allLayersOffloaded", "boundedInference", "forcedTimeoutObserved",
    "postTimeoutRecovery", "restart", "listenerClosed",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    data = json.loads(args.result.read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1 or data.get("kind") != "haven42-alpha2-macos-llamacpp-lifecycle-result" or data.get("outcome") != "passed":
        raise SystemExit("Refused: invalid result identity or outcome.")
    profile = data.get("profile", {})
    if profile != {"hardware": "Apple M4", "memoryGiB": 16, "os": "macOS", "architecture": "arm64"}:
        raise SystemExit("Refused: result is not bound to the exact M4 profile.")
    runtime = data.get("runtime", {})
    model = data.get("model", {})
    if not re.fullmatch(r"[0-9a-f]{7,40}", str(runtime.get("commit", ""))):
        raise SystemExit("Refused: runtime commit is not pinned.")
    for digest in (runtime.get("serverSha256"), model.get("sha256")):
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise SystemExit("Refused: runtime or model digest is not pinned.")
    checks = data.get("checks", {})
    if set(checks) != REQUIRED_CHECKS or not all(checks.values()):
        raise SystemExit("Refused: one or more lifecycle checks did not pass.")
    metrics = data.get("metrics", {})
    if any(not isinstance(metrics.get(key), (int, float)) or metrics[key] <= 0 for key in ("firstCompletionTokens", "recoveryCompletionTokens", "durationSeconds")):
        raise SystemExit("Refused: positive lifecycle metrics are required.")
    if data.get("authority") != {"changesDefaults": False, "changesSupport": False, "changesPackaging": False}:
        raise SystemExit("Refused: evidence exceeds qualification authority.")
    if data.get("privacy") != {"containsPrompt": False, "containsResponse": False, "containsPrivatePath": False, "containsCredential": False}:
        raise SystemExit("Refused: privacy declaration is invalid.")
    serialized = json.dumps(data, sort_keys=True)
    private_pattern = r"(?:" + re.escape("/" + "Users/") + r"|192\.168\.|BEGIN [A-Z ]+KEY|Bearer\s+)"
    if re.search(private_pattern, serialized, re.IGNORECASE):
        raise SystemExit("Refused: private infrastructure or credential material detected.")
    print("Apple M4 llama.cpp lifecycle result validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
