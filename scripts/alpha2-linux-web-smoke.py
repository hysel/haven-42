#!/usr/bin/env python3
"""Exercise Haven 42's loopback HTTP path against a reviewed local model.

Responses remain in memory and are never printed or written. Output contains
only bounded performance counts and pass/fail metadata suitable for private
campaign evidence. This script does not install or download anything.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import threading
from typing import Any
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent.parent
WEB_PATH = ROOT / "web/server.py"
MODEL_IDS = {
    "qwen3.5:0.8b": "qwen35-08b-q8",
    "qwen3.5:2b": "qwen35-2b-q8",
    "qwen3.5:4b": "qwen35-4b-q4",
}
CAPABILITIES = ("general.chat", "content.write", "content.summarize")
PROMPTS = {
    "general.chat": "Reply with one short sentence confirming local chat is available.",
    "content.write": "Write one concise sentence encouraging careful software testing.",
    "content.summarize": "Summarize in one sentence: Portable software keeps its managed files beside the app.",
}
SAFE_PROFILE = re.compile(r"^[a-z0-9][a-z0-9.-]{0,79}$")
MAX_RESPONSE_BYTES = 4 * 1024 * 1024


class SmokeError(ValueError):
    """The application-level smoke test failed closed."""


def _load_web() -> Any:
    spec = importlib.util.spec_from_file_location("alpha2_linux_web_smoke_server", WEB_PATH)
    if spec is None or spec.loader is None:
        raise SmokeError("web-server-module-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _private_root(path: Path) -> Path:
    if path.is_symlink():
        raise SmokeError("unsafe-private-evidence-root")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise SmokeError("private-evidence-root-missing") from error
    if not resolved.is_dir():
        raise SmokeError("private-evidence-root-missing")
    if os.name == "posix" and stat.S_IMODE(resolved.stat().st_mode) & 0o022:
        raise SmokeError("unsafe-private-evidence-root")
    return resolved


def _request(
    origin: str, route: str, *, token: str | None = None,
    body: dict[str, Any] | None = None, timeout: int = 180,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers.update({
            "Content-Type": "application/json",
            "Origin": origin,
            "Sec-Fetch-Site": "same-origin",
            "X-Haven-Token": token or "",
        })
    request = urllib.request.Request(
        origin + route,
        data=data,
        headers=headers,
        method="GET" if data is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise SmokeError("haven-http-request-failed") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise SmokeError("haven-http-response-too-large")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise SmokeError("haven-http-response-invalid") from error
    if not isinstance(value, dict) or value.get("error"):
        raise SmokeError("haven-http-response-invalid")
    return value


def _metrics(reply: dict[str, Any], capability: str) -> dict[str, Any]:
    details = reply.get("runDetails")
    context = reply.get("context")
    if (
        reply.get("capabilityId") != capability
        or not isinstance(reply.get("content"), str)
        or not reply["content"].strip()
        or reply.get("modelDigestVerified") is not True
        or reply.get("modelUnloaded") is not True
        or not isinstance(details, dict)
        or details.get("providerReported") is not True
        or not isinstance(context, dict)
        or context.get("providerTrustScope") != "loopback"
        or context.get("persisted") is not False
        or context.get("filesystemAccessAllowed") is not False
        or context.get("toolInvocationAllowed") is not False
    ):
        raise SmokeError("haven-text-contract-failed")
    for key in ("inputTokens", "outputTokens", "totalTokens"):
        if isinstance(details.get(key), bool) or not isinstance(details.get(key), int) or details[key] <= 0:
            raise SmokeError("haven-text-metrics-invalid")
    rate = details.get("tokensPerSecond")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(rate) or rate <= 0:
        raise SmokeError("haven-text-metrics-invalid")
    return {
        "capability": capability,
        "inputTokens": details["inputTokens"],
        "outputTokens": details["outputTokens"],
        "tokensPerSecond": round(float(rate), 3),
        "modelUnloaded": True,
    }


def run(*, private_root: Path, model: str, operating_system_id: str) -> dict[str, Any]:
    if model not in MODEL_IDS or not SAFE_PROFILE.fullmatch(operating_system_id):
        raise SmokeError("unreviewed-smoke-profile")
    evidence_root = _private_root(private_root)
    web = _load_web()
    state = web.HavenState(diagnostic_root=evidence_root / "Haven42-Logs")
    server = web.HavenWebServer(("127.0.0.1", 0), state)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
    thread.start()
    origin = server.expected_origin
    try:
        bootstrap = _request(origin, "/api/bootstrap")
        token = bootstrap.get("sessionToken")
        if not isinstance(token, str) or len(token) < 32:
            raise SmokeError("haven-session-token-missing")
        connected = _request(
            origin,
            "/api/connect",
            token=token,
            body={
                "endpoint": "http://127.0.0.1:11435",
                "timeoutSeconds": 120,
                "idleUnloadSeconds": 0,
                "authentication": {"mode": "none", "apiKey": ""},
            },
        )
        if (
            connected.get("connected") is not True
            or connected.get("trustScope") != "loopback"
            or connected.get("configurationPersisted") is not False
            or model not in connected.get("models", [])
        ):
            raise SmokeError("haven-provider-connect-contract-failed")
        measurements = []
        for capability in CAPABILITIES:
            reply = _request(
                origin,
                "/api/text",
                token=token,
                body={
                    "capabilityId": capability,
                    "model": model,
                    "messages": [{"role": "user", "content": PROMPTS[capability]}],
                },
                timeout=300,
            )
            measurements.append(_metrics(reply, capability))
        shutdown = _request(origin, "/api/shutdown", token=token, body={})
        if shutdown != {"shutdownAccepted": True, "modelCleanupVerified": True}:
            raise SmokeError("haven-shutdown-contract-failed")
        thread.join(timeout=10)
        if thread.is_alive():
            raise SmokeError("haven-web-server-did-not-stop")
        return {
            "schemaVersion": 1,
            "kind": "alpha2-linux-haven-web-smoke",
            "outcome": "passed",
            "operatingSystemId": operating_system_id,
            "modelId": MODEL_IDS[model],
            "provider": "ollama",
            "providerVersion": connected.get("version"),
            "trustScope": "loopback",
            "capabilities": measurements,
            "containsRawPromptsOrResponses": False,
            "containsPrivateMachineIdentity": False,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--model", choices=sorted(MODEL_IDS), required=True)
    parser.add_argument("--operating-system-id", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(
            private_root=args.private_root,
            model=args.model,
            operating_system_id=args.operating_system_id,
        ), indent=2, sort_keys=True))
    except SmokeError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
