#!/usr/bin/env python3
"""Offline integration tests for the Haven 42 local-web MVP."""

from __future__ import annotations

import importlib.util
import json
import threading
import time
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("haven42_web_server", ROOT / "web/server.py")
assert SPEC and SPEC.loader
WEB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WEB)


class FakeState:
    models = ["qwen3.5:9b", "writer-model:latest"]
    loaded: set[str] = set()
    requests: list[tuple[str, dict]] = []
    fail_chat = False
    fail_connect = False
    empty_chat = False


class FakeOllama(BaseHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return

    def _json(self, status: int, value: dict):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path == "/api/version":
            if FakeState.fail_connect:
                self._json(503, {"error": "forced-connect-failure"})
            else:
                self._json(200, {"version": "test-1.0"})
        elif self.path == "/api/tags":
            self._json(200, {"models": [{"name": name} for name in FakeState.models]})
        elif self.path == "/api/ps":
            self._json(200, {"models": [{"name": name} for name in sorted(FakeState.loaded)]})
        else:
            self._json(404, {"error": "not-found"})

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeState.requests.append((self.path, body))
        model = str(body.get("model", ""))
        if self.path == "/api/chat":
            FakeState.loaded.add(model)
            if FakeState.fail_chat:
                self._json(500, {"error": "forced-chat-failure"})
            elif FakeState.empty_chat:
                self._json(200, {"message": {"role": "assistant", "content": ""}})
            else:
                self._json(200, {"message": {"role": "assistant", "content": "LOCAL_WEB_OK"}})
        elif self.path == "/api/generate" and body.get("keep_alive") == 0:
            FakeState.loaded.discard(model)
            self._json(200, {"done": True})
        else:
            self._json(404, {"error": "not-found"})


def request_json(
    url: str,
    method: str = "GET",
    body: dict | None = None,
    token: str | None = None,
    origin: str | None = None,
) -> tuple[int, dict, dict]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["X-Haven-Token"] = token
    if origin is not None:
        headers["Origin"] = origin
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read()), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read()), dict(error.headers)


