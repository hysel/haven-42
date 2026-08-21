#!/usr/bin/env python3
"""Run sanitized Apple-Silicon Ollama qualification cells.

The runner accepts only candidates bound to the reviewed 16 GiB plan, contacts
IPv4 loopback, never records prompts or model responses, unloads after every
cell, and removes only models that this invocation pulled when explicitly
requested. Provider-level coding screens do not grant editor-agent admission.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any, Callable
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "config/alpha-2-apple-silicon-16gib-qualification-plan.json"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class QualificationError(ValueError):
    """The plan, host, provider, or candidate failed closed."""


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def progress(event: str, **fields: Any) -> None:
    """Emit one sanitized, line-buffered progress record for unattended runs."""
    record = {"event": event, **fields}
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)


def load_json(path: Path) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            raise QualificationError("unsafe-json-input")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise QualificationError("invalid-json-input") from error
    if not isinstance(value, dict):
        raise QualificationError("invalid-json-input")
    return value


def inventory_candidates(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for family in inventory.get("families", []):
        if not isinstance(family, dict):
            raise QualificationError("invalid-inventory")
        for version in family.get("versions", []):
            if not isinstance(version, dict):
                raise QualificationError("invalid-inventory")
            for candidate in version.get("candidates", []):
                if not isinstance(candidate, dict) or not isinstance(candidate.get("id"), str):
                    raise QualificationError("invalid-inventory")
                if candidate["id"] in records:
                    raise QualificationError("duplicate-inventory-candidate")
                records[candidate["id"]] = candidate
    return records


def validate_plan(plan: dict[str, Any], root: Path = ROOT) -> dict[str, dict[str, Any]]:
    if (
        plan.get("schemaVersion") != 1
        or plan.get("kind") != "haven42-apple-silicon-model-qualification-plan"
        or plan.get("status") != "qualification-only-no-product-promotion"
    ):
        raise QualificationError("invalid-plan-identity")
    rules = plan.get("rules")
    required_false = {
        "rawPromptsOrResponsesRetained", "privateIdentityRetained",
        "automaticDefaultChangeAllowed", "automaticSelectionEvidenceAllowed",
        "automaticSupportChangeAllowed", "continueEvidenceMayBeUsedForNewRecommendation",
    }
    if (
        not isinstance(rules, dict)
        or any(rules.get(key) is not False for key in required_false)
        or rules.get("pullOnlyAfterOwnerApproval") is not True
        or rules.get("ownerApprovalRecorded") is not True
        or rules.get("unloadAfterEveryCell") is not True
        or rules.get("removeOnlyModelsPulledByThisRun") is not True
        or rules.get("maintainedCodingSurfaceEvidenceRequiredForCodingRecommendation") is not True
    ):
        raise QualificationError("invalid-plan-rules")
    runtime = plan.get("runtime")
    if (
        not isinstance(runtime, dict)
        or runtime.get("provider") != "ollama"
        or runtime.get("transport") != "ipv4-loopback-only"
        or not isinstance(runtime.get("version"), str)
        or not SHA256.fullmatch(str(runtime.get("artifactSha256", "")))
    ):
        raise QualificationError("invalid-runtime-plan")
    hardware = plan.get("hardwareProfile")
    if (
        not isinstance(hardware, dict)
        or hardware.get("platformFamily") != "macos"
        or hardware.get("architecture") != "arm64"
        or hardware.get("backend") != "metal"
        or not isinstance(hardware.get("minimumSystemMemoryGiB"), (int, float))
        or not isinstance(hardware.get("minimumMemoryReserveGiB"), (int, float))
    ):
        raise QualificationError("invalid-hardware-plan")
    if plan.get("testContract") != {
        "version": 2,
        "generalChat": "exact-token",
        "contentWrite": "one-sentence-6-to-18-words-required-word",
        "contentSummarize": "one-sentence-6-to-24-words-exact-fact-labels",
        "structuredTool": "exact-single-read-file-call",
        "structuredCode": "exact-path-json-compile-and-execute",
    }:
        raise QualificationError("invalid-test-contract")
    binding = plan.get("inventoryBinding")
    if not isinstance(binding, dict) or set(binding) != {"path", "canonicalSha256"}:
        raise QualificationError("invalid-inventory-binding")
    inventory_path = root / str(binding["path"])
    try:
        inventory_path.resolve().relative_to(root.resolve())
    except ValueError as error:
        raise QualificationError("inventory-path-escaped-root") from error
    inventory = load_json(inventory_path)
    if canonical_sha256(inventory) != binding["canonicalSha256"]:
        raise QualificationError("stale-inventory-binding")
    reviewed = inventory_candidates(inventory)
    candidates = plan.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise QualificationError("invalid-plan-candidates")
    selected: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise QualificationError("invalid-plan-candidate")
        model_id = candidate.get("modelId")
        if not isinstance(model_id, str) or model_id in selected or model_id not in reviewed:
            raise QualificationError("invalid-plan-candidate-id")
        source = reviewed[model_id]
        for plan_key, source_key in (
            ("model", "model"), ("manifestDigest", "manifestDigest"),
            ("modelBytes", "modelBytes"),
        ):
            if candidate.get(plan_key) != source.get(source_key):
                raise QualificationError("plan-candidate-inventory-mismatch")
        if not SHA256.fullmatch(str(candidate["manifestDigest"])):
            raise QualificationError("invalid-model-digest")
        selected[model_id] = candidate
    return selected


def validate_origin(origin: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError as error:
        raise QualificationError("invalid-loopback-origin") from error
    if (
        parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
        or parsed.username is not None or parsed.password is not None
        or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
        or parsed.port is None or not 1024 <= parsed.port <= 65535
    ):
        raise QualificationError("invalid-loopback-origin")
    return f"http://127.0.0.1:{parsed.port}"


def request_json(origin: str, route: str, body: dict[str, Any] | None = None, timeout: int = 600) -> dict[str, Any]:
    if route not in {"/api/version", "/api/tags", "/api/pull", "/api/generate", "/api/chat", "/api/ps", "/api/delete"}:
        raise QualificationError("invalid-provider-route")
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    method = "DELETE" if route == "/api/delete" else ("GET" if data is None else "POST")
    request = urllib.request.Request(
        origin + route, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Haven42-Apple-Silicon-Qualification/1"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise QualificationError("provider-request-failed") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise QualificationError("provider-response-too-large")
    if not raw:
        return {}
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise QualificationError("invalid-provider-response") from error
    if not isinstance(value, dict) or value.get("error"):
        raise QualificationError("provider-returned-error")
    return value


def normalize_digest(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    return value[7:] if value.startswith("sha256:") else value


def installed_models(origin: str) -> dict[str, str]:
    records = request_json(origin, "/api/tags", timeout=30).get("models")
    if not isinstance(records, list):
        raise QualificationError("invalid-model-inventory")
    return {
        item["name"]: normalize_digest(item.get("digest")) or ""
        for item in records
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }


def response_text(value: dict[str, Any], route: str) -> str:
    text = value.get("response") if route == "/api/generate" else (value.get("message") or {}).get("content")
    return text.strip() if isinstance(text, str) else ""


def generation_metrics(value: dict[str, Any]) -> dict[str, Any]:
    count, duration = value.get("eval_count"), value.get("eval_duration")
    rate = None
    if isinstance(count, int) and not isinstance(count, bool) and isinstance(duration, int) and duration > 0:
        rate = round(count / (duration / 1_000_000_000), 3)
    return {
        "promptTokens": value.get("prompt_eval_count") if isinstance(value.get("prompt_eval_count"), int) else None,
        "outputTokens": count if isinstance(count, int) else None,
        "tokensPerSecond": rate,
        "totalDurationMs": round(value.get("total_duration", 0) / 1_000_000, 3) if isinstance(value.get("total_duration"), int) else None,
        "loadDurationMs": round(value.get("load_duration", 0) / 1_000_000, 3) if isinstance(value.get("load_duration"), int) else None,
    }


def unload(origin: str, model: str) -> bool:
    request_json(origin, "/api/generate", {"model": model, "stream": False, "keep_alive": 0}, timeout=60)
    for _ in range(40):
        running = request_json(origin, "/api/ps", timeout=15).get("models")
        if isinstance(running, list) and not any(
            isinstance(item, dict) and item.get("name") == model for item in running
        ):
            return True
        time.sleep(0.25)
    return False


def residency(origin: str, model: str) -> dict[str, Any]:
    running = request_json(origin, "/api/ps", timeout=15).get("models")
    matches = [item for item in running or [] if isinstance(item, dict) and item.get("name") == model]
    if len(matches) != 1:
        raise QualificationError("model-residency-not-observed")
    size, size_vram = matches[0].get("size"), matches[0].get("size_vram")
    if not isinstance(size, int) or size <= 0 or not isinstance(size_vram, int) or not 0 <= size_vram <= size:
        raise QualificationError("invalid-model-residency")
    return {"modelBytes": size, "metalResidentBytes": size_vram, "fullMetalResidency": size == size_vram}


def single_sentence(text: str) -> bool:
    return bool(text) and len(re.findall(r"[.!?]", text)) == 1 and "\n" not in text


def check_exact(text: str, expected: str) -> bool:
    return text == expected


def check_write(text: str, _: str) -> bool:
    words = re.findall(r"\b[\w'-]+\b", text)
    return single_sentence(text) and 6 <= len(words) <= 18 and "testing" in text.lower()


def check_summary(text: str, _: str) -> bool:
    words = re.findall(r"\b[\w'-]+\b", text)
    return single_sentence(text) and 6 <= len(words) <= 24 and all(label in text for label in ("RUNTIME_LOCAL", "MODEL_LOCAL", "CLEAR_REMOVAL"))


def parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def run_generate_cell(
    origin: str, model: str, prompt: str, validator: Callable[[str, str], bool], expected: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    value = request_json(origin, "/api/generate", {
        "model": model, "prompt": prompt, "think": False, "stream": False,
        "keep_alive": "5m", "options": {"temperature": 0, "seed": 42, "num_predict": 128},
    })
    text = response_text(value, "/api/generate")
    resident = residency(origin, model)
    passed = validator(text, expected)
    if not unload(origin, model):
        raise QualificationError("model-unload-failed")
    return {"status": "passed" if passed else "failed", "responseRetained": False}, {
        **generation_metrics(value), **resident, "unloadPassed": True,
    }


def run_tool_cell(origin: str, model: str) -> tuple[dict[str, Any], dict[str, Any]]:
    tool = {"type": "function", "function": {"name": "read_file", "description": "Read one repository file.", "parameters": {"type": "object", "properties": {"filepath": {"type": "string"}}, "required": ["filepath"]}}}
    value = request_json(origin, "/api/chat", {
        "model": model, "think": False, "stream": False, "keep_alive": "5m",
        "options": {"temperature": 0, "seed": 42, "num_predict": 128},
        "tools": [tool], "messages": [{"role": "user", "content": "Call read_file for README.md. Return only the tool call."}],
    })
    calls = (value.get("message") or {}).get("tool_calls") or []
    function = calls[0].get("function", {}) if len(calls) == 1 and isinstance(calls[0], dict) else {}
    passed = function.get("name") == "read_file" and function.get("arguments") == {"filepath": "README.md"}
    resident = residency(origin, model)
    if not unload(origin, model):
        raise QualificationError("model-unload-failed")
    return {"status": "passed" if passed else "failed", "responseRetained": False}, {
        **generation_metrics(value), **resident, "unloadPassed": True,
    }


def run_code_cell(origin: str, model: str) -> tuple[dict[str, Any], dict[str, Any]]:
    prompt = (
        'Return JSON only with exactly keys "path" and "code". Path must be app/main.py. '
        'Code must define def add(a: int, b: int) -> int and return a + b. No markdown.'
    )
    value = request_json(origin, "/api/generate", {
        "model": model, "prompt": prompt, "think": False, "stream": False,
        "keep_alive": "5m", "format": "json",
        "options": {"temperature": 0, "seed": 42, "num_predict": 192},
    })
    parsed = parse_json_object(response_text(value, "/api/generate"))
    passed = False
    if parsed is not None and set(parsed) == {"path", "code"} and parsed.get("path") == "app/main.py" and isinstance(parsed.get("code"), str):
        try:
            compiled = compile(parsed["code"], "app/main.py", "exec")
            namespace: dict[str, Any] = {}
            exec(compiled, namespace)
            passed = namespace.get("add") is not None and namespace["add"](2, 3) == 5
        except Exception:
            passed = False
    resident = residency(origin, model)
    if not unload(origin, model):
        raise QualificationError("model-unload-failed")
    return {"status": "passed" if passed else "failed", "responseRetained": False}, {
        **generation_metrics(value), **resident, "unloadPassed": True,
    }


def run_candidate(origin: str, candidate: dict[str, Any]) -> dict[str, Any]:
    model = candidate["model"]
    checks: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    cells = (
        ("generalChat", lambda: run_generate_cell(origin, model, "Reply exactly: MAC_CHAT_OK", check_exact, "MAC_CHAT_OK")),
        ("contentWrite", lambda: run_generate_cell(origin, model, "Write exactly one sentence of 6 to 18 words about careful software testing. Include the word testing.", check_write)),
        ("contentSummarize", lambda: run_generate_cell(origin, model, "Summarize in exactly one sentence of 6 to 24 words while preserving the exact labels RUNTIME_LOCAL, MODEL_LOCAL, and CLEAR_REMOVAL: A portable app keeps its runtime and model beside the app so removal is clear.", check_summary)),
        ("structuredTool", lambda: run_tool_cell(origin, model)),
        ("structuredCode", lambda: run_code_cell(origin, model)),
    )
    for name, execute in cells:
        started = time.monotonic()
        try:
            check, measurement = execute()
        except QualificationError as error:
            try:
                unloaded = unload(origin, model)
            except QualificationError:
                unloaded = False
            check = {"status": "failed", "errorCode": str(error), "responseRetained": False}
            measurement = {"unloadPassed": unloaded}
        check["durationSeconds"] = round(time.monotonic() - started, 3)
        checks[name] = check
        metrics[name] = measurement
    return {
        "modelId": candidate["modelId"], "model": model,
        "manifestDigest": candidate["manifestDigest"],
        "checks": checks, "metrics": metrics,
        "corePassed": all(item["status"] == "passed" for item in checks.values()),
        "codingSurfaceStatus": "not-run",
        "codingRecommendationEligible": False,
        "promotionBlock": candidate.get("promotionBlock"),
    }


def host_preflight(plan: dict[str, Any]) -> dict[str, Any]:
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise QualificationError("apple-silicon-host-required")
    try:
        memory = int(subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.memsize"], text=True).strip())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise QualificationError("system-memory-unavailable") from error
    minimum = float(plan["hardwareProfile"]["minimumSystemMemoryGiB"])
    if memory / 1024**3 < minimum:
        raise QualificationError("insufficient-system-memory")
    return {"platformFamily": "macos", "architecture": "arm64", "systemMemoryGiB": round(memory / 1024**3, 2), "backend": "metal"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=PLAN_PATH)
    parser.add_argument("--origin", default="http://127.0.0.1:11434")
    parser.add_argument("--model-id", action="append", default=[])
    parser.add_argument("--pull-missing", action="store_true")
    parser.add_argument("--remove-new-models", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        plan = load_json(args.plan)
        candidates = validate_plan(plan, ROOT)
        origin = validate_origin(args.origin)
        host = host_preflight(plan)
        if request_json(origin, "/api/version", timeout=20) != {"version": plan["runtime"]["version"]}:
            raise QualificationError("runtime-version-mismatch")
        requested = args.model_id or list(candidates)
        if len(requested) != len(set(requested)) or any(model_id not in candidates for model_id in requested):
            raise QualificationError("unreviewed-model-id")
        before = installed_models(origin)
        pulled: list[str] = []
        results: list[dict[str, Any]] = []
        cleanup: list[dict[str, Any]] = []
        progress("qualification-started", modelsRequested=len(requested))
        try:
            for ordinal, model_id in enumerate(requested, start=1):
                candidate = candidates[model_id]
                model = candidate["model"]
                progress("candidate-started", modelId=model_id, ordinal=ordinal, total=len(requested))
                if model not in before:
                    if not args.pull_missing:
                        results.append({"modelId": model_id, "model": model, "status": "blocked", "errorCode": "model-not-installed", "codingRecommendationEligible": False})
                        progress("candidate-finished", modelId=model_id, status="blocked")
                        continue
                    request_json(origin, "/api/pull", {"model": model, "stream": False}, timeout=3600)
                    pulled.append(model)
                current = installed_models(origin)
                if current.get(model) != candidate["manifestDigest"]:
                    results.append({"modelId": model_id, "model": model, "status": "failed", "errorCode": "manifest-digest-mismatch", "codingRecommendationEligible": False})
                    progress("candidate-finished", modelId=model_id, status="failed")
                    continue
                result = run_candidate(origin, candidate)
                result["status"] = "passed" if result["corePassed"] else "failed"
                results.append(result)
                progress("candidate-finished", modelId=model_id, status=result["status"])
        finally:
            if args.remove_new_models:
                for model in pulled:
                    try:
                        unload(origin, model)
                        request_json(origin, "/api/delete", {"model": model}, timeout=120)
                        removed = model not in installed_models(origin)
                    except QualificationError:
                        removed = False
                    cleanup.append({"model": model, "removed": removed})
                    progress("cleanup-finished", model=model, removed=removed)
        report = {
            "schemaVersion": 1,
            "kind": "haven42-apple-silicon-model-qualification-result",
            "release": plan["release"],
            "observedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "completed" if len(results) == len(requested) else "incomplete",
            "planCanonicalSha256": canonical_sha256(plan),
            "inventoryCanonicalSha256": plan["inventoryBinding"]["canonicalSha256"],
            "testContract": plan["testContract"],
            "runtime": {key: plan["runtime"][key] for key in ("provider", "version", "artifactSha256", "transport")},
            "hardwareProfile": host | {"profileId": plan["hardwareProfile"]["id"]},
            "modelsRequested": len(requested), "modelsPulled": len(pulled),
            "results": results, "cleanup": cleanup,
            "rawPromptsOrResponsesRetained": False,
            "privateIdentityRetained": False,
            "automaticDefaultChangeAllowed": False,
            "automaticSelectionEvidenceAllowed": False,
            "automaticSupportChangeAllowed": False,
        }
        encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_name(args.output.name + ".tmp")
            temporary.write_text(encoded, encoding="utf-8")
            os.replace(temporary, args.output)
        print(encoded, end="")
        progress("qualification-finished", status=report["status"], modelsCompleted=len(results))
        return 0 if all(item.get("status") == "passed" for item in results) else 1
    except QualificationError as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
