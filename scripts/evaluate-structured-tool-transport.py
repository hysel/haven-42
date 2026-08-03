#!/usr/bin/env python3
"""Effect-free normalization gate for future structured model tool calls."""

from __future__ import annotations

import json
import re
from datetime import datetime


NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
CALL_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,254}$")
RFC3339_UTC = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$"
)
DANGEROUS_KEYS = {"__proto__", "constructor", "prototype"}
MAX_ARGUMENT_BYTES = 8192
MAX_RESPONSE_BYTES = 32768
MAX_ARGUMENT_DEPTH = 6
MAX_ARGUMENT_NODES = 128
MAX_STRING_CHARACTERS = 2048
MAX_METRIC_VALUE = 2**63 - 1
OLLAMA_FIELDS = {
    "model", "created_at", "message", "done", "done_reason", "total_duration",
    "load_duration", "prompt_eval_count", "prompt_eval_duration", "eval_count",
    "eval_duration",
}


class ToolTransportRejected(ValueError):
    """Stable rejection at the inactive structured-tool transport boundary."""


def _pairs(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if key in result:
            raise ToolTransportRejected("duplicate-json-key")
        result[key] = value
    return result


def _json_object(value: object) -> dict[str, object]:
    if not isinstance(value, str) or len(value.encode("utf-8")) > MAX_ARGUMENT_BYTES:
        raise ToolTransportRejected("arguments-size")
    try:
        parsed = json.loads(
            value,
            object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ToolTransportRejected("arguments-number")
            ),
        )
    except ToolTransportRejected:
        raise
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ToolTransportRejected("arguments-json") from error
    if not isinstance(parsed, dict):
        raise ToolTransportRejected("arguments-object")
    return parsed


def _response_json(value: object) -> object:
    if isinstance(value, bytes):
        try:
            source = value.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise ToolTransportRejected("response-encoding") from error
    elif isinstance(value, str):
        source = value
    else:
        raise ToolTransportRejected("response-type")
    if not source or len(source.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ToolTransportRejected("response-size")
    try:
        return json.loads(
            source,
            object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ToolTransportRejected("response-number")
            ),
        )
    except ToolTransportRejected:
        raise
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ToolTransportRejected("response-json") from error


def _bounded(
    value: object,
    depth: int = 1,
    nodes: list[int] | None = None,
    seen: set[int] | None = None,
) -> None:
    counter = nodes if nodes is not None else [0]
    identities = seen if seen is not None else set()
    counter[0] += 1
    if counter[0] > MAX_ARGUMENT_NODES:
        raise ToolTransportRejected("arguments-nodes")
    if depth > MAX_ARGUMENT_DEPTH:
        raise ToolTransportRejected("arguments-depth")
    if isinstance(value, dict):
        if id(value) in identities:
            raise ToolTransportRejected("arguments-cycle")
        identities.add(id(value))
        for key, item in value.items():
            if not isinstance(key, str) or key.casefold() in DANGEROUS_KEYS:
                raise ToolTransportRejected("arguments-key")
            _bounded(item, depth + 1, counter, identities)
        identities.remove(id(value))
    elif isinstance(value, list):
        if id(value) in identities:
            raise ToolTransportRejected("arguments-cycle")
        identities.add(id(value))
        for item in value:
            _bounded(item, depth + 1, counter, identities)
        identities.remove(id(value))
    elif isinstance(value, str):
        if len(value) > MAX_STRING_CHARACTERS or "\x00" in value:
            raise ToolTransportRejected("arguments-string")
    elif value is not None and not isinstance(value, (bool, int, float)):
        raise ToolTransportRejected("arguments-value")
    elif isinstance(value, float) and (value != value or abs(value) == float("inf")):
        raise ToolTransportRejected("arguments-number")


def _registry(value: object) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict) or not 1 <= len(value) <= 32:
        raise ToolTransportRejected("registry-shape")
    for name, schema in value.items():
        if not isinstance(name, str) or NAME.fullmatch(name) is None:
            raise ToolTransportRejected("registry-name")
        if not isinstance(schema, dict) or set(schema) != {"required", "properties"}:
            raise ToolTransportRejected("registry-schema")
        required = schema["required"]
        properties = schema["properties"]
        if not isinstance(required, list) or not isinstance(properties, dict):
            raise ToolTransportRejected("registry-schema")
        if (
            not 1 <= len(properties) <= 32
            or any(not isinstance(key, str) or NAME.fullmatch(key) is None for key in properties)
            or any(not isinstance(key, str) for key in required)
            or len(required) != len(set(required))
            or not set(required) <= set(properties)
            or any(key.casefold() in DANGEROUS_KEYS for key in properties)
            or any(kind not in {"string", "integer", "boolean"} for kind in properties.values())
        ):
            raise ToolTransportRejected("registry-schema")
    return value


def _nonnegative_metric(value: object) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= MAX_METRIC_VALUE
    )


def _valid_model(value: object) -> bool:
    return (
        isinstance(value, str)
        and MODEL.fullmatch(value) is not None
        and ".." not in value
        and "//" not in value
    )


