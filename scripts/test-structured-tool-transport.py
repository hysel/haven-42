#!/usr/bin/env python3
"""Security tests for the inactive structured-tool transport boundary."""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/evaluate-structured-tool-transport.py"
SPEC = importlib.util.spec_from_file_location("structured_tool_transport", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
REGISTRY = {
    "lookup_context": {
        "required": ["query", "limit", "includeMetadata"],
        "properties": {
            "query": "string",
            "limit": "integer",
            "includeMetadata": "boolean",
        },
    }
}


def ollama(arguments: object | None = None, name: str = "lookup_context") -> dict:
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "function": {
                    "name": name,
                    "arguments": arguments if arguments is not None else {
                        "query": "safe", "limit": 2, "includeMetadata": False
                    },
                }
            }],
        }
    }


def openai(arguments: str = '{"query":"safe","limit":2,"includeMetadata":false}') -> dict:
    return {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_safe_1",
                    "type": "function",
                    "function": {"name": "lookup_context", "arguments": arguments},
                }],
            }
        }]
    }


def rejected(action, reason: str) -> None:
    try:
        action()
    except MODULE.ToolTransportRejected as error:
        assert str(error) == reason, (str(error), reason)
        return
    raise AssertionError(f"hostile tool call admitted: {reason}")


def assess(response: object, transport: str = "ollama") -> dict[str, object]:
    source = response if isinstance(response, (str, bytes)) else json.dumps(response)
    return MODULE.evaluate(source, transport, REGISTRY)


def main() -> int:
    checks = 0
    for transport, response in (("ollama", ollama()), ("openai-compatible", openai())):
        result = assess(response, transport)
        assert result["toolName"] == "lookup_context"
        assert result["arguments"] == {
            "query": "safe", "limit": 2, "includeMetadata": False
        }
        assert result["argumentsUntrusted"] is True
        assert result["executionAllowed"] is False
        assert result["approvalGranted"] is False
        assert result["runtimeAdmissionGranted"] is False
        assert not any(result["effects"].values())
        checks += 7

    rejected(lambda: assess(ollama(name="shell")), "tool-not-allowed")
    parallel = ollama()
    parallel["message"]["tool_calls"].append(parallel["message"]["tool_calls"][0])
    rejected(lambda: assess(parallel), "tool-call-count")
    mixed = ollama()
    mixed["message"]["content"] = "Run this"
    rejected(lambda: assess(mixed), "mixed-assistant-content")
    rejected(lambda: assess(openai('{"query":"a","query":"b","limit":2,"includeMetadata":false}'), "openai-compatible"), "duplicate-json-key")
    rejected(lambda: assess(openai("[]"), "openai-compatible"), "arguments-object")
    rejected(lambda: assess(openai('{"query":NaN,"limit":2,"includeMetadata":false}'), "openai-compatible"), "arguments-number")
    rejected(lambda: assess(ollama({"query": "x", "limit": True, "includeMetadata": False})), "arguments-type")
    rejected(lambda: assess(ollama({"query": "x", "limit": 2, "includeMetadata": False, "extra": "x"})), "arguments-fields")
    rejected(lambda: assess(ollama({"query": "x", "limit": 2, "includeMetadata": False, "__proto__": {}})), "arguments-key")
    rejected(lambda: assess(ollama({"query": "x" * 2049, "limit": 2, "includeMetadata": False})), "arguments-string")
    cyclic: dict[str, object] = {
        "query": "x", "limit": 2, "includeMetadata": False
    }
    cyclic["query"] = cyclic
    rejected(lambda: MODULE._bounded(cyclic), "arguments-cycle")
    rejected(lambda: assess(ollama({"query": "x", "limit": 2})), "arguments-required")
    rejected(lambda: assess({}, "other"), "transport-unsupported")
    rejected(lambda: assess('{"message":{},"message":{}}'), "duplicate-json-key")
    rejected(lambda: assess(b"\xff"), "response-encoding")
    rejected(lambda: MODULE.evaluate({}, "ollama", REGISTRY), "response-type")
    checks += 16

    source = PATH.read_text(encoding="utf-8")
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    assert roots <= {"__future__", "json", "re"}
    assert all(marker not in source for marker in (
        "open(", "Path(", "socket", "subprocess", "requests", "urllib",
        "os.environ", "eval(", "exec(",
    ))
    contract = json.loads(
        (ROOT / "config/structured-tool-transport-contract.json").read_text(encoding="utf-8")
    )
    assert not any(contract["authority"].values())
    assert contract["policy"]["parallelCallsAllowed"] is False
    assert contract["policy"]["mixedAssistantContentAllowed"] is False
    assert contract["policy"]["rawUtf8JsonRequired"] is True
    assert MODULE.MAX_RESPONSE_BYTES == contract["limits"]["maximumResponseBytes"]
    assert MODULE.MAX_ARGUMENT_BYTES == contract["limits"]["maximumArgumentBytes"]
    runtime = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "web").rglob("*")
        if path.is_file() and path.suffix in {".py", ".js", ".html", ".css"}
    )
    assert "evaluate-structured-tool-transport" not in runtime
    package = (ROOT / "package/haven42.spec").read_text(encoding="utf-8")
    resources = (ROOT / "package/resource-integrity.json").read_text(encoding="utf-8")
    assert "evaluate-structured-tool-transport" not in package + resources
    checks += 10
    print(f"Structured tool transport passed {checks} effect-free security checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
