#!/usr/bin/env python3
"""Create a local-only anonymized packet for human writing-quality review."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import sys
import urllib.request
from typing import Any

from provider_security import ProviderSecurityError, read_json, validate_local_base_url


ROOT = Path(__file__).resolve().parent.parent
MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
MAX_RESPONSE_BYTES = 1024 * 1024
ALIASES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
CASES = (
    {
        "id": "schedule-email",
        "title": "Professional scheduling email",
        "prompt": (
            "Write a concise professional email in Markdown. Include the subject "
            "'Schedule update'. State that the design review moved from July 14 to "
            "July 16 because the accessibility audit needs two additional days. Ask "
            "the recipient to confirm availability by July 10. Do not invent names, "
            "times, locations, attachments, or project status."
        ),
        "reviewFocus": (
            "instruction compliance", "factual retention", "professional tone",
            "conciseness", "unsupported additions",
        ),
    },
    {
        "id": "executive-rewrite",
        "title": "Fact-preserving executive rewrite",
        "prompt": (
            "Rewrite the following as a calm executive update in Markdown without "
            "changing any fact or certainty level: 'Alice estimates the pilot may "
            "cost $4,200. Twelve of eighteen participants have responded. The "
            "decision is expected on September 3, but approval is uncertain.' Do not "
            "add a recommendation, cause, location, success rate, or conclusion."
        ),
        "reviewFocus": (
            "factual fidelity", "uncertainty preservation", "clarity",
            "executive tone", "unsupported additions",
        ),
    },
    {
        "id": "source-grounded-brief",
        "title": "Source-grounded public brief",
        "prompt": (
            "Create a short Markdown brief using exactly these headings: '## Facts', "
            "'## Risks', and '## Next step'. Source facts: the trial has 18 "
            "participants; results are preliminary; no safety conclusion is "
            "available; the next review is July 16. The next step is to review the "
            "remaining responses. Do not invent a sponsor, location, success rate, "
            "medical recommendation, or approval status."
        ),
        "reviewFocus": (
            "source grounding", "completeness", "organization", "readability",
            "unsupported additions",
        ),
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


def generate(
    base_url: str,
    model: str,
    prompt: str,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    response = provider_json(
        base_url,
        "/api/chat",
        timeout_seconds,
        {
            "model": model,
            "stream": False,
            "think": False,
            "keep_alive": 0,
            "options": {"temperature": 0.2, "seed": 42, "num_predict": 700},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Follow the writing request exactly. Preserve supplied facts "
                        "and uncertainty. Return only the requested Markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        },
    )
    output = response.get("message", {}).get("content")
    if not isinstance(output, str) or not output.strip():
        raise ProviderSecurityError("empty-model-output")
    metrics = {
        "outputSha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
        "outputLength": len(output),
        "inputTokens": response.get("prompt_eval_count"),
        "outputTokens": response.get("eval_count"),
    }
    return output.strip(), metrics


def render_packet(cases: list[dict[str, Any]], created_at: str) -> str:
    lines = [
        "# Haven 42 Blind Writing Review",
        "",
        f"Packet created: {created_at}",
        "",
        "The candidate labels are randomized independently for every scenario.",
        "Do not inspect the separate local answer key until scoring is complete.",
        "",
        "Score each output from 1 (poor) to 5 (excellent) for every listed",
        "criterion. Record a forced overall rank with no ties for each scenario.",
        "",
    ]
    for index, case in enumerate(cases, start=1):
        lines.extend([
            f"## Scenario {index}: {case['title']}",
            "",
            "### Request",
            "",
            case["prompt"],
            "",
            "### Review criteria",
            "",
            *[f"- {item}" for item in case["reviewFocus"]],
            "",
        ])
        for candidate in case["candidates"]:
            lines.extend([
                f"### Candidate {candidate['alias']}",
                "",
                candidate["output"],
                "",
                f"Scores for Candidate {candidate['alias']}: "
                + " / ".join(f"{criterion}=__" for criterion in case["reviewFocus"]),
                "",
            ])
        labels = ", ".join(candidate["alias"] for candidate in case["candidates"])
        lines.extend([
            f"Overall rank, best to worst ({labels}): __",
            "",
            "Reviewer notes: __",
            "",
        ])
    return "\n".join(lines) + "\n"


def validate_output_directory(value: str) -> Path:
    requested = Path(value).absolute()
    if requested.exists() and requested.is_symlink():
        raise ValueError("output directory cannot use a symbolic link")
    if requested.is_relative_to(ROOT):
        for candidate in (requested, *requested.parents):
            if candidate.exists() and candidate.is_symlink():
                raise ValueError("repository output cannot use a symbolic link")
            if candidate == ROOT:
                break
    resolved = requested.resolve()
    if resolved.is_relative_to(ROOT) and not resolved.is_relative_to(ROOT / "dist"):
        raise ValueError("repository-local review output must stay under ignored dist/")
    resolved.mkdir(parents=True, exist_ok=True)
    packet_path = resolved / "blind-review-packet.md"
    key_path = resolved / "blind-review-answer-key.json"
    if packet_path.exists() or key_path.exists():
        raise ValueError("blind review output already exists; refusing to overwrite")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ollama-base-url", required=True)
    parser.add_argument("--model", action="append", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--output-directory", required=True)
    args = parser.parse_args()
    if args.timeout_seconds < 30 or args.timeout_seconds > 900:
        parser.error("--timeout-seconds must be from 30 through 900")
    if len(args.model) < 2 or len(args.model) > 8:
        parser.error("two through eight models are required")
    if len(set(args.model)) != len(args.model) or any(
        not MODEL_NAME.fullmatch(model) for model in args.model
    ):
        parser.error("models must be unique valid Ollama names")

    try:
        output_directory = validate_output_directory(args.output_directory)
    except (OSError, ValueError) as error:
        parser.error(str(error))
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
    if any(model not in artifacts or not DIGEST.fullmatch(artifacts[model]) for model in args.model):
        print("Every requested model must already exist with an exact digest.", file=sys.stderr)
        return 2

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    packet_cases: list[dict[str, Any]] = []
    answer_cases: list[dict[str, Any]] = []
    completed_models: set[str] = set()
    final_unloads: dict[str, bool] = {}
    try:
        for case in CASES:
            generated = []
            for model in args.model:
                output, metrics = generate(base_url, model, case["prompt"], args.timeout_seconds)
                unloaded = unload_and_verify(base_url, model, args.timeout_seconds)
                if not unloaded:
                    raise ProviderSecurityError("per-sample-unload-not-verified")
                completed_models.add(model)
                generated.append({
                    "model": model,
                    "digest": artifacts[model],
                    "output": output,
                    "metrics": metrics,
                })
            secrets.SystemRandom().shuffle(generated)
            candidates = []
            answer_candidates = []
            for alias, record in zip(ALIASES[:len(generated)], generated, strict=True):
                candidates.append({"alias": alias, "output": record["output"]})
                answer_candidates.append({
                    "alias": alias,
                    "model": record["model"],
                    "digest": record["digest"],
                    **record["metrics"],
                })
            packet_cases.append({
                "id": case["id"],
                "title": case["title"],
                "prompt": case["prompt"],
                "reviewFocus": case["reviewFocus"],
                "candidates": candidates,
            })
            answer_cases.append({"id": case["id"], "candidates": answer_candidates})
    except (OSError, ProviderSecurityError, KeyError, TypeError) as error:
        print(f"Blind review generation failed: {error}", file=sys.stderr)
        return 2
    finally:
        final_unloads = {
            model: unload_and_verify(base_url, model, args.timeout_seconds)
            for model in args.model
        }

    if not all(final_unloads.values()):
        print("Final model unload verification failed.", file=sys.stderr)
        return 2
    packet_path = output_directory / "blind-review-packet.md"
    key_path = output_directory / "blind-review-answer-key.json"
    packet_path.write_text(render_packet(packet_cases, created_at), encoding="utf-8")
    key_path.write_text(json.dumps({
        "schemaVersion": 1,
        "kind": "blind-writing-review-answer-key",
        "createdAtUtc": created_at,
        "provider": {
            "id": "ollama",
            "version": str(version.get("version", "unknown"))[:64],
            "trustScope": policy["trustScope"],
            "endpointPersisted": False,
        },
        "generation": {
            "temperature": 0.2,
            "seed": 42,
            "maxOutputTokens": 700,
            "rawOutputCommitted": False,
        },
        "cases": answer_cases,
        "finalUnloadVerified": final_unloads,
    }, indent=2) + "\n", encoding="utf-8")
    print(packet_path)
    print(key_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
