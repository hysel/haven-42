#!/usr/bin/env python3
"""Offline integration tests for the Haven 42 local-web MVP."""

from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QWEN_DIGEST = "6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7"
WRITER_DIGEST = "1" * 64
SPEC = importlib.util.spec_from_file_location("haven42_web_server", ROOT / "web/server.py")
assert SPEC and SPEC.loader
WEB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WEB)


class FakeState:
    models = ["qwen3.5:9b", "writer-model:latest", "bad model<script>"]
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

    def _bytes(self, status: int, data: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
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
            self._json(200, {"models": [
                {
                    "name": name,
                    "digest": (
                        QWEN_DIGEST
                        if name == "qwen3.5:9b"
                        else WRITER_DIGEST
                        if name == "writer-model:latest"
                        else "invalid"
                    ),
                }
                for name in FakeState.models
            ]})
        elif self.path == "/api/ps":
            self._json(200, {"models": [{"name": name} for name in sorted(FakeState.loaded)]})
        elif self.path == "/object_info/CheckpointLoaderSimple":
            self._json(200, {
                "CheckpointLoaderSimple": {
                    "input": {
                        "required": {
                            "ckpt_name": [[WEB.PROMOTED_IMAGE_MODEL], {}],
                        },
                    },
                },
            })
        elif self.path == "/history/browser-test-image":
            self._json(200, {
                "browser-test-image": {
                    "status": {"status_str": "success"},
                    "outputs": {
                        "9": {
                            "images": [{
                                "filename": "test.png",
                                "subfolder": "haven-42",
                                "type": "output",
                            }],
                        },
                    },
                },
            })
        elif self.path.startswith("/view?"):
            png_header = (
                b"\x89PNG\r\n\x1a\n"
                + b"\x00\x00\x00\rIHDR"
                + struct.pack(">II", 512, 512)
            )
            self._bytes(200, png_header, "image/png")
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
                self._json(200, {
                    "message": {"role": "assistant", "content": "LOCAL_WEB_OK"},
                    "prompt_eval_count": 30,
                    "eval_count": 10,
                    "total_duration": 7_500_000_000,
                    "load_duration": 500_000_000,
                    "prompt_eval_duration": 1_000_000_000,
                    "eval_duration": 5_000_000_000,
                })
        elif self.path == "/api/generate" and body.get("keep_alive") == 0:
            FakeState.loaded.discard(model)
            self._json(200, {"done": True})
        elif self.path == "/prompt":
            self._json(200, {"prompt_id": "browser-test-image"})
        elif self.path == "/history" and body == {"clear": True}:
            self._json(200, {"status": "cleared"})
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


def wait_until(predicate, timeout_seconds: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


def main() -> int:
    checks = 0
    fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeOllama)
    fake_thread = threading.Thread(target=fake.serve_forever, daemon=True)
    fake_thread.start()
    readiness_snapshot = {
        "schemaVersion": 1,
        "kind": "system-readiness",
        "snapshotId": "browser-test-snapshot-0001",
        "platform": {
            "operatingSystem": "windows",
            "architecture": "amd64",
            "logicalProcessors": 16,
            "systemMemoryGiB": 32.0,
            "availableStorageGiB": 512.0,
        },
        "accelerators": [{
            "vendor": "AMD", "model": "Test GPU", "memoryGiB": 16.0,
            "memoryType": "dedicated", "state": "detected",
            "source": "fixture", "confidence": "high",
        }],
        "software": [
            {
                "componentId": "python", "state": "validated", "version": "3.13",
                "source": "fixture", "confidence": "high",
            },
            {
                "componentId": "ollama", "state": "not-detected", "version": None,
                "source": "fixture", "confidence": "high",
            },
        ],
        "installedModels": [],
        "warnings": [],
        "effects": {
            "networkUsed": False, "filesWritten": False, "installationPerformed": False,
            "elevationRequested": False, "servicesChanged": False, "driversChanged": False,
        },
        "privacy": {
            "persisted": False, "rawProbeOutputReturned": False,
            "hostIdentityIncluded": False, "privatePathsIncluded": False,
        },
    }
    state = WEB.HavenState(readiness_provider=lambda: json.loads(json.dumps(readiness_snapshot)))
    app = WEB.HavenWebServer(("127.0.0.1", 0), state)
    app_thread = threading.Thread(target=app.serve_forever, daemon=True)
    app_thread.start()
    origin = app.expected_origin
    try:
        status, bootstrap, headers = request_json(origin + "/api/bootstrap")
        assert status == 200 and bootstrap["runtime"]["bindScope"] == "loopback-only"
        assert bootstrap["privacy"]["modelResidency"] == "idle-timeout"
        assert bootstrap["privacy"]["idleUnloadSeconds"] == 300
        assert bootstrap["updates"] == {
            "mode": "disabled",
            "networkCheckPerformed": False,
            "downloadAllowed": False,
            "activationAllowed": False,
        }
        assert [item["id"] for item in bootstrap["capabilities"]] == [
            "general.chat", "content.write", "content.summarize", "software", "media.image.create"
        ]
        software_status = next(item for item in bootstrap["capabilities"] if item["id"] == "software")
        assert software_status["operationKind"] == "workflow-group"
        assert software_status["operationId"] == "engineering.software-work"
        assert software_status["state"] == "available"
        registry = json.loads((ROOT / "config/capabilities.json").read_text(encoding="utf-8"))
        registered_capabilities = {item["id"] for item in registry["capabilities"]}
        assert all(
            item["operationId"] in registered_capabilities
            for item in bootstrap["capabilities"]
            if item["operationKind"] == "capability"
        )
        assert headers["X-Frame-Options"] == "DENY"
        assert "default-src 'self'" in headers["Content-Security-Policy"]
        token = bootstrap["sessionToken"]
        checks += 6

        status, workflow_catalog, _ = request_json(
            origin + "/api/workflows", "POST", {}, token, origin,
        )
        assert status == 200 and workflow_catalog["kind"] == "workflow-catalog"
        assert workflow_catalog["executionMode"] == "plan-only"
        assert workflow_catalog["arbitraryCommandsAllowed"] is False
        assert workflow_catalog["rendererArgumentsAllowed"] is False
        assert workflow_catalog["workflows"]
        assert all(
            workflow["safetyLevel"] == "read-only"
            and workflow["executionMode"] == "plan-only"
            and workflow["rendererArgumentsAllowed"] is False
            for workflow in workflow_catalog["workflows"]
        )
        workflow_id = workflow_catalog["workflows"][0]["id"]
        status, workflow_plan, _ = request_json(
            origin + "/api/workflow-plan",
            "POST",
            {"workflowId": workflow_id},
            token,
            origin,
        )
        assert status == 200 and workflow_plan["status"] == "planned"
        assert workflow_plan["workflow"]["id"] == workflow_id
        assert workflow_plan["result"] == {
            "invoked": False,
            "dryRun": True,
            "processStarted": False,
            "argumentsAccepted": False,
        }
        assert [event["type"] for event in workflow_plan["events"]] == [
            "accepted", "warning", "result",
        ]
        assert workflow_plan["artifact"]["artifactType"] == "engineering-report"
        assert workflow_plan["artifact"]["policy"]["repositoryRead"] is False
        assert workflow_plan["artifact"]["policy"]["fileWrite"] is False
        status, error, _ = request_json(
            origin + "/api/workflow-plan",
            "POST",
            {"workflowId": "test-pack"},
            token,
            origin,
        )
        assert status == 400 and error["error"] == "workflow-not-admitted"
        assert error["kind"] == "workflow-execution-error"
        assert error["events"][-1]["type"] == "error"
        assert error["recovery"]["automaticRetryAttempted"] is False
        status, error, _ = request_json(
            origin + "/api/workflow-plan",
            "POST",
            {"workflowId": workflow_id, "arguments": ["--apply"]},
            token,
            origin,
        )
        assert status == 400 and error["error"] == "invalid-workflow-plan-fields"
        checks += 14

        fake_url = f"http://127.0.0.1:{fake.server_port}"
        status, image_connection, _ = request_json(
            origin + "/api/image/connect",
            "POST",
            {"endpoint": fake_url, "timeoutSeconds": 300},
            token,
            origin,
        )
        assert status == 200 and image_connection["connected"] is True
        assert image_connection["trustScope"] == "loopback"
        assert image_connection["model"] == WEB.PROMOTED_IMAGE_MODEL
        assert image_connection["customNodesAllowed"] is False
        assert image_connection["externalApiNodesAllowed"] is False
        assert image_connection["providerRetainsOutput"] is True
        status, image_result, _ = request_json(
            origin + "/api/image/run",
            "POST",
            {
                "prompt": "synthetic image prompt",
                "width": 512,
                "height": 512,
                "steps": 10,
                "seed": 424242,
            },
            token,
            origin,
        )
        assert status == 200 and image_result["kind"] == "image"
        assert image_result["promptPersisted"] is False
        assert image_result["endpointPersisted"] is False
        assert image_result["artifact"]["content"]["delivery"] == "browser-memory"
        assert image_result["artifact"]["content"]["width"] == 512
        assert image_result["artifact"]["policy"]["fileWrite"] is False
        assert image_result["artifact"]["policy"]["providerRetainedOutput"] is True
        assert [event["type"] for event in image_result["events"]] == [
            "accepted", "progress", "warning", "result",
        ]
        assert any(
            path == "/history" and body == {"clear": True}
            for path, body in FakeState.requests
        )
        status, error, _ = request_json(
            origin + "/api/image/run",
            "POST",
            {
                "prompt": "escape",
                "width": 512,
                "height": 512,
                "steps": 10,
                "seed": 1,
                "model": "untrusted.safetensors",
            },
            token,
            origin,
        )
        assert status == 400 and error["error"] == "invalid-image-run-fields"
        assert error["kind"] == "image-execution-error"
        assert error["events"][-1]["type"] == "error"
        assert error["recovery"]["automaticRetryAttempted"] is False
        checks += 23

        status, error, _ = request_json(
            origin + "/api/readiness", "POST", {"force": True}, token,
        )
        assert status == 403 and error["error"] == "invalid-origin"
        status, snapshot, _ = request_json(
            origin + "/api/readiness", "POST", {"force": True}, token, origin,
        )
        assert status == 200 and snapshot["snapshotId"] == readiness_snapshot["snapshotId"]
        assert all(value is False for value in snapshot["effects"].values())
        status, cached, _ = request_json(
            origin + "/api/readiness", "POST", {"force": False}, token, origin,
        )
        assert status == 200 and cached["snapshotId"] == snapshot["snapshotId"]
        status, error, _ = request_json(
            origin + "/api/readiness", "POST", {"force": False, "command": "whoami"}, token, origin,
        )
        assert status == 400 and error["error"] == "invalid-readiness-fields"
        status, error, _ = request_json(
            origin + "/api/setup-plan", "POST",
            {"snapshotId": "wrong-snapshot-id", "intent": "guided-setup"}, token, origin,
        )
        assert status == 409 and error["error"] == "readiness-snapshot-mismatch"
        status, plan, _ = request_json(
            origin + "/api/setup-plan", "POST",
            {"snapshotId": snapshot["snapshotId"], "intent": "guided-setup"}, token, origin,
        )
        assert status == 200 and plan["installationAllowed"] is False
        assert all(action["installControl"] == "disabled" for action in plan["actions"])
        assert all(value is False for value in plan["effects"].values())
        status, error, _ = request_json(
            origin + "/api/setup-plan", "POST",
            {"snapshotId": snapshot["snapshotId"], "intent": "guided-setup", "hardware": {"ram": 999}},
            token, origin,
        )
        assert status == 400 and error["error"] == "invalid-setup-plan-fields"
        checks += 9

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
        assert connected["providerHealth"]["status"] == "healthy"
        assert connected["evidenceBoundary"]["immutableDigestBound"] is True
        assert connected["evidenceBoundary"]["unknownModelsGainAuthority"] is False
        assert connected["catalogStatus"] == "ready" and connected["downloadsPerformed"] is False
        assert connected["recommendations"]["general.chat"] == {
            "status": "recommended",
            "model": "qwen3.5:9b",
            "evidenceId": "general-chat-qwen35-9b-ollama",
            "digestVerified": True,
            "hardwareFit": "unknown",
            "automatic": True,
        }
        writer_option = next(item for item in connected["modelOptions"] if item["name"] == "writer-model:latest")
        assert set(writer_option["capabilityStatus"].values()) == {"unverified"}
        checks += 9

        cross_capability = WEB.build_model_decisions(
            ["chat-only:1b"],
            {
                "general.chat": ({
                    "model": "chat-only:1b",
                    "digest": "2" * 64,
                    "priority": 1,
                    "evidenceId": "chat",
                },),
                "content.write": (),
                "content.summarize": (),
            },
            {"chat-only:1b": "2" * 64},
        )
        assert cross_capability["modelOptions"][0]["capabilityStatus"] == {
            "general.chat": "recommended",
            "content.write": "compatible",
            "content.summarize": "compatible",
        }
        unavailable_catalog = WEB.HavenState(ROOT / "config/does-not-exist.json")
        unavailable_decisions = WEB.build_model_decisions(
            ["unknown:latest"],
            unavailable_catalog.model_recommendations,
        )
        assert unavailable_decisions["catalogStatus"] == "unavailable"
        assert unavailable_decisions["recommendations"]["general.chat"]["status"] == "missing"
        assert unavailable_decisions["modelOptions"][0]["capabilityStatus"]["general.chat"] == "unverified"
        assert WEB.load_model_recommendations(
            ROOT / "config/text-capability-model-recommendations.json",
            ROOT / "config/does-not-exist.tsv",
        ) == {}
        valid_catalog = json.loads(
            (ROOT / "config/text-capability-model-recommendations.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory() as temp_root:
            hostile_path = Path(temp_root) / "catalog.json"
            duplicate = json.loads(json.dumps(valid_catalog))
            duplicate["capabilities"]["general.chat"].append(
                json.loads(json.dumps(duplicate["capabilities"]["general.chat"][0]))
            )
            hostile_path.write_text(json.dumps(duplicate), encoding="utf-8")
            assert WEB.load_model_recommendations(hostile_path) == {}
            forged = json.loads(json.dumps(valid_catalog))
            forged["capabilities"]["content.write"][0]["evidenceOperation"] = "general-chat"
            hostile_path.write_text(json.dumps(forged), encoding="utf-8")
            assert WEB.load_model_recommendations(hostile_path) == {}
            unexpected = json.loads(json.dumps(valid_catalog))
            unexpected["rendererMayPromote"] = True
            hostile_path.write_text(json.dumps(unexpected), encoding="utf-8")
            assert WEB.load_model_recommendations(hostile_path) == {}
        checks += 8

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
        assert [event["type"] for event in error["events"]] == ["error"]
        assert error["recovery"]["retryAllowed"] is False
        assert error["recovery"]["automaticRetryAttempted"] is False
        checks += 4

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
        assert reply["artifact"]["artifactType"] == "chat-message"
        assert reply["artifact"]["sourceCapabilityId"] == "general.chat"
        assert reply["artifact"]["policy"]["fileWrite"] is False
        assert reply["artifact"]["policy"]["networkAccess"] is False
        assert reply["modelDigestVerified"] is True
        assert reply["runDetails"] == {
            "providerReported": True,
            "inputTokens": 30,
            "outputTokens": 10,
            "totalTokens": 40,
            "tokensPerSecond": 2.0,
            "totalDurationMs": 7500.0,
            "loadDurationMs": 500.0,
            "promptDurationMs": 1000.0,
            "generationDurationMs": 5000.0,
        }
        assert [event["type"] for event in reply["events"]] == ["accepted", "progress", "result"]
        assert [event["sequence"] for event in reply["events"]] == [1, 2, 3]
        chat_payload = next(body for path, body in FakeState.requests if path == "/api/chat")
        assert chat_payload["keep_alive"] == "300s" and chat_payload["stream"] is False
        assert chat_payload["think"] is False
        assert chat_payload["messages"][0]["role"] == "system"
        assert not any(path == "/api/generate" for path, _body in FakeState.requests)
        checks += 11

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
        assert [event["type"] for event in switched["events"]] == [
            "accepted", "progress", "warning", "result"
        ]
        assert switched["events"][2]["code"] == "MODEL_SELECTION_UNVERIFIED_FOR_CAPABILITY"
        checks += 5

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
        assert wait_until(lambda: not FakeState.loaded), "idle cleanup did not finish within two seconds"
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
        assert error["kind"] == "text-execution-error" and error["status"] == "failed"
        assert [event["type"] for event in error["events"]] == ["accepted", "error"]
        assert error["recovery"] == {
            "automaticRetryAttempted": False,
            "retryAllowed": True,
            "retryRequiresNewRequest": True,
            "inputMayBeRestored": True,
        }
        assert not FakeState.loaded
        checks += 5

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
        assert error["events"][-1]["type"] == "error"
        assert error["recovery"]["retryAllowed"] is True
        assert not FakeState.loaded
        checks += 4

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

        FakeState.fail_connect = False
        FakeState.models = []
        status, no_models, _ = request_json(
            origin + "/api/connect",
            "POST",
            {"endpoint": fake_url, "timeoutSeconds": 30, "idleUnloadSeconds": 300},
            token,
            origin,
        )
        assert status == 200 and no_models["models"] == [] and no_models["modelOptions"] == []
        assert all(
            decision["status"] == "missing" and decision["automatic"] is False
            for decision in no_models["recommendations"].values()
        )
        assert no_models["downloadsPerformed"] is False
        FakeState.models = ["qwen3.5:9b", "writer-model:latest"]
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
        assert policy["text"]["automaticUnknownModelSelectionAllowed"] is False
        assert policy["text"]["missingModelDownloadsAllowed"] is False
        assert policy["executionEvents"]["automaticRetryAllowed"] is False
        assert policy["executionEvents"]["retryRequiresNewRequest"] is True
        assert policy["executionEvents"]["failedInputPersistenceAllowed"] is False
        assert policy["executionEvents"]["unverifiedModelWarningRequired"] is True
        assert policy["browser"]["remoteAssetsAllowed"] is False
        javascript = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
        html = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
        styles = (ROOT / "web/static/styles.css").read_text(encoding="utf-8")
        assert "innerHTML" not in javascript and "X-Haven-Token" in javascript
        assert "/api/text" in javascript and "content.summarize" in javascript
        assert "trust-scope" not in javascript and "modelSelections" in javascript
        assert "Automatic — no validated model installed" in javascript
        assert "Advanced manual selection" in javascript and "downloadsPerformed" not in javascript
        assert "renderTypedResult" in javascript and "renderCapabilities" in javascript
        assert "validateExecutionEvents" in javascript and "event-after-terminal" in javascript
        assert "validateRecovery" in javascript and "invalid-recovery-envelope" in javascript
        assert "missing-accepted-event" in javascript
        assert "retry creates a new request" in javascript
        assert "event.dataset.kind = kind" in javascript
        assert "innerHTML" not in javascript and "insertAdjacentHTML" not in javascript
        assert html.count('id="connection-panel"') == 1 and html.count('id="status-panel"') == 1
        assert html.count('id="setup-wizard"') == 1 and 'id="wizard-connection-form"' in html
        assert all(
            marker in html
            for marker in ('id="wizard-guided"', 'id="wizard-existing"', 'id="wizard-explore"')
        )
        assert 'class="skip-link"' in html and 'aria-modal="true"' in html
        assert 'id="capability-panel"' in html and 'id="evidence-panel"' in html
        assert html.index('id="text-panel"') < html.index('id="connection-panel"')
        assert 'class="interaction-grid"' in html and 'class="configuration-column"' in html
        assert ".rail {" in styles and ".configuration-column {" in styles and "position: sticky" in styles and "4.5rem" not in styles and "2.25rem" in styles
        assert ".wizard-backdrop {" in styles and ".wizard-readiness {" in styles
        assert ".wizard-choices {" in styles and ".readiness-dashboard" in styles
        checks += 33
    finally:
        app.shutdown()
        app.server_close()
        fake.shutdown()
        fake.server_close()
    print(f"Haven 42 local-web self-test passed: {checks} security and behavior checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