def main() -> int:
    checks = 0
    fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
    fake_thread = threading.Thread(target=fake.serve_forever, daemon=True)
    fake_thread.start()
    state = WEB.HavenState()
    app = WEB.HavenWebServer(("127.0.0.1", 0), state)
    app_thread = threading.Thread(target=app.serve_forever, daemon=True)
    app_thread.start()
    origin = app.expected_origin
    try:
        status, bootstrap, headers = request_json(origin + "/api/bootstrap")
        assert status == 200 and bootstrap["runtime"]["bindScope"] == "loopback-only"
        assert bootstrap["privacy"]["modelResidency"] == "idle-timeout"
        assert bootstrap["privacy"]["idleUnloadSeconds"] == 300
        assert headers["X-Frame-Options"] == "DENY"
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        token = bootstrap["sessionToken"]
        checks += 4

        status, error, _ = request_json(
            origin + "/api/connect",
            "POST",
            {"endpoint": "http://127.0.0.1:11434", "timeoutSeconds": 30, "idleUnloadSeconds": 300},
            token,
        )
        assert status == 403 and error["error"] == "invalid-origin"
        status, error, _ = request_json(
            origin + "/api/connect",
            "POST",
            {"endpoint": "http://127.0.0.1:11434", "timeoutSeconds": 30, "idleUnloadSeconds": 300},
            "wrong-token",
            origin,
        )
        assert status == 403 and error["error"] == "invalid-session-token"
        checks += 2

        for endpoint, expected in (
            ("http://169.254.169.254", "unsafe-provider-address"),
            ("http://example.com", "provider-host-must-be-ip-literal"),
            ("http://user:secret@127.0.0.1", "invalid-provider-url"),
            ("https://8.8.8.8", "trusted-lan-provider-required"),
        ):
            status, error, _ = request_json(
                origin + "/api/connect",
                "POST",
                {"endpoint": endpoint, "timeoutSeconds": 30, "idleUnloadSeconds": 300},
                token,
                origin,
            )
            assert status == 400 and error["error"] == expected
            checks += 1

        fake_url = f"http://127.0.0.1:{fake.server_port}"
        status, connected, _ = request_json(
            origin + "/api/connect",
            "POST",
            {"endpoint": fake_url, "timeoutSeconds": 30, "idleUnloadSeconds": 300},
            token,
            origin,
        )
        assert status == 200
        assert connected["models"] == ["qwen3.5:9b", "writer-model:latest"]
        assert connected["trustScope"] == "loopback" and connected["idleUnloadSeconds"] == 300
        assert connected["configurationPersisted"] is False
        checks += 3

        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "invented:latest",
                "messages": [{"role": "user", "content": "hello"}],
            },
            token,
            origin,
        )
        assert status == 400 and error["error"] == "model-not-discovered"
        checks += 1

        status, reply, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "hello"}],
            },
            token,
            origin,
        )
        assert status == 200 and reply["content"] == "LOCAL_WEB_OK"
        assert reply["capabilityId"] == "general.chat" and reply["kind"] == "chat-message"
        assert reply["modelUnloaded"] is False and FakeState.loaded == {"qwen3.5:9b"}
        chat_payload = next(body for path, body in FakeState.requests if path == "/api/chat")
        assert chat_payload["keep_alive"] == "300s" and chat_payload["stream"] is False
        assert chat_payload["messages"][0]["role"] == "system"
        assert not any(path == "/api/generate" for path, _body in FakeState.requests)
        checks += 6

        for capability_id, expected_title, prompt_fragment in (
            ("content.write", "Generated Writing", "clean Markdown"),
            ("content.summarize", "Summary", "material supplied"),
        ):
            status, reply, _ = request_json(
                origin + "/api/text",
                "POST",
                {
                    "capabilityId": capability_id,
                    "model": "qwen3.5:9b",
                    "messages": [{"role": "user", "content": "bounded source"}],
                },
                token,
                origin,
            )
            assert status == 200 and reply["kind"] == "markdown-document"
            assert reply["capabilityId"] == capability_id and reply["title"] == expected_title
            matching_payload = [body for path, body in FakeState.requests if path == "/api/chat"][-1]
            assert prompt_fragment in matching_payload["messages"][0]["content"]
            assert reply["modelUnloaded"] is False and FakeState.loaded == {"qwen3.5:9b"}
            checks += 4

        status, switched, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "content.write",
                "model": "writer-model:latest",
                "messages": [{"role": "user", "content": "use the writing model"}],
            },
            token,
            origin,
        )
        assert status == 200 and switched["model"] == "writer-model:latest"
        assert FakeState.loaded == {"writer-model:latest"}
        assert any(path == "/api/generate" and body["model"] == "qwen3.5:9b" for path, body in FakeState.requests)
        checks += 3

        status, unloaded, _ = request_json(origin + "/api/unload", "POST", {}, token, origin)
        assert status == 200 and unloaded["modelUnloaded"] is True and not FakeState.loaded
        checks += 2

        status, connected, _ = request_json(
            origin + "/api/connect",
            "POST",
            {"endpoint": fake_url, "timeoutSeconds": 30, "idleUnloadSeconds": 0},
            token,
            origin,
        )
        assert status == 200 and connected["idleUnloadSeconds"] == 0
        status, immediate, _ = request_json(
            origin + "/api/text",
            "POST",
            {"capabilityId": "general.chat", "model": "qwen3.5:9b", "messages": [{"role": "user", "content": "energy saver"}]},
            token,
            origin,
        )
        assert status == 200 and immediate["modelUnloaded"] is True and not FakeState.loaded
        checks += 3

        state.idle_unload_seconds = 0.05
        status, warm, _ = request_json(
            origin + "/api/text",
            "POST",
            {"capabilityId": "general.chat", "model": "qwen3.5:9b", "messages": [{"role": "user", "content": "idle cleanup"}]},
            token,
            origin,
        )
        assert status == 200 and warm["modelUnloaded"] is False
        with state.lock:
            active_target = state.active_model
            stale_generation = state.lifecycle_generation - 1
        assert active_target is not None
        state._idle_unload(active_target, stale_generation)
        assert FakeState.loaded == {"qwen3.5:9b"}
        time.sleep(0.2)
        assert not FakeState.loaded
        checks += 4

        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "media.video.create",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "hello"}],
            },
            token,
            origin,
        )
        assert status == 400 and error["error"] == "capability-not-admitted"
        checks += 1

        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "content.summarize",
                "model": "qwen3.5:9b",
                "messages": [
                    {"role": "user", "content": "one"},
                    {"role": "assistant", "content": "two"},
                    {"role": "user", "content": "three"},
                ],
            },
            token,
            origin,
        )
        assert status == 400 and error["error"] == "single-input-required"
        checks += 1

        FakeState.fail_chat = True
        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "force failure"}],
            },
            token,
            origin,
        )
        assert status == 502 and error["error"] == "ollama-chat-failed"
        assert not FakeState.loaded
        checks += 2

        FakeState.fail_chat = False
        FakeState.empty_chat = True
        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {"capabilityId": "general.chat", "model": "qwen3.5:9b", "messages": [{"role": "user", "content": "empty"}]},
            token,
            origin,
        )
        assert status == 502 and error["error"] == "empty-model-response"
        assert not FakeState.loaded
        checks += 2

        FakeState.empty_chat = False
        FakeState.fail_connect = True
        status, error, _ = request_json(
            origin + "/api/connect",
            "POST",
            {"endpoint": fake_url, "timeoutSeconds": 30, "idleUnloadSeconds": 300},
            token,
            origin,
        )
        assert status == 502 and error["error"] == "ollama-connection-failed"
        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "must stay disconnected"}],
            },
            token,
            origin,
        )
        assert status == 409 and error["error"] == "ollama-not-connected"
        assert state.public_status()["provider"]["connected"] is False
        checks += 3

        try:
            WEB.HavenWebServer(("0.0.0.0", 0), WEB.HavenState())
        except ValueError:
            checks += 1
        else:
            raise AssertionError("non-loopback bind must be rejected")

        policy = json.loads((ROOT / "config/local-web-runtime-policy.json").read_text(encoding="utf-8"))
        assert policy["bind"]["remoteBindAllowed"] is False
        assert policy["providerConnections"]["trustScopeSelection"] == "server-inferred-from-ip-literal"
        assert policy["text"]["modelResidency"] == "bounded-idle-timeout"
        assert policy["text"]["defaultIdleUnloadSeconds"] == 300
        assert policy["text"]["capabilityIds"] == [
            "general.chat", "content.write", "content.summarize"
        ]
        assert policy["browser"]["remoteAssetsAllowed"] is False
        javascript = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
        assert "innerHTML" not in javascript and "X-Haven-Token" in javascript
        assert "/api/text" in javascript and "content.summarize" in javascript
        assert "trust-scope" not in javascript and "modelSelections" in javascript
        checks += 9
    finally:
        app.shutdown()
        app.server_close()
        fake.shutdown()
        fake.server_close()
    print(f"Haven 42 local-web self-test passed: {checks} security and behavior checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
