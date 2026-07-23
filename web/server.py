#!/usr/bin/env python3
"""Haven 42 local-web application.

This process binds only to IPv4 loopback, serves bundled assets, and proxies
bounded requests to an explicitly selected Ollama endpoint. Configuration and
text content stay in memory and are never written by this server.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import secrets
import sys
import threading
import time
import urllib.request
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
STATIC_ROOT = Path(__file__).resolve().parent / "static"
sys.path.insert(0, str(ROOT / "scripts"))

from provider_security import (  # noqa: E402
    MAX_JSON_RESPONSE_BYTES,
    ProviderSecurityError,
    read_json,
    validate_local_base_url,
)


APP_VERSION = "0.3.0"
MAX_REQUEST_BYTES = 64 * 1024
MAX_MESSAGE_BYTES = 32 * 1024
MAX_CHAT_RESPONSE_BYTES = 1024 * 1024
MAX_CONVERSATION_MESSAGES = 20
ALLOWED_IDLE_UNLOAD_SECONDS = {0, 300, 900, 1800}
CAPABILITY_PROMPTS = {
    "general.chat": (
        "Answer the user's general question clearly. Do not claim repository access "
        "or actions you did not perform."
    ),
    "content.write": (
        "Create the requested general-purpose content as clean Markdown. Do not claim "
        "external facts were verified unless the user supplied them."
    ),
    "content.summarize": (
        "Summarize only the material supplied by the user. Preserve uncertainty and "
        "do not invent missing facts. Return clean Markdown."
    ),
}
MODEL_RECOMMENDATIONS_PATH = ROOT / "config" / "text-capability-model-recommendations.json"
EVIDENCE_CATALOG_PATH = ROOT / "config" / "evidence-catalog.tsv"


class WebRequestError(ValueError):
    def __init__(self, code: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(code)
        self.code = code
        self.status = status


def load_model_recommendations(
    path: Path = MODEL_RECOMMENDATIONS_PATH,
    evidence_path: Path = EVIDENCE_CATALOG_PATH,
) -> dict[str, tuple[dict[str, Any], ...]]:
    """Load the exact, evidence-gated text catalog; fail closed on malformed data."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        with evidence_path.open(encoding="utf-8", newline="") as stream:
            evidence_records = tuple(csv.DictReader(stream, delimiter="\t"))
        if (
            not isinstance(value, dict)
            or value.get("schemaVersion") != 1
            or not isinstance(value.get("capabilities"), dict)
        ):
            return {}
        result: dict[str, tuple[dict[str, Any], ...]] = {}
        for capability_id, records in value["capabilities"].items():
            if capability_id not in CAPABILITY_PROMPTS or not isinstance(records, list):
                return {}
            admitted: list[dict[str, Any]] = []
            for record in records:
                if (
                    not isinstance(record, dict)
                    or set(record) != {
                        "model", "priority", "evidenceId", "evidenceStatus",
                        "evidenceOperation", "evidence",
                    }
                    or not isinstance(record["model"], str)
                    or not record["model"].strip()
                    or len(record["model"]) > 256
                    or not isinstance(record["priority"], int)
                    or record["evidenceStatus"] != "passed"
                    or not isinstance(record["evidenceId"], str)
                    or not record["evidenceId"].strip()
                    or not isinstance(record["evidenceOperation"], str)
                    or not isinstance(record["evidence"], str)
                    or not any(
                        evidence.get("area") == "general-capability"
                        and evidence.get("provider") == "Ollama"
                        and evidence.get("model") == record["model"]
                        and evidence.get("operation") == record["evidenceOperation"]
                        and evidence.get("status") == "validated-by-tests"
                        and evidence.get("evidence") == record["evidence"]
                        for evidence in evidence_records
                    )
                ):
                    return {}
                admitted.append({
                    "model": record["model"],
                    "priority": record["priority"],
                    "evidenceId": record["evidenceId"],
                })
            result[capability_id] = tuple(sorted(
                admitted,
                key=lambda item: (-item["priority"], item["model"]),
            ))
        return result
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, csv.Error):
        return {}


