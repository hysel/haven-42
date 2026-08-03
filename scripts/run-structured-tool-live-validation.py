#!/usr/bin/env python3
"""Manual, bounded Ollama tool-envelope validation with sanitized evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot-load-{name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SECURITY = _load("haven42_provider_security", ROOT / "scripts/provider_security.py")
TRANSPORT = _load(
    "haven42_structured_tool_transport",
    ROOT / "scripts/evaluate-structured-tool-transport.py",
)
EXPECTED_VERSION = "0.32.5"
MAX_LIVE_RESPONSE_BYTES = TRANSPORT.MAX_RESPONSE_BYTES
TOOL = {
    "type": "function",
    "function": {
        "name": "lookup_context",
        "description": "Return synthetic validation context.",
        "parameters": {
            "type": "object",
            "required": ["query", "limit", "includeMetadata"],
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
                "includeMetadata": {"type": "boolean"},
            },
        },
    },
}
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


class LiveValidationError(RuntimeError):
    pass


class HttpFailure(LiveValidationError):
    def __init__(self, status: int, body: bytes = b"") -> None:
        super().__init__(f"provider-http-{status}")
        self.status = status
        self.body = body[:4096]


def make_requester(base_url: str, timeout: int):
    opener = urllib.request.build_opener(SECURITY._NoRedirect())

    def request(path: str, payload: object | None = None, maximum: int = 65536) -> bytes:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {} if data is None else {"Content-Type": "application/json"}
        call = urllib.request.Request(base_url + path, data=data, headers=headers)
        try:
            with opener.open(call, timeout=timeout) as response:
                length = response.headers.get("Content-Length")
                if length is not None and int(length) > maximum:
                    raise LiveValidationError("provider-response-too-large")
                body = response.read(maximum + 1)
        except urllib.error.HTTPError as error:
            body = error.read(4097)
            raise HttpFailure(error.code, body) from error
        if len(body) > maximum:
            raise LiveValidationError("provider-response-too-large")
        return body

    return request


def _object(raw: bytes) -> dict[str, object]:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            if key in result:
                raise LiveValidationError("duplicate-provider-json-key")
            result[key] = value
        return result
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LiveValidationError("invalid-provider-json") from error
    if not isinstance(value, dict):
        raise LiveValidationError("provider-json-root")
    return value


def _unsupported(error: HttpFailure) -> bool:
    if error.status != 400:
        return False
    try:
        value = _object(error.body)
    except LiveValidationError:
        return False
    message = value.get("error")
    return isinstance(message, str) and "does not support tools" in message.casefold()


def _tool_shape(raw: bytes) -> dict[str, object]:
    """Return key/type metadata only; never retain generated values."""
    try:
        value = _object(raw)
        message = value.get("message")
        calls = message.get("tool_calls") if isinstance(message, dict) else None
        call = calls[0] if isinstance(calls, list) and len(calls) == 1 else None
        function = call.get("function") if isinstance(call, dict) else None
        arguments = function.get("arguments") if isinstance(function, dict) else None
        return {
            "callKeys": sorted(call) if isinstance(call, dict) else [],
            "functionKeys": sorted(function) if isinstance(function, dict) else [],
            "argumentsType": type(arguments).__name__,
        }
    except (LiveValidationError, TypeError, ValueError):
        return {"callKeys": [], "functionKeys": [], "argumentsType": "unavailable"}


def validate(request, models: list[str]) -> dict[str, object]:
    if not models or any(
        not TRANSPORT._valid_model(model)
        for model in models
    ):
        raise LiveValidationError("invalid-model-request")
    version = _object(request("/api/version"))
    if set(version) != {"version"} or version["version"] != EXPECTED_VERSION:
        raise LiveValidationError("ollama-version-not-validated")
    tags = _object(request("/api/tags"))
    installed = tags.get("models")
    if not isinstance(installed, list):
        raise LiveValidationError("invalid-model-inventory")
    installed_names = {
        item.get("name") for item in installed
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }
    results: list[dict[str, object]] = []
    for model in models:
        if model not in installed_names:
            results.append({"model": model, "outcome": "not-installed"})
            continue
        payload = {
            "model": model,
            "stream": False,
            "think": False,
            "messages": [{
                "role": "user",
                "content": (
                    "Call lookup_context exactly once with query synthetic-validation, "
                    "limit 2, and includeMetadata false. Return no prose."
                ),
            }],
            "tools": [TOOL],
            "options": {"temperature": 0, "num_predict": 256},
        }
        try:
            raw = request("/api/chat", payload, MAX_LIVE_RESPONSE_BYTES)
            candidate = TRANSPORT.evaluate(
                raw, "ollama", REGISTRY, expected_model=model
            )
            arguments = candidate["arguments"]
            exact = arguments == {
                "query": "synthetic-validation",
                "limit": 2,
                "includeMetadata": False,
            }
            results.append({
                "model": model,
                "outcome": "pass" if exact else "argument-mismatch",
                "toolName": candidate["toolName"],
                "finalResponseValidated": candidate["finalResponseValidated"],
                "rawContentRetained": False,
                "argumentsRetained": False,
            })
        except HttpFailure as error:
            results.append({
                "model": model,
                "outcome": (
                    "model-does-not-support-tools" if _unsupported(error)
                    else f"provider-http-{error.status}"
                ),
            })
        except TRANSPORT.ToolTransportRejected as error:
            results.append({
                "model": model,
                "outcome": f"rejected:{error}",
                "responseShape": _tool_shape(raw),
            })
        except LiveValidationError as error:
            results.append({"model": model, "outcome": f"rejected:{error}"})
        finally:
            try:
                request("/api/generate", {"model": model, "keep_alive": 0})
            except (LiveValidationError, HttpFailure):
                results[-1]["unloadConfirmed"] = False
            else:
                results[-1]["unloadConfirmed"] = True
    return {
        "schemaVersion": 1,
        "evidenceType": "manual-live-ollama-tool-envelope",
        "ollamaVersion": EXPECTED_VERSION,
        "endpointRetained": False,
        "promptOrResponseContentRetained": False,
        "models": results,
        "runtimeAdmissionGranted": False,
        "toolExecutionAllowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--trust-scope", choices=("loopback", "trusted-lan"), required=True)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if not args.live:
        raise SystemExit("refusing network activity without --live")
    if not 1 <= args.timeout <= 600:
        raise SystemExit("timeout must be between 1 and 600 seconds")
    validated = SECURITY.validate_base_url(args.endpoint, args.trust_scope)
    evidence = validate(
        make_requester(validated["baseUrl"], args.timeout),
        list(dict.fromkeys(args.models)),
    )
    session = ROOT / "dist/local-review" / (
        "structured-tool-live-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    session.mkdir(mode=0o700, parents=True, exist_ok=False)
    output = session / "sanitized-evidence.json"
    SECURITY.write_new_file(
        output, (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    try:
        display_path = str(output.relative_to(ROOT))
    except ValueError:
        display_path = "operator-selected-output"
    print(json.dumps({"status": "complete", "evidence": display_path, "results": evidence["models"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
