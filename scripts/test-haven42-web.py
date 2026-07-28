#!/usr/bin/env python3
"""Offline integration tests for the Haven 42 local-web MVP."""

from __future__ import annotations

import base64
import importlib.util
import json
import struct
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib
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
    safe_url = "http://127.0.0.1:4242"
    assert WEB._validated_browser_url(safe_url)
    checks += 1
    assert all(
        not WEB._validated_browser_url(candidate)
        for candidate in (
            "https://127.0.0.1:4242",
            "http://localhost:4242",
            "http://127.0.0.1:4242/path",
            "http://127.0.0.1:4242?query=1",
            "http://user@127.0.0.1:4242",
            "http://127.0.0.1:0",
        )
    )
    checks += 1
    safe_environment = WEB._browser_environment({
        "BROWSER": "hostile-browser-command",
        "LD_PRELOAD": "/tmp/hostile.so",
        "PYTHONPATH": "/tmp/hostile-python",
        "HOME": "/home/tester",
        "DISPLAY": ":0",
        "PATH": "/tmp/hostile-bin",
    })
    assert safe_environment == {
        "HOME": "/home/tester",
        "DISPLAY": ":0",
        "PATH": "/usr/bin:/bin",
    }
    checks += 1

    windows_urls: list[str] = []
    assert WEB.open_default_browser(
        safe_url,
        platform_name="win32",
        windows_launcher=windows_urls.append,
    )
    assert windows_urls == [safe_url]
    checks += 1

    launches: list[tuple[list[str], dict]] = []

    def record_launch(command, **kwargs):
        launches.append((command, kwargs))

    assert WEB.open_default_browser(
        safe_url,
        platform_name="darwin",
        executable_exists=lambda path: path == "/usr/bin/open",
        process_launcher=record_launch,
        environment={"BROWSER": "hostile", "HOME": "/Users/tester"},
    )
    assert launches[-1][0] == ["/usr/bin/open", safe_url]
    checks += 1
    assert (
        launches[-1][1]["shell"] is False
        and launches[-1][1]["close_fds"] is True
        and launches[-1][1]["start_new_session"] is True
        and "BROWSER" not in launches[-1][1]["env"]
    )
    checks += 1

    launches.clear()
    assert WEB.open_default_browser(
        safe_url,
        platform_name="linux",
        executable_exists=lambda path: path in {"/usr/bin/gio", "/usr/bin/xdg-open"},
        process_launcher=record_launch,
        environment={"BROWSER": "hostile", "DISPLAY": ":1"},
    )
    assert launches[-1][0] == ["/usr/bin/gio", "open", safe_url]
    checks += 1
    launches.clear()
    assert WEB.open_default_browser(
        safe_url,
        platform_name="linux",
        executable_exists=lambda path: path == "/usr/bin/xdg-open",
        process_launcher=record_launch,
    )
    assert launches[-1][0] == ["/usr/bin/xdg-open", safe_url]
    checks += 1
    launches.clear()
    assert not WEB.open_default_browser(
        safe_url,
        platform_name="linux",
        executable_exists=lambda _path: False,
        process_launcher=record_launch,
    )
    assert launches == []
    checks += 1

    def fail_launch(_command, **_kwargs):
        raise OSError("forced-launch-failure")

    assert not WEB.open_default_browser(
        safe_url,
        platform_name="linux",
        executable_exists=lambda _path: True,
        process_launcher=fail_launch,
    )
    checks += 1
    assert not WEB.open_default_browser(safe_url, platform_name="unsupported")
    checks += 1

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
    state = WEB.HavenState(
        readiness_provider=lambda: json.loads(json.dumps(readiness_snapshot)),
        model_catalog_provider=lambda query: [
            "qwen3.5",
            "community/example-writing:7b",
            "unsafe model<script>",
            "qwen3.5",
        ] if query == "writing" else [],
    )
    invalid_assurance_state = WEB.HavenState(
        assurance_provider=lambda: {
            "kind": "read-only-assurance-summary",
            "status": "ready",
            "effects": {
                "networkAccess": True,
                "processCreation": False,
                "filesystemWrite": False,
                "repositoryRead": False,
                "providerInvocation": False,
                "machineModification": False,
            },
        },
    )
    try:
        invalid_assurance_state.assurance_summary()
        raise AssertionError("unsafe assurance effects were accepted")
    except WEB.WebRequestError as error:
        assert error.code == "assurance-evidence-invalid"
        assert error.status == HTTPStatus.SERVICE_UNAVAILABLE
    unavailable_assurance_state = WEB.HavenState(
        assurance_provider=lambda: (_ for _ in ()).throw(
            WEB.EvidenceDashboardError("unavailable")
        ),
    )
    try:
        unavailable_assurance_state.assurance_summary()
        raise AssertionError("unavailable assurance evidence was accepted")
    except WEB.WebRequestError as error:
        assert error.code == "assurance-evidence-unavailable"
        assert error.status == HTTPStatus.SERVICE_UNAVAILABLE
    checks += 2
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

        status, assurance, _ = request_json(
            origin + "/api/assurance", "POST", {}, token, origin,
        )
        assert status == 200 and assurance["kind"] == "read-only-assurance-summary"
        assert assurance["status"] == "ready"
        assert assurance["sources"] == {
            "evidenceCatalog": "config/evidence-catalog.tsv",
            "surfaceMatrix": "config/agent-surface-capabilities.json",
            "surfaceSolutions": "config/agent-surface-solutions.json",
        }
        assert assurance["evidence"]["recordCount"] >= 1
        assert assurance["evidence"]["modelCount"] >= 1
        assert len(assurance["surfaces"]) == 4
        assert all(value is False for value in assurance["effects"].values())
        assert all(
            set(surface) == {
                "id", "name", "supportTier", "validationLevel",
                "supportedActivities", "validatedActivities", "blockedActivities",
                "installStatus", "configureStatus", "testStatus",
            }
            for surface in assurance["surfaces"]
        )
        serialized_assurance = json.dumps(assurance)
        assert '"notes"' not in serialized_assurance and str(ROOT) not in serialized_assurance
        status, error, _ = request_json(
            origin + "/api/assurance", "POST", {"force": True}, token, origin,
        )
        assert status == 400 and error["error"] == "invalid-assurance-fields"
        checks += 11

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
        assert connected["transportScheme"] == "http"
        assert connected["transportEncrypted"] is False
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

        status, error, _ = request_json(
            origin + "/api/model-search", "POST",
            {"query": "writing", "online": False}, token, origin,
        )
        assert status == 400 and error["error"] == "explicit-online-search-consent-required"
        status, error, _ = request_json(
            origin + "/api/model-search", "POST",
            {"query": "bad?<script>", "online": True}, token, origin,
        )
        assert status == 400 and error["error"] == "invalid-model-search-query"
        status, discovery, _ = request_json(
            origin + "/api/model-search", "POST",
            {"query": "writing", "online": True}, token, origin,
        )
        assert status == 200 and discovery["query"] == "writing"
        assert discovery["downloadsPerformed"] is False
        assert discovery["configurationChanged"] is False
        assert discovery["repositoryContentSent"] is False
        assert discovery["results"] == [
            {
                "name": "qwen3.5",
                "source": "ollama-public-catalog",
                "status": "not-installed",
                "validationStatus": "candidate-only",
                "capabilityEvidence": "unverified",
                "hardwareFit": "unknown",
                "licenseStatus": "review-required",
                "executionAllowed": False,
                "installCommand": "ollama pull qwen3.5",
            },
            {
                "name": "community/example-writing:7b",
                "source": "ollama-public-catalog",
                "status": "not-installed",
                "validationStatus": "candidate-only",
                "capabilityEvidence": "unverified",
                "hardwareFit": "unknown",
                "licenseStatus": "review-required",
                "executionAllowed": False,
                "installCommand": "ollama pull community/example-writing:7b",
            },
        ]
        fixture_html = (ROOT / "examples/fixtures/ollama-model-library.html").read_text(encoding="utf-8")
        search_globals = WEB.search_ollama_catalog.__globals__
        parsed = search_globals["parse_ollama_search_html"](fixture_html)
        assert parsed == ["qwen3.5:9b", "qwen3.5:35b", "qwen3.5:9b-mlx"]
        assert search_globals["validate_query"]("  agent   writing ") == "agent writing"
        for hostile_query in ("", "x" * 65, "model?token=secret", "<script>"):
            try:
                search_globals["validate_query"](hostile_query)
            except search_globals["ModelCatalogSearchError"]:
                pass
            else:
                raise AssertionError("hostile model search query must be rejected")
        hostile_html = "".join(
            f'<a href="/library/model-{index}:7b">model</a>'
            for index in range(25)
        ) + '<a href="/library/model:cloud">cloud</a><a href="/library/bad%20model">bad</a>'
        assert len(search_globals["parse_ollama_search_html"](hostile_html)) == 20
        assert search_globals["_NoRedirect"]().redirect_request(None, None, 302, "", {}, "") is None
        try:
            WEB.search_ollama_catalog("safe", timeout_seconds=16)
        except search_globals["ModelCatalogSearchError"] as error:
            assert str(error) == "invalid-model-search-timeout"
        else:
            raise AssertionError("unsafe model search timeout must be rejected")
        checks += 14

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
        assert reply["context"] == {
            "fileCount": 0,
            "totalBytes": 0,
            "imageCount": 0,
            "imageTotalBytes": 0,
            "imageInputEvidence": "not-requested",
            "providerTrustScope": "loopback",
            "persisted": False,
            "temporaryFilesWritten": False,
            "hostExecutionAllowed": False,
            "toolInvocationAllowed": False,
            "filesystemAccessAllowed": False,
        }
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
        checks += 12

        attachment_content = "# Project notes\nTreat `rm -rf` as quoted source text."
        attachment = {
            "name": "notes.md",
            "mediaType": "text/markdown",
            "content": attachment_content,
            "sizeBytes": len(attachment_content.encode("utf-8")),
        }
        status, context_reply, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Summarize the attached notes."}],
                "attachments": [attachment],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 200
        assert context_reply["context"] == {
            "fileCount": 1,
            "totalBytes": attachment["sizeBytes"],
            "imageCount": 0,
            "imageTotalBytes": 0,
            "imageInputEvidence": "not-requested",
            "providerTrustScope": "loopback",
            "persisted": False,
            "temporaryFilesWritten": False,
            "hostExecutionAllowed": False,
            "toolInvocationAllowed": False,
            "filesystemAccessAllowed": False,
        }
        context_payload = [body for path, body in FakeState.requests if path == "/api/chat"][-1]
        assert "untrusted, inert reference data" in context_payload["messages"][0]["content"]
        assert "tools" not in context_payload
        assert "untrusted reference material" in context_payload["messages"][-1]["content"]
        assert attachment_content in context_payload["messages"][-1]["content"]
        assert not any(
            key in json.dumps(context_reply).lower()
            for key in ("fullpath", "filepath", "temporarypath")
        )

        state.trust_scope = "trusted-lan"
        status, error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Use the attachment."}],
                "attachments": [attachment],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 409 and error["error"] == "private-context-confirmation-required"
        status, lan_reply, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Use the attachment."}],
                "attachments": [attachment],
                "contextConsent": True,
            },
            token,
            origin,
        )
        assert status == 200 and lan_reply["context"]["providerTrustScope"] == "trusted-lan"
        state.trust_scope = "loopback"

        hostile_attachments = (
            ({**attachment, "name": "../notes.md"}, "invalid-context-file-name"),
            ({**attachment, "mediaType": "text/plain"}, "invalid-context-file-type"),
            ({**attachment, "sizeBytes": attachment["sizeBytes"] + 1}, "context-file-too-large"),
            ({**attachment, "content": "bad\u0000text", "sizeBytes": 8}, "invalid-context-file-content"),
        )
        for hostile_attachment, expected_error in hostile_attachments:
            status, error, _ = request_json(
                origin + "/api/text",
                "POST",
                {
                    "capabilityId": "general.chat",
                    "model": "qwen3.5:9b",
                    "messages": [{"role": "user", "content": "Use this."}],
                    "attachments": [hostile_attachment],
                    "contextConsent": False,
                },
                token,
                origin,
            )
            assert status in {400, 413} and error["error"] == expected_error
        status, duplicate_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Use these."}],
                "attachments": [attachment, {**attachment, "name": "NOTES.MD"}],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 400 and duplicate_error["error"] == "duplicate-context-file-name"
        status, count_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Use these."}],
                "attachments": [
                    {**attachment, "name": f"notes-{index}.md"}
                    for index in range(WEB.MAX_CONTEXT_FILES + 1)
                ],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 400 and count_error["error"] == "invalid-context-file-count"
        oversized_attachment = {
            "name": "large.txt",
            "mediaType": "text/plain",
            "content": "x" * (WEB.MAX_CONTEXT_FILE_BYTES + 1),
            "sizeBytes": WEB.MAX_CONTEXT_FILE_BYTES + 1,
        }
        status, size_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Use this."}],
                "attachments": [oversized_attachment],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 413 and size_error["error"] == "context-file-too-large"
        total_attachments = [
            {
                "name": f"large-{index}.txt",
                "mediaType": "text/plain",
                "content": "x" * size,
                "sizeBytes": size,
            }
            for index, size in enumerate((65536, 65536, 1))
        ]
        status, total_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Use these."}],
                "attachments": total_attachments,
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 413 and total_error["error"] == "context-total-too-large"
        structured_attachments = [
            {
                "name": "records.csv",
                "mediaType": "text/csv",
                "content": 'name,note\nalpha,"quoted, inert formula =CMD()"\n',
                "sizeBytes": len(
                    'name,note\nalpha,"quoted, inert formula =CMD()"\n'.encode("utf-8")
                ),
            },
            {
                "name": "settings.json",
                "mediaType": "application/json",
                "content": '{"enabled":false,"instruction":"rm -rf is inert text"}',
                "sizeBytes": len(
                    '{"enabled":false,"instruction":"rm -rf is inert text"}'.encode("utf-8")
                ),
            },
        ]
        status, structured_reply, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Describe these records."}],
                "attachments": structured_attachments,
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 200 and structured_reply["context"]["fileCount"] == 2
        structured_payload = [body for path, body in FakeState.requests if path == "/api/chat"][-1]
        assert 'media-type="text/csv"' in structured_payload["messages"][-1]["content"]
        assert 'media-type="application/json"' in structured_payload["messages"][-1]["content"]
        for hostile_structured, expected_error in (
            (
                {
                    "name": "broken.json",
                    "mediaType": "application/json",
                    "content": '{"open":',
                    "sizeBytes": 8,
                },
                "invalid-context-json",
            ),
            (
                {
                    "name": "broken.csv",
                    "mediaType": "text/csv",
                    "content": 'header\n"unterminated',
                    "sizeBytes": 20,
                },
                "invalid-context-csv",
            ),
        ):
            status, error, _ = request_json(
                origin + "/api/text",
                "POST",
                {
                    "capabilityId": "general.chat",
                    "model": "qwen3.5:9b",
                    "messages": [{"role": "user", "content": "Use this."}],
                    "attachments": [hostile_structured],
                    "contextConsent": False,
                },
                token,
                origin,
            )
            assert status == 400 and error["error"] == expected_error
        checks += 22

        png_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        png_bytes = base64.b64decode(png_base64)
        screenshot = {
            "name": "clipboard-screenshot-1.png",
            "mediaType": "image/png",
            "base64": png_base64,
            "sizeBytes": len(png_bytes),
            "width": 1,
            "height": 1,
        }
        status, screenshot_reply, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Describe the screenshot."}],
                "attachments": [],
                "images": [screenshot],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 200
        assert screenshot_reply["context"] == {
            "fileCount": 0,
            "totalBytes": 0,
            "imageCount": 1,
            "imageTotalBytes": len(png_bytes),
            "imageInputEvidence": "unverified",
            "providerTrustScope": "loopback",
            "persisted": False,
            "temporaryFilesWritten": False,
            "hostExecutionAllowed": False,
            "toolInvocationAllowed": False,
            "filesystemAccessAllowed": False,
        }
        screenshot_payload = [body for path, body in FakeState.requests if path == "/api/chat"][-1]
        assert screenshot_payload["messages"][-1]["images"] == [png_base64]
        assert screenshot_reply["events"][-2]["code"] == "MODEL_IMAGE_INPUT_UNVERIFIED"
        screenshot_hostiles = (
            ({**screenshot, "base64": "***"}, "invalid-context-image"),
            ({**screenshot, "sizeBytes": len(png_bytes) + 1}, "context-image-too-large"),
            ({**screenshot, "width": 2}, "invalid-context-image-dimensions"),
            ({**screenshot, "mediaType": "image/jpeg"}, "invalid-context-image-type"),
            ({**screenshot, "name": "../screen.png"}, "invalid-context-image-name"),
        )
        for hostile_image, expected_error in screenshot_hostiles:
            status, error, _ = request_json(
                origin + "/api/text",
                "POST",
                {
                    "capabilityId": "general.chat",
                    "model": "qwen3.5:9b",
                    "messages": [{"role": "user", "content": "Describe this."}],
                    "attachments": [],
                    "images": [hostile_image],
                    "contextConsent": False,
                },
                token,
                origin,
            )
            assert status in {400, 413} and error["error"] == expected_error
        oversized_dimensions = bytearray(png_bytes)
        struct.pack_into(">I", oversized_dimensions, 16, WEB.MAX_CONTEXT_IMAGE_DIMENSION + 1)
        struct.pack_into(
            ">I",
            oversized_dimensions,
            29,
            zlib.crc32(oversized_dimensions[12:29]) & 0xFFFFFFFF,
        )
        status, dimension_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Describe this."}],
                "attachments": [],
                "images": [{
                    **screenshot,
                    "base64": base64.b64encode(oversized_dimensions).decode("ascii"),
                    "width": WEB.MAX_CONTEXT_IMAGE_DIMENSION + 1,
                }],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 400 and dimension_error["error"] == "context-image-dimensions-too-large"
        status, image_duplicate_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Describe these."}],
                "attachments": [],
                "images": [screenshot, {**screenshot, "name": "CLIPBOARD-SCREENSHOT-1.PNG"}],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 400 and image_duplicate_error["error"] == "duplicate-context-image-name"
        status, image_count_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Describe these."}],
                "attachments": [],
                "images": [
                    {**screenshot, "name": f"clipboard-screenshot-{index}.png"}
                    for index in range(WEB.MAX_CONTEXT_IMAGES + 1)
                ],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 400 and image_count_error["error"] == "invalid-context-image-count"
        state.trust_scope = "trusted-lan"
        status, image_consent_error, _ = request_json(
            origin + "/api/text",
            "POST",
            {
                "capabilityId": "general.chat",
                "model": "qwen3.5:9b",
                "messages": [{"role": "user", "content": "Describe this."}],
                "attachments": [],
                "images": [screenshot],
                "contextConsent": False,
            },
            token,
            origin,
        )
        assert status == 409 and image_consent_error["error"] == "private-context-confirmation-required"
        state.trust_scope = "loopback"
        checks += 14

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

        status, continued_summary, _ = request_json(
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
        assert status == 200
        assert continued_summary["capabilityId"] == "content.summarize"
        assert continued_summary["kind"] == "markdown-document"
        summary_payload = next(
            payload for path, payload in reversed(FakeState.requests)
            if path == "/api/chat" and payload["messages"][-1]["content"] == "three"
        )
        assert [message["role"] for message in summary_payload["messages"][1:]] == [
            "user", "assistant", "user"
        ]
        checks += 4

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
        assert policy["text"]["maximumRequestBytes"] == 12582912
        assert policy["text"]["maximumConversationBytes"] == 65536
        assert policy["documentContext"]["contract"] == "config/document-context-policy.json"
        assert policy["documentContext"]["allowedExtensions"] == [
            ".txt", ".md", ".csv", ".json"
        ]
        assert policy["documentContext"]["structuredTextSyntaxValidationRequired"] is True
        assert policy["documentContext"]["structuredTextFormulaEvaluationAllowed"] is False
        assert policy["documentContext"]["maximumFiles"] == 5
        assert policy["documentContext"]["maximumTotalBytes"] == 131072
        assert policy["documentContext"]["clipboardScreenshotMediaTypes"] == ["image/png"]
        assert policy["documentContext"]["maximumScreenshots"] == 2
        assert policy["documentContext"]["maximumBytesPerScreenshot"] == 4194304
        assert policy["documentContext"]["maximumScreenshotDimension"] == 4096
        assert policy["documentContext"]["imageInputEvidence"] == "unverified-visible-warning"
        assert policy["documentContext"]["screenshotFilePickerAllowed"] is True
        assert policy["documentContext"]["memoryOnly"] is True
        assert policy["documentContext"]["privateNetworkConfirmationRequired"] is True
        assert policy["documentContext"]["privateNetworkWarningRequired"] is True
        assert policy["documentContext"]["privateNetworkConfirmationMechanism"] == (
            "deliberate-submit-after-visible-warning"
        )
        assert policy["documentContext"]["separateConfirmationControlRequired"] is False
        context_policy = json.loads(
            (ROOT / "config/document-context-policy.json").read_text(encoding="utf-8")
        )
        assert context_policy["selection"]["backgroundScanningAllowed"] is False
        assert context_policy["selection"]["arbitraryPathInputAllowed"] is False
        assert context_policy["lifecycle"]["temporaryFilesAllowed"] is False
        assert context_policy["lifecycle"]["clearOnFailure"] is True
        assert context_policy["formats"]["clipboardImages"]["clipboardPasteAllowed"] is True
        assert context_policy["formats"]["clipboardImages"]["filePickerAllowed"] is True
        assert context_policy["formats"]["allowedExtensions"] == [
            ".txt", ".md", ".csv", ".json"
        ]
        assert context_policy["formats"]["structuredText"]["formulaEvaluationAllowed"] is False
        assert context_policy["budgets"]["maximumImagePixels"] == 16777216
        assert context_policy["executionIsolation"] == {
            "attachmentContentTreatedAsData": True,
            "executableFormatsAllowed": False,
            "archiveExpansionAllowed": False,
            "contentDrivenProcessLaunchAllowed": False,
            "contentDrivenToolInvocationAllowed": False,
            "contentDrivenFilesystemAccessAllowed": False,
            "modelOutputExecutionAllowed": False,
            "antivirusScanningClaimed": False,
        }
        assert context_policy["providerDisclosure"]["confirmationMechanism"] == (
            "deliberate-submit-after-visible-warning"
        )
        assert context_policy["providerDisclosure"]["separateConfirmationControlRequired"] is False
        assert context_policy["retrieval"]["persistentIndexAllowed"] is False
        lexical_contract = json.loads(
            (ROOT / "config/lexical-retrieval-contract.json").read_text(encoding="utf-8")
        )
        assert lexical_contract["status"] == "offline-engine-implemented-not-runtime-admitted"
        assert not any(lexical_contract["activation"].values())
        assert lexical_contract["inputBoundary"]["validatedMemoryAttachmentsOnly"] is True
        assert lexical_contract["inputBoundary"]["filesystemPathsAllowed"] is False
        assert lexical_contract["determinism"]["semanticEmbeddingsAllowed"] is False
        assert lexical_contract["resultBoundary"]["contentAuthorityAllowed"] is False
        assert lexical_contract["lifecycle"]["persistentIndexAllowed"] is False
        lexical_fixtures = json.loads(
            (ROOT / lexical_contract["hostileFixture"]).read_text(encoding="utf-8")
        )
        assert lexical_fixtures["effectsAllowed"] is False
        assert len({case["id"] for case in lexical_fixtures["cases"]}) == 10
        assert all(case["expected"] in {"rejected", "inert-data", "memory-cleared"} for case in lexical_fixtures["cases"])
        research_contract = json.loads(
            (ROOT / "config/web-research-contract.json").read_text(encoding="utf-8")
        )
        assert research_contract["status"] == "proposed-offline-fixtures-only"
        assert not any(research_contract["activation"].values())
        assert research_contract["query"]["explicitUserActionRequired"] is True
        assert research_contract["query"]["repositoryContentAllowed"] is False
        assert research_contract["futureBrokerBoundary"]["privateNetworkDestinationsAllowed"] is False
        assert research_contract["citations"]["modelSuppliedActiveLinksAllowed"] is False
        assert research_contract["lifecycle"]["persistenceAllowed"] is False
        research_fixtures = json.loads(
            (ROOT / research_contract["hostileFixture"]).read_text(encoding="utf-8")
        )
        assert research_fixtures["networkUsed"] is False
        assert len({case["id"] for case in research_fixtures["cases"]}) == 10
        assert all(case["expected"] in {"rejected", "inert-rejected", "inert-data", "inactive-rejected", "cleaned"} for case in research_fixtures["cases"])
        assert policy["inactiveFoundations"]["lexicalRetrieval"]["runtimeRouteAllowed"] is False
        assert policy["inactiveFoundations"]["webResearch"]["networkAllowed"] is False
        assert policy["modelDiscovery"]["automaticDownloadsAllowed"] is False
        assert policy["modelDiscovery"]["explicitOnlineConsentRequired"] is True
        assert policy["executionEvents"]["automaticRetryAllowed"] is False
        assert policy["executionEvents"]["retryRequiresNewRequest"] is True
        assert policy["executionEvents"]["failedInputPersistenceAllowed"] is False
        assert policy["executionEvents"]["unverifiedModelWarningRequired"] is True
        assert policy["browser"]["remoteAssetsAllowed"] is False
        assert policy["browser"]["fixedExternalNavigationUrls"] == [
            "https://github.com/hysel/haven-42/wiki/Evidence-Dashboard"
        ]
        assert policy["browser"]["fixedExternalNavigationRequiresExplicitClick"] is True
        assert policy["browser"]["rendererSuppliedExternalNavigationAllowed"] is False
        javascript = (ROOT / "web/static/app.js").read_text(encoding="utf-8")
        html = (ROOT / "web/static/index.html").read_text(encoding="utf-8")
        styles = (ROOT / "web/static/styles.css").read_text(encoding="utf-8")
        assert "innerHTML" not in javascript and "X-Haven-Token" in javascript
        assert "/api/text" in javascript and "content.summarize" in javascript
        assert "trust-scope" not in javascript and "modelSelections" in javascript
        assert "Automatic — no validated model installed" in javascript
        assert "Advanced manual selection" in javascript
        assert "result.downloadsPerformed !== false" in javascript
        assert "/api/model-search" in javascript and "Copy installation command" in html
        assert 'id="models-panel"' in html and 'id="model-search-capability"' in html
        assert 'id="model-search-consent"' not in html and "Search public catalog" in html
        assert "Already installed on connected Ollama server" in javascript
        assert "Not installed on connected Ollama server" in javascript
        assert 'id="cleanup-policy-form"' in html and 'id="system-idle-unload"' in html
        assert 'byId("system-idle-unload").value = String(idleUnloadSeconds)' in javascript
        assert 'state.desiredModel = null' in javascript and 'Showing installed models ranked for' in javascript
        assert html.count('class="field-row compact-control-row"') == 3
        assert ".compact-control-row input, .compact-control-row select { height: 36px; padding: 8px 10px; font-size: 13px; }" in styles
        assert ".advanced-grid select { height: 36px; padding: 8px 10px; font-size: 13px; }" in styles
        assert ".model-select select { min-width: 190px; height: 36px;" in styles
        assert "providerConfigChanged" in javascript and 'button.textContent = changed ? "Apply changes" : "Connected"' in javascript
        assert 'button.textContent = changed ? "Apply changes" : "Continue"' in javascript
        assert "renderProviderTransportWarning" in javascript
        assert 'id="connection-transport-warning"' in html and 'id="wizard-transport-warning"' in html
        assert "private-network Ollama connection uses unencrypted HTTP" in javascript
        assert ".transport-warning {" in styles and ".transport-warning.loopback {" in styles
        assert "selectedSeconds === state.idleUnloadSeconds" in javascript
        assert 'id="apply-cleanup-policy" type="submit" disabled>Selected</button>' in html
        assert "Applying changes starts a new task" in html
        assert 'id="about-panel"' in html and 'id="about-nav"' in html
        assert "03 · WRITING" not in javascript and "03 · SUMMARY" not in javascript
        assert "one continuous private conversation" in html
        assert 'id="model-switch-prompt"' in html and 'id="use-recommended-model"' in html
        assert "suggestedCapability" in javascript and "showModelSwitchPrompt" in javascript
        assert 'document.querySelectorAll(".mode-tab").length' not in javascript
        assert 'class="mode-tab' not in html and 'class="nav-item capability-nav' not in html
        assert "requestMessages = [...state.messages" in javascript
        assert "state.messages = requestMessages" in javascript
        assert "renderTypedResult(result, capability, capabilityId)" in javascript
        assert ".model-switch-prompt {" in styles and ".model-switch-actions {" in styles
        assert 'event.key !== "Enter"' in javascript and "event.shiftKey" in javascript
        assert "Enter to send · Shift+Enter for a new line" in html
        assert "↑/↓ recall prompts" in html and 'id="prompt-history-limit"' in html
        assert 'value="20" selected' in html and 'value="50"' in html and 'value="100"' in html
        assert "recordPromptHistory" in javascript and "recallPrompt" in javascript
        assert "clearPromptHistory" in javascript and "state.promptHistory.slice(-selectedLimit)" in javascript
        assert javascript.count("clearPromptHistory();") >= 3
        assert 'id="browse-context" type="button" disabled>Browse files</button>' in html
        assert 'id="context-files"' in html and (
            'accept=".txt,.md,.csv,.json,.png,text/plain,text/markdown,text/csv,application/json,image/png"'
            in html
        )
        assert 'id="context-images"' not in html and "Browse files" in html
        assert 'id="context-consent"' not in html
        assert 'id="context-network-warning"' in html and "private-network Ollama server" in html
        assert "addContextFiles" in javascript and "clearContextFiles" in javascript
        assert 'new TextDecoder("utf-8", { fatal: true })' in javascript
        assert 'contextConsent: hasContext && state.providerTrustScope === "trusted-lan"' in javascript
        assert "context-file-too-large" in javascript and "context-total-too-large" in javascript
        assert "validateContextJson" in javascript and "validateContextCsv" in javascript
        assert 'document.addEventListener("paste"' in javascript and "addContextImages" in javascript
        assert "inspectPngHeader" in javascript and "blobDataUrl" in javascript
        assert "MODEL_IMAGE_INPUT_UNVERIFIED" in javascript
        assert (
            'id="context-image-list"' in html
            and "browse UTF-8 .txt/.md/.csv/.json or PNG" in html
            and "paste a PNG screenshot" in html
            and "structured text is syntax-checked but never evaluated" in html
        )
        assert "Attachments are inert data and are never executed" in html
        assert "result.context.hostExecutionAllowed !== false" in javascript
        assert ".context-image img {" in styles and ".context-warning {" in styles
        assert 'previewText.textContent = file.content.length > 1000' in javascript
        assert "clearContextFiles();\n    showError" in javascript
        assert ".context-panel { flex: 0 1 auto; max-height: min(190px, 32vh);" in styles and ".context-file {" in styles
        assert ".messages { flex: 1 1 auto;" in styles and "min-height: 0; overflow: auto;" in styles
        assert ".composer { flex: 0 0 auto;" in styles
        assert "localStorage" not in javascript and "sessionStorage" not in javascript and "indexedDB" not in javascript
        assert ".system-setting select { height: 36px;" in styles
        assert ".hidden { display: none !important; }" in styles
        assert ".chat-panel > .panel-heading" in styles and "overflow-y: auto" in styles
        assert "appendInlineMarkdown" in javascript and "appendMarkdown" in javascript
        assert "markdownBlockKind" in javascript and 'text.className = "message-content"' in javascript
        assert ".message-content h3" in styles and ".message-content ul" in styles
        assert ".message-content pre" in styles and '"Segoe UI Emoji"' in styles
        assert "renderTypedResult" in javascript and "renderCapabilities" in javascript
        assert "/api/assurance" in javascript and 'id="assurance-panel"' in html
        assert 'id="assurance-nav"' in html and 'class="panel chat-panel hidden" id="assurance-panel"' in html
        assert html.index('id="assurance-panel"') < html.index('class="configuration-column"')
        assert '"assurance-panel", "about-panel"' in javascript and "openAssurance" in javascript
        assert 'id="assurance-surface-list"' in html and "renderAssuranceSummary" in javascript
        assert 'id="assurance-status-list"' in html and "assurance-status-item" in javascript
        assert "supportedActivities} supported" in javascript and "blockedActivities} blocked" in javascript
        assert html.count('href="https://github.com/hysel/haven-42/wiki/Evidence-Dashboard"') == 1 and html.count('href="http') == 1
        assert 'target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer"' in html
        assert "read-only-assurance-summary" in javascript and "providerInvocation" in javascript
        assert "Bundled sanitized evidence only" in html
        assert ".assurance-list {" in styles and ".assurance-item {" in styles
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
        assert "webbrowser" not in (ROOT / "web/server.py").read_text(encoding="utf-8")
        readiness_source = (ROOT / "scripts/system_readiness.py").read_text(encoding="utf-8")
        assert 'ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))' in readiness_source
        checks += 105
    finally:
        app.shutdown()
        app.server_close()
        fake.shutdown()
        fake.server_close()
    print(f"Haven 42 local-web self-test passed: {checks} security and behavior checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