def build_model_decisions(
    installed_models: list[str],
    catalog: dict[str, tuple[dict[str, Any], ...]],
) -> dict[str, Any]:
    installed = set(installed_models)
    evidenced_anywhere = {
        record["model"]
        for records in catalog.values()
        for record in records
    }
    recommendations: dict[str, dict[str, Any]] = {}
    for capability_id in CAPABILITY_PROMPTS:
        candidates = catalog.get(capability_id, ())
        chosen = next((record for record in candidates if record["model"] in installed), None)
        if chosen is not None:
            recommendations[capability_id] = {
                "status": "recommended",
                "model": chosen["model"],
                "evidenceId": chosen["evidenceId"],
                "hardwareFit": "unknown",
                "automatic": True,
            }
        elif candidates:
            recommendations[capability_id] = {
                "status": "missing",
                "model": candidates[0]["model"],
                "evidenceId": candidates[0]["evidenceId"],
                "hardwareFit": "unknown",
                "automatic": False,
            }
        else:
            recommendations[capability_id] = {
                "status": "missing",
                "model": None,
                "evidenceId": None,
                "hardwareFit": "unknown",
                "automatic": False,
            }
    options = []
    for model in installed_models:
        capability_status = {}
        for capability_id in CAPABILITY_PROMPTS:
            exact = any(record["model"] == model for record in catalog.get(capability_id, ()))
            capability_status[capability_id] = (
                "recommended"
                if exact
                else "compatible"
                if model in evidenced_anywhere
                else "unverified"
            )
        options.append({"name": model, "capabilityStatus": capability_status})
    return {
        "catalogStatus": "ready" if catalog else "unavailable",
        "recommendations": recommendations,
        "modelOptions": options,
        "downloadsPerformed": False,
    }


