#!/usr/bin/env python3
"""Pure fail-closed evaluator for future PDF worker OS isolation evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "config/pdf-os-isolation-gate.json").read_text(encoding="utf-8")
)


class IsolationRejected(ValueError):
    pass


def evaluate(evidence: object) -> dict[str, object]:
    if not isinstance(evidence, dict) or set(evidence) != {
        "schemaVersion",
        "platform",
        "platformIdentity",
        "controls",
        "sourcePackageParityPassed",
    }:
        raise IsolationRejected("evidence-shape")
    if evidence["schemaVersion"] != 1:
        raise IsolationRejected("evidence-schema")
    platform = evidence["platform"]
    if platform not in CONTRACT["platforms"]:
        raise IsolationRejected("platform-unsupported")
    identity = evidence["platformIdentity"]
    if not isinstance(identity, str) or not identity or len(identity) > 160:
        raise IsolationRejected("platform-identity")
    controls = evidence["controls"]
    if not isinstance(controls, list):
        raise IsolationRejected("controls-type")
    required = CONTRACT["platforms"][platform]["requiredControls"]
    if len(controls) != len(required):
        raise IsolationRejected("controls-count")
    by_id: dict[str, dict[str, object]] = {}
    for control in controls:
        if not isinstance(control, dict) or set(control) != {
            "id",
            "available",
            "implemented",
            "enforcementTestPassed",
            "hostileEscapeTestPassed",
        }:
            raise IsolationRejected("control-shape")
        identifier = control["id"]
        if identifier in by_id:
            raise IsolationRejected("control-duplicate")
        if identifier not in required:
            raise IsolationRejected("control-unknown")
        if any(
            not isinstance(control[field], bool)
            for field in (
                "available",
                "implemented",
                "enforcementTestPassed",
                "hostileEscapeTestPassed",
            )
        ):
            raise IsolationRejected("control-boolean")
        by_id[identifier] = control
    if set(by_id) != set(required):
        raise IsolationRejected("control-missing")
    missing = [
        identifier
        for identifier in required
        if not all(
            by_id[identifier][field]
            for field in (
                "available",
                "implemented",
                "enforcementTestPassed",
                "hostileEscapeTestPassed",
            )
        )
    ]
    parity = evidence["sourcePackageParityPassed"]
    if not isinstance(parity, bool):
        raise IsolationRejected("parity-boolean")
    admitted = not missing and parity
    return {
        "schemaVersion": 1,
        "platform": platform,
        "platformIdentity": identity,
        "missingControls": missing,
        "sourcePackageParityPassed": parity,
        "isolationAdmissionPassed": admitted,
        "runtimeAdmissionGranted": False,
        "fallbackUsed": False,
    }


def template(platform: str, identity: str) -> dict[str, object]:
    if platform not in CONTRACT["platforms"]:
        raise IsolationRejected("platform-unsupported")
    return {
        "schemaVersion": 1,
        "platform": platform,
        "platformIdentity": identity,
        "controls": [
            {
                "id": identifier,
                "available": False,
                "implemented": False,
                "enforcementTestPassed": False,
                "hostileEscapeTestPassed": False,
            }
            for identifier in CONTRACT["platforms"][platform]["requiredControls"]
        ],
        "sourcePackageParityPassed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=sorted(CONTRACT["platforms"]), required=True)
    parser.add_argument("--identity", required=True)
    args = parser.parse_args()
    print(json.dumps(evaluate(template(args.platform, args.identity)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