def _valid_created_at(value: object) -> bool:
    if not isinstance(value, str) or RFC3339_UTC.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def _ollama(
    response: object,
    expected_model: object,
) -> tuple[str | None, str, dict[str, object], dict[str, object]]:
    if not _valid_model(expected_model):
        raise ToolTransportRejected("expected-model")
    if not isinstance(response, dict) or set(response) != OLLAMA_FIELDS:
        raise ToolTransportRejected("response-shape")
    if response["model"] != expected_model:
        raise ToolTransportRejected("model-mismatch")
    if not _valid_created_at(response["created_at"]):
        raise ToolTransportRejected("created-at")
    if response["done"] is not True:
        raise ToolTransportRejected("response-incomplete")
    if response["done_reason"] != "stop":
        raise ToolTransportRejected("stop-reason")
    metric_names = OLLAMA_FIELDS - {
        "model", "created_at", "message", "done", "done_reason"
    }
    if any(not _nonnegative_metric(response[name]) for name in metric_names):
        raise ToolTransportRejected("response-metric")
    message = response["message"]
    if not isinstance(message, dict) or set(message) != {"role", "content", "tool_calls"}:
        raise ToolTransportRejected("message-shape")
    if message["role"] != "assistant" or message["content"] not in {"", None}:
        raise ToolTransportRejected("mixed-assistant-content")
    calls = message["tool_calls"]
    if not isinstance(calls, list) or len(calls) != 1:
        raise ToolTransportRejected("tool-call-count")
    call = calls[0]
    if not isinstance(call, dict) or set(call) != {"id", "function"}:
        raise ToolTransportRejected("tool-call-shape")
    if not isinstance(call["id"], str) or CALL_ID.fullmatch(call["id"]) is None:
        raise ToolTransportRejected("tool-call-identity")
    function = call["function"]
    if not isinstance(function, dict) or set(function) != {"name", "arguments", "index"}:
        raise ToolTransportRejected("function-shape")
    if function["index"] != 0 or isinstance(function["index"], bool):
        raise ToolTransportRejected("function-index")
    if not isinstance(function["arguments"], dict):
        raise ToolTransportRejected("arguments-object")
    metrics = {name: response[name] for name in sorted(metric_names)}
    return call["id"], function["name"], function["arguments"], metrics


def _openai(response: object) -> tuple[str, str, dict[str, object]]:
    if not isinstance(response, dict) or set(response) != {"choices"}:
        raise ToolTransportRejected("response-shape")
    choices = response["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ToolTransportRejected("choice-count")
    choice = choices[0]
    if not isinstance(choice, dict) or set(choice) != {"message"}:
        raise ToolTransportRejected("choice-shape")
    message = choice["message"]
    if not isinstance(message, dict) or set(message) != {"role", "content", "tool_calls"}:
        raise ToolTransportRejected("message-shape")
    if message["role"] != "assistant" or message["content"] not in {"", None}:
        raise ToolTransportRejected("mixed-assistant-content")
    calls = message["tool_calls"]
    if not isinstance(calls, list) or len(calls) != 1:
        raise ToolTransportRejected("tool-call-count")
    call = calls[0]
    if not isinstance(call, dict) or set(call) != {"id", "type", "function"}:
        raise ToolTransportRejected("tool-call-shape")
    if call["type"] != "function" or not isinstance(call["id"], str) or CALL_ID.fullmatch(call["id"]) is None:
        raise ToolTransportRejected("tool-call-identity")
    function = call["function"]
    if not isinstance(function, dict) or set(function) != {"name", "arguments"}:
        raise ToolTransportRejected("function-shape")
    return call["id"], function["name"], _json_object(function["arguments"])


def evaluate(
    response: object,
    transport: str,
    trusted_registry: object,
    expected_model: object = None,
) -> dict[str, object]:
    registry = _registry(trusted_registry)
    parsed_response = _response_json(response)
    if transport == "ollama":
        call_id, name, arguments, metrics = _ollama(parsed_response, expected_model)
    elif transport == "openai-compatible":
        call_id, name, arguments = _openai(parsed_response)
        metrics = None
    else:
        raise ToolTransportRejected("transport-unsupported")
    if not isinstance(name, str) or NAME.fullmatch(name) is None or name not in registry:
        raise ToolTransportRejected("tool-not-allowed")
    _bounded(arguments)
    try:
        argument_bytes = len(json.dumps(arguments, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError) as error:
        raise ToolTransportRejected("arguments-value") from error
    if argument_bytes > MAX_ARGUMENT_BYTES:
        raise ToolTransportRejected("arguments-size")
    schema = registry[name]
    if not set(arguments) <= set(schema["properties"]):
        raise ToolTransportRejected("arguments-fields")
    if not set(schema["required"]) <= set(arguments):
        raise ToolTransportRejected("arguments-required")
    for key, kind in schema["properties"].items():
        value = arguments[key]
        valid = (
            kind == "string" and isinstance(value, str)
            or kind == "integer" and isinstance(value, int) and not isinstance(value, bool)
            or kind == "boolean" and isinstance(value, bool)
        )
        if not valid:
            raise ToolTransportRejected("arguments-type")
    return {
        "schemaVersion": 1,
        "kind": "structured-tool-call-candidate",
        "transport": transport,
        "model": expected_model if transport == "ollama" else None,
        "finalResponseValidated": transport == "ollama",
        "providerMetrics": metrics,
        "callId": call_id,
        "toolName": name,
        "arguments": arguments,
        "argumentsUntrusted": True,
        "executionAllowed": False,
        "approvalGranted": False,
        "runtimeAdmissionGranted": False,
        "effects": {
            "filesystemRead": False,
            "filesystemWrite": False,
            "networkAccess": False,
            "providerInvocation": False,
            "processCreation": False,
            "toolExecution": False
        }
    }


if __name__ == "__main__":
    print(json.dumps({"status": "offline-library-only", "runtimeAdmissionGranted": False}))