def _provider_json(
    base_url: str,
    path: str,
    timeout: int,
    payload: dict[str, Any] | None = None,
    maximum_bytes: int = MAX_JSON_RESPONSE_BYTES,
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
    return read_json(request, timeout, maximum_bytes)


class HavenState:
    def __init__(self, recommendation_path: Path = MODEL_RECOMMENDATIONS_PATH) -> None:
        self.csrf_token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.base_url: str | None = None
        self.trust_scope: str | None = None
        self.timeout_seconds = 120
        self.idle_unload_seconds = 300
        self.models: tuple[str, ...] = ()
        self.ollama_version: str | None = None
        self.used_models: set[tuple[str, str, int]] = set()
        self.active_model: tuple[str, str, int] | None = None
        self.idle_timer: threading.Timer | None = None
        self.lifecycle_generation = 0
        self.operation_lock = threading.Lock()
        self.model_recommendations = load_model_recommendations(recommendation_path)

    def public_status(self) -> dict[str, Any]:
        with self.lock:
            return {
                "schemaVersion": 1,
                "kind": "haven42-web-status",
                "product": "Haven 42",
                "version": APP_VERSION,
                "runtime": {
                    "platform": platform.system().lower(),
                    "architecture": platform.machine().lower(),
                    "python": platform.python_version(),
                    "bindScope": "loopback-only",
                },
                "provider": {
                    "id": "ollama.local-text",
                    "connected": self.base_url is not None,
                    "trustScope": self.trust_scope,
                    "version": self.ollama_version,
                    "modelCount": len(self.models),
                },
                "privacy": {
                    "configurationPersisted": False,
                    "messagesPersisted": False,
                    "telemetryEnabled": False,
                    "remoteAssetsAllowed": False,
                    "modelResidency": "idle-timeout",
                    "idleUnloadSeconds": self.idle_unload_seconds,
                },
            }

    def connect(self, endpoint: str, timeout_seconds: int, idle_unload_seconds: int) -> dict[str, Any]:
        try:
            policy = validate_local_base_url(endpoint)
        except ProviderSecurityError as error:
            raise WebRequestError(str(error)) from error
        if timeout_seconds < 5 or timeout_seconds > 300:
            raise WebRequestError("invalid-provider-timeout")
        if idle_unload_seconds not in ALLOWED_IDLE_UNLOAD_SECONDS:
            raise WebRequestError("invalid-idle-unload-timeout")
        base_url = policy["baseUrl"]
        with self.operation_lock:
            if not self.unload_active_model():
                raise WebRequestError("previous-model-unload-failed", HTTPStatus.BAD_GATEWAY)
            with self.lock:
                self.base_url = None
                self.trust_scope = None
                self.models = ()
                self.ollama_version = None
            try:
                version = _provider_json(base_url, "/api/version", timeout_seconds)
                tags = _provider_json(base_url, "/api/tags", timeout_seconds)
            except (OSError, ProviderSecurityError) as error:
                raise WebRequestError("ollama-connection-failed", HTTPStatus.BAD_GATEWAY) from error
        records = tags.get("models", [])
        if not isinstance(records, list):
            raise WebRequestError("invalid-ollama-model-list", HTTPStatus.BAD_GATEWAY)
        models = sorted({
            str(item.get("name") or item.get("model", "")).strip()
            for item in records
            if isinstance(item, dict)
            and str(item.get("name") or item.get("model", "")).strip()
            and len(str(item.get("name") or item.get("model", "")).strip()) <= 256
        })
        with self.lock:
            self.base_url = base_url
            self.trust_scope = policy["trustScope"]
            self.timeout_seconds = timeout_seconds
            self.idle_unload_seconds = idle_unload_seconds
            self.models = tuple(models)
            self.ollama_version = str(version.get("version", "unknown"))[:64]
        result = {
            "connected": True,
            "providerId": "ollama.local-text",
            "trustScope": policy["trustScope"],
            "executionLocation": policy["executionLocation"],
            "version": self.ollama_version,
            "models": models,
            "configurationPersisted": False,
            "idleUnloadSeconds": idle_unload_seconds,
        }
        result.update(build_model_decisions(models, self.model_recommendations))
        return result

    def _unload(self, model: str, base_url: str, timeout_seconds: int) -> bool:
        cleanup_timeout = min(timeout_seconds, 15)
        for attempt in range(2):
            try:
                _provider_json(
                    base_url,
                    "/api/generate",
                    cleanup_timeout,
                    {"model": model, "prompt": "", "keep_alive": 0, "stream": False},
                )
                for _ in range(3):
                    processes = _provider_json(base_url, "/api/ps", cleanup_timeout)
                    loaded = {
                        str(item.get("name") or item.get("model", ""))
                        for item in processes.get("models", [])
                        if isinstance(item, dict)
                    }
                    if model not in loaded:
                        return True
                    time.sleep(0.1)
            except (OSError, ProviderSecurityError):
                if attempt == 0:
                    time.sleep(0.1)
        return False

    def _cancel_idle_timer(self) -> None:
        with self.lock:
            timer = self.idle_timer
            self.idle_timer = None
            self.lifecycle_generation += 1
        if timer is not None:
            timer.cancel()

    def _idle_unload(self, target: tuple[str, str, int], generation: int) -> None:
        with self.operation_lock:
            with self.lock:
                if generation != self.lifecycle_generation or self.active_model != target:
                    return
            base_url, model, timeout_seconds = target
            unloaded = self._unload(model, base_url, timeout_seconds)
            with self.lock:
                if unloaded and self.active_model == target:
                    self.active_model = None
                self.idle_timer = None

    def _schedule_idle_unload(self, target: tuple[str, str, int], seconds: float) -> None:
        self._cancel_idle_timer()
        with self.lock:
            generation = self.lifecycle_generation
        timer = threading.Timer(seconds, self._idle_unload, args=(target, generation))
        timer.daemon = True
        with self.lock:
            self.idle_timer = timer
        timer.start()

    def unload_active_model(self) -> bool:
        self._cancel_idle_timer()
        with self.lock:
            target = self.active_model
        if target is None:
            return True
        base_url, model, timeout_seconds = target
        unloaded = self._unload(model, base_url, timeout_seconds)
        with self.lock:
            if unloaded and self.active_model == target:
                self.active_model = None
        return unloaded

    def run_text_capability(
        self,
        capability_id: str,
        model: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        with self.lock:
            base_url = self.base_url
            timeout_seconds = self.timeout_seconds
            allowed_models = self.models
        if base_url is None:
            raise WebRequestError("ollama-not-connected", HTTPStatus.CONFLICT)
        if capability_id not in CAPABILITY_PROMPTS:
            raise WebRequestError("capability-not-admitted")
        if model not in allowed_models:
            raise WebRequestError("model-not-discovered")
        if not messages or len(messages) > MAX_CONVERSATION_MESSAGES:
            raise WebRequestError("invalid-message-count")
        clean_messages: list[dict[str, str]] = []
        total_bytes = 0
        for item in messages:
            if not isinstance(item, dict) or set(item) != {"role", "content"}:
                raise WebRequestError("invalid-message")
            role = item.get("role")
            content = item.get("content")
            if role not in {"user", "assistant"} or not isinstance(content, str) or not content.strip():
                raise WebRequestError("invalid-message")
            encoded_length = len(content.encode("utf-8"))
            if encoded_length > MAX_MESSAGE_BYTES:
                raise WebRequestError("message-too-large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            total_bytes += encoded_length
            clean_messages.append({"role": role, "content": content})
        if total_bytes > MAX_REQUEST_BYTES:
            raise WebRequestError("conversation-too-large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        if clean_messages[-1]["role"] != "user":
            raise WebRequestError("last-message-must-be-user")
        if capability_id != "general.chat" and (
            len(clean_messages) != 1 or clean_messages[0]["role"] != "user"
        ):
            raise WebRequestError("single-input-required")

        with self.operation_lock:
            self._cancel_idle_timer()
            with self.lock:
                previous = self.active_model
                idle_unload_seconds = self.idle_unload_seconds
            target = (base_url, model, timeout_seconds)
            if previous is not None and previous != target:
                previous_base, previous_model, previous_timeout = previous
                if not self._unload(previous_model, previous_base, previous_timeout):
                    raise WebRequestError("previous-model-unload-failed", HTTPStatus.BAD_GATEWAY)
            with self.lock:
                self.used_models.add(target)
                self.active_model = target
            try:
                response = _provider_json(
                base_url,
                "/api/chat",
                timeout_seconds,
                {
                    "model": model,
                    "stream": False,
                    "keep_alive": 0 if idle_unload_seconds == 0 else f"{idle_unload_seconds}s",
                    "options": {"temperature": 0.2},
                    "messages": [
                        {"role": "system", "content": CAPABILITY_PROMPTS[capability_id]},
                        *clean_messages,
                    ],
                },
                maximum_bytes=MAX_CHAT_RESPONSE_BYTES,
                )
            except (OSError, ProviderSecurityError) as error:
                self.unload_active_model()
                raise WebRequestError("ollama-chat-failed", HTTPStatus.BAD_GATEWAY) from error
            content = str((response or {}).get("message", {}).get("content", ""))
            if not content.strip():
                self.unload_active_model()
                raise WebRequestError("empty-model-response", HTTPStatus.BAD_GATEWAY)
            if idle_unload_seconds == 0:
                unloaded = self.unload_active_model()
                residency = "unloaded"
            else:
                unloaded = False
                residency = f"warm-for-{idle_unload_seconds}-seconds"
                self._schedule_idle_unload(target, idle_unload_seconds)
        artifact_kind = "chat-message" if capability_id == "general.chat" else "markdown-document"
        return {
            "schemaVersion": 1,
            "kind": artifact_kind,
            "capabilityId": capability_id,
            "role": "assistant",
            "content": content,
            "title": (
                None
                if capability_id == "general.chat"
                else "Generated Writing"
                if capability_id == "content.write"
                else "Summary"
            ),
            "model": model,
            "providerId": "ollama.local-text",
            "modelUnloaded": unloaded,
            "modelResidency": residency,
            "promptPersisted": False,
            "endpointPersisted": False,
        }

    def unload_used_models(self) -> bool:
        self._cancel_idle_timer()
        with self.lock:
            models = tuple(self.used_models)
        results = [self._unload(model, base_url, timeout) for base_url, model, timeout in models]
        result = all(results)
        with self.lock:
            if result:
                self.active_model = None
        return result


class HavenWebServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, address: tuple[str, int], state: HavenState):
        if address[0] != "127.0.0.1":
            raise ValueError("Haven 42 web MVP must bind to 127.0.0.1.")
        self.state = state
        super().__init__(address, HavenRequestHandler)
        self.expected_origin = f"http://127.0.0.1:{self.server_port}"
        self.expected_host = f"127.0.0.1:{self.server_port}"

    def server_close(self) -> None:
        self.state.unload_used_models()
        super().server_close()


class HavenRequestHandler(BaseHTTPRequestHandler):
    server: HavenWebServer

    def log_message(self, _format: str, *_args: Any) -> None:
        return

    def _security_headers(self, content_type: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        )

    def _valid_host(self) -> bool:
        return self.headers.get("Host", "") == self.server.expected_host

    def _send_json(self, status: HTTPStatus, value: dict[str, Any]) -> None:
        data = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self._security_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error_json(self, error: WebRequestError) -> None:
        self._send_json(error.status, {"error": error.code})

    def _require_local_request(self) -> None:
        if not self._valid_host():
            raise WebRequestError("invalid-host", HTTPStatus.FORBIDDEN)

    def _require_post_authority(self) -> None:
        self._require_local_request()
        if self.headers.get("Origin") != self.server.expected_origin:
            raise WebRequestError("invalid-origin", HTTPStatus.FORBIDDEN)
        if self.headers.get("Sec-Fetch-Site") not in {None, "same-origin"}:
            raise WebRequestError("cross-site-request-rejected", HTTPStatus.FORBIDDEN)
        if not secrets.compare_digest(
            self.headers.get("X-Haven-Token", ""),
            self.server.state.csrf_token,
        ):
            raise WebRequestError("invalid-session-token", HTTPStatus.FORBIDDEN)
        if self.headers.get_content_type() != "application/json":
            raise WebRequestError("json-content-type-required", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

    def _read_body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError as error:
            raise WebRequestError("invalid-content-length") from error
        if length < 1 or length > MAX_REQUEST_BYTES:
            raise WebRequestError("request-too-large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise WebRequestError("invalid-json") from error
        if not isinstance(value, dict):
            raise WebRequestError("json-object-required")
        return value

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._require_local_request()
            if self.path == "/api/bootstrap":
                status = self.server.state.public_status()
                status["sessionToken"] = self.server.state.csrf_token
                self._send_json(HTTPStatus.OK, status)
                return
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/index.html": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/styles.css": ("styles.css", "text/css; charset=utf-8"),
            }
            asset = assets.get(self.path)
            if asset is None:
                raise WebRequestError("not-found", HTTPStatus.NOT_FOUND)
            data = (STATIC_ROOT / asset[0]).read_bytes()
            self.send_response(HTTPStatus.OK)
            self._security_headers(asset[1])
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except WebRequestError as error:
            self._send_error_json(error)

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._require_post_authority()
            body = self._read_body()
            if self.path == "/api/connect":
                if set(body) != {"endpoint", "timeoutSeconds", "idleUnloadSeconds"}:
                    raise WebRequestError("invalid-connect-fields")
                result = self.server.state.connect(
                    str(body["endpoint"]),
                    int(body["timeoutSeconds"]),
                    int(body["idleUnloadSeconds"]),
                )
                self._send_json(HTTPStatus.OK, result)
                return
            if self.path == "/api/unload":
                if body:
                    raise WebRequestError("invalid-unload-fields")
                with self.server.state.operation_lock:
                    unloaded = self.server.state.unload_active_model()
                self._send_json(HTTPStatus.OK, {
                    "modelUnloaded": unloaded,
                    "modelResidency": "unloaded" if unloaded else "cleanup-failed",
                })
                return
            if self.path == "/api/text":
                if (
                    set(body) != {"capabilityId", "model", "messages"}
                    or not isinstance(body["messages"], list)
                ):
                    raise WebRequestError("invalid-text-fields")
                result = self.server.state.run_text_capability(
                    str(body["capabilityId"]),
                    str(body["model"]),
                    body["messages"],
                )
                self._send_json(HTTPStatus.OK, result)
                return
            raise WebRequestError("not-found", HTTPStatus.NOT_FOUND)
        except (TypeError, ValueError) as error:
            if isinstance(error, WebRequestError):
                self._send_error_json(error)
            else:
                self._send_error_json(WebRequestError("invalid-request"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local-only Haven 42 web application.")
    parser.add_argument("--host", default="127.0.0.1", help=argparse.SUPPRESS)
    parser.add_argument("--port", type=int, default=4242)
    parser.add_argument("--no-open", action="store_true", help="Do not open the default browser.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.host != "127.0.0.1":
        print("Haven 42 web application may bind only to 127.0.0.1.", file=sys.stderr)
        return 2
    if args.port < 0 or args.port > 65535:
        print("Port must be from 0 through 65535.", file=sys.stderr)
        return 2
    state = HavenState()
    try:
        server = HavenWebServer((args.host, args.port), state)
    except OSError as error:
        print(f"Could not start Haven 42 local web server: {error}", file=sys.stderr)
        return 1
    url = server.expected_origin
    print(f"Haven 42 is available at {url}")
    print("The server is loopback-only. Configuration and text content are not persisted.")
    if not args.no_open:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\nStopping Haven 42 and unloading models used by this session.")
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
