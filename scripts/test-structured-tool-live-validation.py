#!/usr/bin/env python3
"""Offline security tests for the manual Ollama live-validation harness."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/run-structured-tool-live-validation.py"
SPEC = importlib.util.spec_from_file_location("tool_live_validation", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def envelope(model: str) -> bytes:
    return json.dumps({
        "model": model,
        "created_at": "2026-08-03T12:34:56Z",
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "call_live_1", "function": {
                "name": "lookup_context",
                "index": 0,
                "arguments": {
                    "query": "synthetic-validation",
                    "limit": 2,
                    "includeMetadata": False,
                },
            }}],
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": 1,
        "load_duration": 1,
        "prompt_eval_count": 1,
        "prompt_eval_duration": 1,
        "eval_count": 1,
        "eval_duration": 1,
    }).encode()


def main() -> int:
    calls: list[tuple[str, object | None]] = []

    def request(path: str, payload=None, maximum=65536):
        calls.append((path, payload))
        if path == "/api/version":
            return b'{"version":"0.32.5"}'
        if path == "/api/tags":
            return b'{"models":[{"name":"tool-model"},{"name":"no-tools"}]}'
        if path == "/api/generate":
            return b'{}'
        if payload["model"] == "no-tools":
            raise MODULE.HttpFailure(400, b'{"error":"model does not support tools"}')
        return envelope(payload["model"])

    result = MODULE.validate(request, ["tool-model", "no-tools", "missing"])
    assert result["models"] == [
        {
            "model": "tool-model", "outcome": "pass",
            "toolName": "lookup_context", "finalResponseValidated": True,
            "rawContentRetained": False, "argumentsRetained": False,
            "unloadConfirmed": True,
        },
        {
            "model": "no-tools", "outcome": "model-does-not-support-tools",
            "unloadConfirmed": True,
        },
        {"model": "missing", "outcome": "not-installed"},
    ]
    assert result["endpointRetained"] is False
    assert result["promptOrResponseContentRetained"] is False
    assert result["runtimeAdmissionGranted"] is False
    assert sum(path == "/api/generate" for path, _ in calls) == 2
    serialized = json.dumps(result)
    assert "127" + ".0.0.1" not in serialized
    assert "192" + ".168." not in serialized

    def wrong_version(path: str, payload=None, maximum=65536):
        return b'{"version":"99.0.0"}'

    try:
        MODULE.validate(wrong_version, ["tool-model"])
    except MODULE.LiveValidationError as error:
        assert str(error) == "ollama-version-not-validated"
    else:
        raise AssertionError("unvalidated Ollama version accepted")
    try:
        MODULE.validate(request, ["bad model"])
    except MODULE.LiveValidationError as error:
        assert str(error) == "invalid-model-request"
    else:
        raise AssertionError("unsafe model identifier accepted")
    try:
        MODULE._object(b'{"version":"0.32.5","version":"forged"}')
    except MODULE.LiveValidationError as error:
        assert str(error) == "duplicate-provider-json-key"
    else:
        raise AssertionError("duplicate provider JSON key accepted")
    assert MODULE._unsupported(MODULE.HttpFailure(400, b'{"error":"does not support tools"}'))
    assert not MODULE._unsupported(MODULE.HttpFailure(500, b'{"error":"does not support tools"}'))
    shape = MODULE._tool_shape(envelope("tool-model"))
    assert shape == {
        "callKeys": ["function", "id"],
        "functionKeys": ["arguments", "index", "name"],
        "argumentsType": "dict",
    }
    source = PATH.read_text(encoding="utf-8")
    assert "ollama pull" not in source
    assert "subprocess" not in source
    assert '"runtimeAdmissionGranted": False' in source
    assert "--output-root" not in source
    print("Structured tool live harness passed 15 offline security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
