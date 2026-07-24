#!/usr/bin/env python3
"""Run a bounded, sanitized Ollama writing-candidate matrix.

The harness uses only embedded synthetic material, records no response text,
and unloads each tested model before continuing.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import urllib.request
from typing import Any

from provider_security import ProviderSecurityError, read_json, validate_local_base_url


MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
MAX_RESPONSE_BYTES = 1024 * 1024
CASES = (
    {
        "id": "professional-email",
        "prompt": (
            "Write a concise professional email in Markdown. It must include the subject "
            "'Schedule update', state that the review moved from July 14 to July 16, ask "
            "the recipient to confirm availability, and make no other factual claims."
        ),
        "required": ("Schedule update", "July 14", "July 16", "confirm"),
        "forbidden": ("verified", "guaranteed"),
    },
    {
        "id": "fact-preserving-rewrite",
        "prompt": (
            "Rewrite this as a calm executive update without changing facts: "
            "'Alice estimates the pilot may cost $4,200. The decision is expected on "
            "September 3, but approval is uncertain.' Preserve every name, number, date, "
            "and uncertainty marker."
        ),
        "required": ("Alice", "$4,200", "September 3", "uncertain"),
        "forbidden": ("approved", "confirmed"),
    },
    {
        "id": "structured-brief",
        "prompt": (
            "Create a Markdown brief using exactly these headings: '## Facts', "
            "'## Risks', and '## Next step'. Facts: the trial has 18 participants; "
            "results are preliminary; no safety conclusion is available. Do not invent "
            "a location, sponsor, success rate, or medical recommendation."
        ),
        "required": (
            "## Facts", "## Risks", "## Next step", "18",
            "preliminary", "no safety conclusion",
        ),
        "forbidden": ("success rate", "safe to", "recommend taking"),
    },
)


def provider_json(
    base_url: str,
    path: str,
    timeout_seconds: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    headers: dict[str, str] = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        headers=headers,
        method=method,
    )
    return read_json(request, timeout_seconds, MAX_RESPONSE_BYTES)


def bounded_integer(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**18:
        return None
    return value


def unload_and_verify(base_url: str, model: str, timeout_seconds: int) -> bool:
    try:
        provider_json(
            base_url,
            "/api/generate",
            min(timeout_seconds, 30),
            {"model": model, "prompt": "", "stream": False, "keep_alive": 0},
        )
        processes = provider_json(base_url, "/api/ps", min(timeout_seconds, 30))
        loaded = {
            str(item.get("name") or item.get("model", ""))
            for item in processes.get("models", [])
            if isinstance(item, dict)
        }
        return model not in loaded
    except (OSError, ProviderSecurityError):
        return False


def run_case(
    base_url: str,
    model: str,
    case: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    started = time.monotonic()
    response: dict[str, Any] = {}
    error_code: str | None = None
    output = ""
    try:
        response = provider_json(
            base_url,
            "/api/chat",
            timeout_seconds,
            {
                "model": model,
                "stream": False,
                "think": False,
                "keep_alive": 0,
                "options": {"temperature": 0, "num_predict": 512},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Follow the supplied writing constraints exactly. Return only "
                            "the requested content and do not add unsupported facts."
                        ),
                    },
                    {"role": "user", "content": case["prompt"]},
                ],
            },
        )
        output = str(response.get("message", {}).get("content", ""))
        if not output.strip():
            error_code = "EMPTY_RESPONSE"
    except (OSError, ProviderSecurityError, KeyError, TypeError):
        error_code = "PROVIDER_REQUEST_FAILED"
    unloaded = unload_and_verify(base_url, model, timeout_seconds)
    folded = output.casefold()
    required = {
        marker: marker.casefold() in folded
        for marker in case["required"]
    }
    forbidden = {
        marker: marker.casefold() in folded
        for marker in case["forbidden"]
    }
    prompt_tokens = bounded_integer(response.get("prompt_eval_count"))
    output_tokens = bounded_integer(response.get("eval_count"))
    eval_duration = bounded_integer(response.get("eval_duration"))
    return {
        "caseId": case["id"],
        "status": (
            "passed"
            if error_code is None
            and all(required.values())
            and not any(forbidden.values())
            and unloaded
            else "failed"
        ),
        "errorCode": error_code,
        "requiredMarkers": required,
        "forbiddenMarkersPresent": forbidden,
        "outputSha256": hashlib.sha256(output.encode("utf-8")).hexdigest() if output else None,
        "outputLength": len(output),
        "providerMetrics": {
            "inputTokens": prompt_tokens,
            "outputTokens": output_tokens,
            "totalTokens": (
                prompt_tokens + output_tokens
                if prompt_tokens is not None and output_tokens is not None
                else None
            ),
            "tokensPerSecond": (
                round(output_tokens / (eval_duration / 1_000_000_000), 2)
                if output_tokens is not None and eval_duration
                else None
            ),
            "totalDurationMs": (
                round(value / 1_000_000, 2)
                if (value := bounded_integer(response.get("total_duration"))) is not None
                else None
            ),
            "wallDurationMs": round((time.monotonic() - started) * 1000, 2),
        },
        "modelUnloaded": unloaded,
        "rawOutputPersisted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ollama-base-url", required=True)
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.timeout_seconds < 30 or args.timeout_seconds > 900:
        parser.error("--timeout-seconds must be from 30 through 900")
    if len(args.model) < 1 or len(args.model) > 8 or any(
        not MODEL_NAME.fullmatch(model) for model in args.model
    ):
        parser.error("model names must be unique valid Ollama names")
    if len(set(args.model)) != len(args.model):
        parser.error("duplicate model")
    try:
        policy = validate_local_base_url(args.ollama_base_url)
        base_url = policy["baseUrl"]
        version = provider_json(base_url, "/api/version", 30)
        tags = provider_json(base_url, "/api/tags", 30)
    except (OSError, ProviderSecurityError) as error:
        print(f"Provider discovery failed: {error}", file=sys.stderr)
        return 2
    artifacts = {
        str(item.get("name") or item.get("model", "")): str(item.get("digest", "")).lower()
        for item in tags.get("models", [])
        if isinstance(item, dict)
    }
    missing = [model for model in args.model if model not in artifacts]
    invalid_digests = [
        model for model in args.model if not DIGEST.fullmatch(artifacts.get(model, ""))
    ]
    if missing or invalid_digests:
        print(json.dumps({
            "error": "exact-model-artifacts-required",
            "missingModels": missing,
            "invalidDigestModels": invalid_digests,
        }))
        return 2
    records = []
    try:
        for model in args.model:
            cases = [
                run_case(base_url, model, case, args.timeout_seconds)
                for case in CASES
            ]
            records.append({
                "model": model,
                "digest": artifacts[model],
                "status": "passed" if all(case["status"] == "passed" for case in cases) else "failed",
                "cases": cases,
            })
    finally:
        final_unloads = {
            model: unload_and_verify(base_url, model, args.timeout_seconds)
            for model in args.model
        }
    result = {
        "schemaVersion": 1,
        "kind": "writing-model-matrix",
        "createdAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider": {
            "id": "ollama",
            "version": str(version.get("version", "unknown"))[:64],
            "trustScope": policy["trustScope"],
            "endpointPersisted": False,
        },
        "promptSet": {
            "id": "haven42-writing-matrix-v1",
            "caseCount": len(CASES),
            "syntheticOnly": True,
            "rawInputsPersisted": False,
        },
        "records": records,
        "finalUnloadVerified": final_unloads,
        "rawOutputsPersisted": False,
        "humanQualityReviewComplete": False,
        "promotionAllowed": False,
    }
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0 if all(final_unloads.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
