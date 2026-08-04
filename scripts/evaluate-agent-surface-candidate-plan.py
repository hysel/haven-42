#!/usr/bin/env python3
"""Create an effect-free candidate agent-surface dry-run plan."""

from __future__ import annotations

import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = json.loads((ROOT / "config/agent-surface-candidate-lifecycle.json").read_text(encoding="utf-8"))
MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")


class CandidatePlanRejected(ValueError):
    pass


def endpoint(value: object) -> str:
    if not isinstance(value, str) or len(value) > 256:
        raise CandidatePlanRejected("endpoint-shape")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise CandidatePlanRejected("endpoint-shape") from error
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise CandidatePlanRejected("endpoint-shape")
    try:
        address = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as error:
        raise CandidatePlanRejected("endpoint-address") from error
    if not (address.is_loopback or address.is_private):
        raise CandidatePlanRejected("endpoint-address")
    if port != 11434:
        raise CandidatePlanRejected("endpoint-port")
    return value.rstrip("/")


def evaluate(request: object) -> dict:
    if not isinstance(request, dict) or set(request) != {"surface", "platform", "model", "endpoint", "discovery"}:
        raise CandidatePlanRejected("request-shape")
    surface = request["surface"]
    platform = request["platform"]
    if surface not in CONTRACT["surfaces"] or platform not in {"windows", "linux", "macos"}:
        raise CandidatePlanRejected("request-value")
    model = request["model"]
    if not isinstance(model, str) or not MODEL.fullmatch(model):
        raise CandidatePlanRejected("model-shape")
    target = endpoint(request["endpoint"])
    discovery = request["discovery"]
    profile = CONTRACT["surfaces"][surface]
    if not isinstance(discovery, dict) or set(discovery) != {"executableName", "version", "regularFile", "linkOrReparse"}:
        raise CandidatePlanRejected("discovery-shape")
    if discovery != {
        "executableName": profile["expectedExecutable"],
        "version": profile["expectedVersion"],
        "regularFile": True,
        "linkOrReparse": False,
    }:
        raise CandidatePlanRejected("discovery-mismatch")
    return {
        "schemaVersion": 1,
        "status": "candidate-dry-run-plan",
        "surface": surface,
        "platform": platform,
        "exactVersion": profile["expectedVersion"],
        "versionProbe": {"executableName": profile["expectedExecutable"], "arguments": profile["versionArguments"]},
        "configTarget": {"scope": "repository-direct-child", "name": profile["configName"], "preexistingBehavior": "reject"},
        "configuration": {"model": model, "endpoint": target, "credentials": None, "automaticCommits": False},
        "rollback": CONTRACT["rollback"],
        "dryRun": True,
        "effects": {"filesystemRead": False, "filesystemWrite": False, "processCreation": False, "network": False, "installation": False},
        "authority": CONTRACT["authority"],
    }


if __name__ == "__main__":
    print(json.dumps({"status": CONTRACT["status"], "authority": CONTRACT["authority"]}, sort_keys=True))
