#!/usr/bin/env python3
"""Evaluate future parser-worker requests without opening or parsing content."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = ROOT / "config" / "restricted-parser-worker-contract.json"
FIXTURE_PATH = ROOT / "examples" / "fixtures" / "parser-worker-hostile-cases.json"
IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,63}$")


class ParserAdmissionError(ValueError):
    pass


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ParserAdmissionError("configuration-unavailable") from error


def _integer(value: Any, minimum: int, maximum: int, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ParserAdmissionError(code)
    return value


def _strict(value: Any, fields: list[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ParserAdmissionError(f"invalid-{label}-shape")
    return value


def _scan_forbidden(value: Any, forbidden: set[str]) -> None:
    pending = [value]
    visited = 0
    while pending:
        current = pending.pop()
        if not isinstance(current, (dict, list)):
            continue
        visited += 1
        if visited > 128:
            raise ParserAdmissionError("request-too-complex")
        if isinstance(current, dict):
            if any(key in forbidden for key in current):
                raise ParserAdmissionError("forbidden-request-authority")
            pending.extend(current.values())
        else:
            pending.extend(current)


def evaluate(request: dict[str, Any]) -> dict[str, Any]:
    contract = _load(CONTRACT_PATH)
    if (
        not isinstance(contract, dict)
        or contract.get("status") != "offline-admission-foundation-no-parser-admitted"
        or contract.get("runtimeRouteAllowed") is not False
        or contract.get("workerProcessAllowed") is not False
        or contract.get("parserDependenciesAdmitted") != []
        or any(contract.get("effects", {}).values())
    ):
        raise ParserAdmissionError("unsafe-parser-contract")
    serialized = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(serialized) > contract["request"]["maximumSerializedBytes"]:
        raise ParserAdmissionError("request-too-large")
    _scan_forbidden(request, set(contract["request"]["forbiddenFieldNames"]))
    _strict(request, contract["request"]["requiredFields"], "request")
    if request["schemaVersion"] != contract["schemaVersion"]:
        raise ParserAdmissionError("unsupported-schema")
    if request["operation"] not in contract["operations"]:
        raise ParserAdmissionError("unsupported-operation")
    if not isinstance(request["requestId"], str) or IDENTIFIER.fullmatch(request["requestId"]) is None:
        raise ParserAdmissionError("invalid-request-id")
    expected_media = contract["candidateFormats"].get(request["format"])
    if expected_media is None:
        raise ParserAdmissionError("unsupported-format")
    if request["mediaType"] != expected_media:
        raise ParserAdmissionError("media-type-mismatch")

    bounds = contract["bounds"]
    _integer(request["sizeBytes"], 1, bounds["maximumInputBytes"], "input-too-large")
    _integer(request["objectCount"], 0, bounds["maximumObjects"], "object-budget-exceeded")
    _integer(request["nestingDepth"], 0, bounds["maximumNestingDepth"], "nesting-budget-exceeded")
    compressed = _integer(
        request["compressedBytes"], 1, bounds["maximumInputBytes"], "invalid-compressed-size"
    )
    expanded = _integer(
        request["expandedBytes"], 1, bounds["maximumExpandedBytes"], "expanded-size-exceeded"
    )
    if expanded > compressed * bounds["maximumExpansionRatio"]:
        raise ParserAdmissionError("expansion-ratio-exceeded")

    boolean_rejections = {
        "encrypted": "encrypted-content-rejected",
        "activeContent": "active-content-rejected",
        "macros": "macros-rejected",
        "externalRelationships": "external-relationships-rejected",
        "embeddedObjects": "embedded-objects-rejected",
        "pathProvided": "path-authority-rejected",
    }
    for field, code in boolean_rejections.items():
        if type(request[field]) is not bool:
            raise ParserAdmissionError(f"invalid-{field}-boolean")
        if request[field]:
            raise ParserAdmissionError(code)

    limits = _strict(
        request["workerLimits"], contract["requiredWorkerLimits"], "worker-limits"
    )
    expected_limits = {
        "cpuSeconds": bounds["maximumCpuSeconds"],
        "wallSeconds": bounds["maximumWallSeconds"],
        "memoryBytes": bounds["maximumMemoryBytes"],
        "outputCharacters": bounds["maximumOutputCharacters"],
        "networkDenied": True,
        "filesystemDenied": True,
        "childProcessesDenied": True,
    }
    if limits != expected_limits:
        raise ParserAdmissionError("worker-limits-not-exact")
    if request["dependencyId"] is not None:
        if (
            not isinstance(request["dependencyId"], str)
            or IDENTIFIER.fullmatch(request["dependencyId"]) is None
        ):
            raise ParserAdmissionError("invalid-dependency-id")
        if request["dependencyId"] not in contract["parserDependenciesAdmitted"]:
            raise ParserAdmissionError("parser-dependency-not-admitted")

    return {
        "schemaVersion": 1,
        "kind": "restricted-parser-worker-admission",
        "status": "candidate-blocked",
        "operation": request["operation"],
        "requestId": request["requestId"],
        "format": request["format"],
        "reason": (
            "parser-dependency-selection-required"
            if request["dependencyId"] is None
            else "parser-dependency-not-admitted"
        ),
        "runtimeRouteAllowed": False,
        "workerProcessAllowed": False,
        "contentIncluded": False,
        "effects": dict(contract["effects"]),
    }


def base_request() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "requestId": "parser-foundation",
        "operation": "inspect-candidate",
        "format": "pdf",
        "mediaType": "application/pdf",
        "sizeBytes": 1024,
        "objectCount": 10,
        "nestingDepth": 2,
        "compressedBytes": 1024,
        "expandedBytes": 4096,
        "encrypted": False,
        "activeContent": False,
        "macros": False,
        "externalRelationships": False,
        "embeddedObjects": False,
        "pathProvided": False,
        "dependencyId": None,
        "workerLimits": {
            "cpuSeconds": 10,
            "wallSeconds": 15,
            "memoryBytes": 536870912,
            "outputCharacters": 1000000,
            "networkDenied": True,
            "filesystemDenied": True,
            "childProcessesDenied": True
        }
    }


def self_test() -> int:
    passed = 0

    def allow(mutator=None) -> dict[str, Any]:
        nonlocal passed
        value = base_request()
        if mutator:
            mutator(value)
        result = evaluate(value)
        assert result["status"] == "candidate-blocked"
        assert result["runtimeRouteAllowed"] is False
        assert result["workerProcessAllowed"] is False
        assert result["contentIncluded"] is False
        assert not any(result["effects"].values())
        passed += 1
        return result

    def deny(mutator, code: str) -> None:
        nonlocal passed
        value = base_request()
        mutator(value)
        try:
            evaluate(value)
        except ParserAdmissionError as error:
            assert str(error) == code, (str(error), code)
            passed += 1
            return
        raise AssertionError(f"parser request unexpectedly admitted: {code}")

    allow()
    allow(lambda value: value.update(operation="plan-parse"))
    for format_id, media_type in _load(CONTRACT_PATH)["candidateFormats"].items():
        allow(lambda value, f=format_id, m=media_type: value.update(format=f, mediaType=m))

    cases = _load(FIXTURE_PATH)
    assert isinstance(cases, list)
    for case in cases:
        mutation = case["mutation"]
        deny(lambda value, change=mutation: value.update(copy.deepcopy(change)), case["expectedError"])
    deny(lambda value: value.update(schemaVersion=2), "unsupported-schema")
    deny(lambda value: value.update(operation="execute"), "unsupported-operation")
    deny(lambda value: value.update(format="zip"), "unsupported-format")
    deny(lambda value: value.update(mediaType="text/plain"), "media-type-mismatch")
    deny(lambda value: value.update(dependencyId="future-parser"), "parser-dependency-not-admitted")
    deny(
        lambda value: value["workerLimits"].update(networkDenied=False),
        "worker-limits-not-exact",
    )
    print(f"Restricted parser-worker hostile self-test passed: {passed} cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.request:
        parser.error("--request is required unless --self-test is used")
    try:
        result = evaluate(_load(Path(args.request)))
    except ParserAdmissionError as error:
        print(f"Parser-worker admission rejected input: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
