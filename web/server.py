#!/usr/bin/env python3
"""Haven 42 local-web application.

This process binds only to IPv4 loopback, serves bundled assets, and proxies
bounded requests to an explicitly selected Ollama endpoint. Configuration and
text content stay in memory and are never written by this server.
"""

from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import json
import platform
import re
import secrets
import struct
import sys
import threading
import time
import urllib.request
import urllib.parse
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable


SOURCE_ROOT = Path(__file__).resolve().parent.parent
ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))
STATIC_ROOT = ROOT / "web" / "static"
sys.path.insert(0, str(ROOT / "scripts"))

from provider_security import (  # noqa: E402
    MAX_JSON_RESPONSE_BYTES,
    ProviderSecurityError,
    read_bounded,
    read_json,
    validate_base_url,
    validate_local_base_url,
)
from system_readiness import (  # noqa: E402
    ReadinessError,
    build_setup_plan,
    inspect_system,
    validate_snapshot,
)


APP_VERSION = "0.3.0"
INTEGRITY_MANIFEST_PATH = ROOT / "package" / "resource-integrity.json"
MAX_REQUEST_BYTES = 64 * 1024
MAX_MESSAGE_BYTES = 32 * 1024
MAX_CHAT_RESPONSE_BYTES = 1024 * 1024
MAX_WEB_IMAGE_BYTES = 16 * 1024 * 1024
MAX_IMAGE_PROMPT_BYTES = 8 * 1024
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
WORKFLOW_REGISTRY_PATH = ROOT / "config" / "workflows.json"
PROMOTED_IMAGE_MODEL = "sd_xl_base_1.0.safetensors"
MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/:+-]{0,255}$")
MODEL_DIGEST = re.compile(r"^[0-9a-f]{64}$")
CAPABILITY_OPERATION = {
    "general.chat": "general-chat",
    "content.write": "general-writing",
    "content.summarize": "general-summarization",
}
CAPABILITY_SUMMARY = (
    {
        "id": "general.chat", "label": "Chat", "operationKind": "capability",
        "operationId": "general.chat", "state": "configuration-required", "execution": "local",
    },
    {
        "id": "content.write", "label": "Writing", "operationKind": "capability",
        "operationId": "content.write", "state": "configuration-required", "execution": "local",
    },
    {
        "id": "content.summarize", "label": "Summarization", "operationKind": "capability",
        "operationId": "content.summarize", "state": "configuration-required", "execution": "local",
    },
    {
        "id": "software", "label": "Software", "operationKind": "workflow-group",
        "operationId": "engineering.software-work", "state": "available", "execution": "local",
    },
    {
        "id": "media.image.create", "label": "Images", "operationKind": "capability",
        "operationId": "media.image.create", "state": "provider-profile-required", "execution": "unavailable",
    },
)


class WebRequestError(ValueError):
    def __init__(self, code: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(code)
        self.code = code
        self.status = status


def verify_packaged_resources(path: Path = INTEGRITY_MANIFEST_PATH) -> dict[str, Any]:
    """Verify the strict, build-generated resource allowlist in frozen packages."""
    if not getattr(sys, "frozen", False):
        return {"required": False, "verified": False, "resourceCount": 0}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {"schemaVersion", "algorithm", "resources"}
            or manifest["schemaVersion"] != 1
            or manifest["algorithm"] != "sha256"
            or not isinstance(manifest["resources"], list)
        ):
            raise ValueError("invalid-manifest")
        seen: set[str] = set()
        for record in manifest["resources"]:
            if not isinstance(record, dict) or set(record) != {"path", "sha256", "sizeBytes"}:
                raise ValueError("invalid-record")
            relative = Path(str(record["path"]))
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or relative.as_posix() in seen
                or not re.fullmatch(r"[0-9a-f]{64}", str(record["sha256"]))
                or isinstance(record["sizeBytes"], bool)
                or not isinstance(record["sizeBytes"], int)
                or record["sizeBytes"] < 0
            ):
                raise ValueError("unsafe-record")
            seen.add(relative.as_posix())
            target = ROOT / relative
            data = target.read_bytes()
            if len(data) != record["sizeBytes"]:
                raise ValueError("size-mismatch")
            if not secrets.compare_digest(hashlib.sha256(data).hexdigest(), record["sha256"]):
                raise ValueError("digest-mismatch")
        if not seen:
            raise ValueError("empty-manifest")
        actual = {
            target.relative_to(ROOT).as_posix()
            for parent in (ROOT / "web" / "static", ROOT / "config")
            if parent.is_dir()
            for target in parent.rglob("*")
            if target.is_file()
        }
        if actual != seen:
            raise ValueError("resource-allowlist-mismatch")
        return {"required": True, "verified": True, "resourceCount": len(seen)}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise RuntimeError("Packaged resource integrity verification failed.") from error


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
            or set(value) != {"schemaVersion", "catalogId", "selectionPolicy", "capabilities"}
            or value.get("schemaVersion") != 1
            or value.get("catalogId") != "haven42.text-capability-model-recommendations"
            or not isinstance(value.get("capabilities"), dict)
            or set(value["capabilities"]) != set(CAPABILITY_PROMPTS)
            or value.get("selectionPolicy") != {
                "automaticRequiresExactCapabilityEvidence": True,
                "unknownInstalledModelsAre": "unverified",
                "downloadsAllowed": False,
                "hardwareFitSource": "execution-host-profile-required",
            }
        ):
            return {}
        result: dict[str, tuple[dict[str, Any], ...]] = {}
        evidence_ids: set[str] = set()
        for capability_id, records in value["capabilities"].items():
            if capability_id not in CAPABILITY_PROMPTS or not isinstance(records, list):
                return {}
            admitted: list[dict[str, Any]] = []
            seen_models: set[str] = set()
            for record in records:
                if (
                    not isinstance(record, dict)
                    or set(record) != {
                        "model", "digest", "priority", "evidenceId", "evidenceStatus",
                        "evidenceOperation", "evidence",
                    }
                    or not isinstance(record["model"], str)
                    or not MODEL_NAME.fullmatch(record["model"])
                    or not isinstance(record["digest"], str)
                    or not MODEL_DIGEST.fullmatch(record["digest"])
                    or record["model"] in seen_models
                    or isinstance(record["priority"], bool)
                    or not isinstance(record["priority"], int)
                    or record["priority"] < 0
                    or record["priority"] > 1000
                    or record["evidenceStatus"] != "passed"
                    or not isinstance(record["evidenceId"], str)
                    or not record["evidenceId"].strip()
                    or record["evidenceId"] in evidence_ids
                    or not isinstance(record["evidenceOperation"], str)
                    or record["evidenceOperation"] != CAPABILITY_OPERATION[capability_id]
                    or not isinstance(record["evidence"], str)
                    or not record["evidence"].startswith("examples/")
                    or not record["evidence"].endswith(".md")
                    or ".." in Path(record["evidence"]).parts
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
                seen_models.add(record["model"])
                evidence_ids.add(record["evidenceId"])
                admitted.append({
                    "model": record["model"],
                    "digest": record["digest"],
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
    installed_digests: dict[str, str] | None = None,
) -> dict[str, Any]:
    installed = set(installed_models)
    digests = installed_digests or {}
    evidenced_anywhere = {
        record["model"]
        for records in catalog.values()
        for record in records
    }
    recommendations: dict[str, dict[str, Any]] = {}
    for capability_id in CAPABILITY_PROMPTS:
        candidates = catalog.get(capability_id, ())
        chosen = next((
            record
            for record in candidates
            if record["model"] in installed
            and secrets.compare_digest(
                record.get("digest", ""),
                digests.get(record["model"], ""),
            )
        ), None)
        if chosen is not None:
            recommendations[capability_id] = {
                "status": "recommended",
                "model": chosen["model"],
                "evidenceId": chosen["evidenceId"],
                "digestVerified": True,
                "hardwareFit": "unknown",
                "automatic": True,
            }
        elif candidates:
            recommendations[capability_id] = {
                "status": "missing",
                "model": candidates[0]["model"],
                "evidenceId": candidates[0]["evidenceId"],
                "digestVerified": False,
                "hardwareFit": "unknown",
                "automatic": False,
            }
        else:
            recommendations[capability_id] = {
                "status": "missing",
                "model": None,
                "evidenceId": None,
                "digestVerified": False,
                "hardwareFit": "unknown",
                "automatic": False,
            }
    options = []
    for model in installed_models:
        capability_status = {}
        for capability_id in CAPABILITY_PROMPTS:
            exact = any(
                record["model"] == model
                and secrets.compare_digest(record.get("digest", ""), digests.get(model, ""))
                for record in catalog.get(capability_id, ())
            )
            capability_status[capability_id] = (
                "recommended"
                if exact
                else "compatible"
                if model in evidenced_anywhere
                else "unverified"
            )
        options.append({
            "name": model,
            "digestVerified": any(
                record["model"] == model
                and secrets.compare_digest(record.get("digest", ""), digests.get(model, ""))
                for records in catalog.values()
                for record in records
            ),
            "capabilityStatus": capability_status,
        })
    return {
        "catalogStatus": "ready" if catalog else "unavailable",
        "recommendations": recommendations,
        "modelOptions": options,
        "downloadsPerformed": False,
    }


def load_read_only_workflows(path: Path = WORKFLOW_REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    """Load the renderer-visible no-argument planning surface; fail closed."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(value, dict)
            or set(value) != {"schemaVersion", "description", "workflows"}
            or value.get("schemaVersion") != 1
            or not isinstance(value.get("workflows"), list)
        ):
            return {}
        result: dict[str, dict[str, Any]] = {}
        for record in value["workflows"]:
            if not isinstance(record, dict):
                return {}
            workflow_id = record.get("id")
            if (
                not isinstance(workflow_id, str)
                or not re.fullmatch(r"[a-z][a-z0-9-]{0,127}", workflow_id)
                or workflow_id in result
            ):
                return {}
            if record.get("uiReady") is not True or record.get("safetyLevel") != "read-only":
                continue
            if not all(
                isinstance(record.get(field), str) and record[field].strip()
                for field in ("name", "purpose", "category")
            ):
                return {}
            result[workflow_id] = {
                "id": workflow_id,
                "name": record["name"][:160],
                "purpose": record["purpose"][:1000],
                "category": record["category"][:80],
                "safetyLevel": "read-only",
                "executionMode": "plan-only",
                "rendererArgumentsAllowed": False,
            }
        return result
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}


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


def png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise WebRequestError("invalid-image-provider-png", HTTPStatus.BAD_GATEWAY)
    width, height = struct.unpack(">II", data[16:24])
    if width < 64 or height < 64 or width > 2048 or height > 2048:
        raise WebRequestError("invalid-image-dimensions", HTTPStatus.BAD_GATEWAY)
    return width, height


class HavenState:
    def __init__(
        self,
        recommendation_path: Path = MODEL_RECOMMENDATIONS_PATH,
        readiness_provider: Callable[[], dict[str, Any]] = inspect_system,
    ) -> None:
        self.csrf_token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.base_url: str | None = None
        self.trust_scope: str | None = None
        self.timeout_seconds = 120
        self.idle_unload_seconds = 300
        self.models: tuple[str, ...] = ()
        self.model_digests: dict[str, str] = {}
        self.ollama_version: str | None = None
        self.used_models: set[tuple[str, str, int]] = set()
        self.active_model: tuple[str, str, int] | None = None
        self.idle_timer: threading.Timer | None = None
        self.lifecycle_generation = 0
        self.operation_lock = threading.Lock()
        self.readiness_lock = threading.Lock()
        self.image_lock = threading.Lock()
        self.image_base_url: str | None = None
        self.image_timeout_seconds = 300
        self.readiness_provider = readiness_provider
        self.readiness_snapshot: dict[str, Any] | None = None
        self.readiness_created = 0.0
        self.model_recommendations = load_model_recommendations(recommendation_path)
        self.read_only_workflows = load_read_only_workflows()
        self.package_integrity = verify_packaged_resources()

    def public_status(self) -> dict[str, Any]:
        with self.lock:
            connected = self.base_url is not None
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
                "capabilities": [
                    {
                        **item,
                        "state": (
                            "available"
                            if connected and item["id"] in CAPABILITY_PROMPTS
                            else item["state"]
                        ),
                    }
                    for item in CAPABILITY_SUMMARY
                ],
                "updates": {
                    "mode": "disabled",
                    "networkCheckPerformed": False,
                    "downloadAllowed": False,
                    "activationAllowed": False,
                },
                "package": self.package_integrity,
                "readiness": {
                    "scanAvailable": True,
                    "scanPerformed": self.readiness_snapshot is not None,
                    "installationAvailable": False,
                    "snapshotPersisted": False,
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

    def list_workflows(self) -> dict[str, Any]:
        workflows = [
            self.read_only_workflows[key]
            for key in sorted(self.read_only_workflows)
        ]
        return {
            "schemaVersion": 1,
            "kind": "workflow-catalog",
            "executionMode": "plan-only",
            "workflows": workflows,
            "arbitraryCommandsAllowed": False,
            "rendererArgumentsAllowed": False,
        }

    def plan_workflow(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.read_only_workflows.get(workflow_id)
        if workflow is None:
            raise WebRequestError("workflow-not-admitted")
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return {
            "schemaVersion": 1,
            "kind": "workflow-execution",
            "status": "planned",
            "workflow": workflow,
            "events": [
                {"sequence": 1, "type": "accepted", "code": "WORKFLOW_REQUEST_ACCEPTED"},
                {"sequence": 2, "type": "warning", "code": "PLAN_ONLY_NO_PROCESS_STARTED"},
                {"sequence": 3, "type": "result", "code": "WORKFLOW_PLAN_READY"},
            ],
            "result": {
                "invoked": False,
                "dryRun": True,
                "processStarted": False,
                "argumentsAccepted": False,
            },
            "artifact": {
                "schemaVersion": 1,
                "artifactType": "engineering-report",
                "status": "planned",
                "createdAtUtc": now,
                "sourceCapabilityId": "engineering.software-work",
                "content": {
                    "workflowId": workflow["id"],
                    "title": workflow["name"],
                    "summary": workflow["purpose"],
                    "executionMode": "plan-only",
                },
                "policy": {
                    "localExecution": True,
                    "externalProvider": False,
                    "repositoryRead": False,
                    "fileWrite": False,
                    "networkAccess": False,
                    "modelDownload": False,
                    "approvalRequired": False,
                },
            },
        }

    def connect_image_provider(self, endpoint: str, timeout_seconds: int) -> dict[str, Any]:
        try:
            policy = validate_base_url(endpoint, "loopback")
        except ProviderSecurityError as error:
            raise WebRequestError(str(error)) from error
        if timeout_seconds < 30 or timeout_seconds > 600:
            raise WebRequestError("invalid-image-timeout")
        try:
            object_info = _provider_json(
                policy["baseUrl"],
                "/object_info/CheckpointLoaderSimple",
                timeout_seconds,
            )
        except (OSError, ProviderSecurityError) as error:
            raise WebRequestError("comfyui-connection-failed", HTTPStatus.BAD_GATEWAY) from error
        try:
            checkpoints = object_info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        except (KeyError, IndexError, TypeError) as error:
            raise WebRequestError("invalid-comfyui-checkpoint-discovery", HTTPStatus.BAD_GATEWAY) from error
        if (
            not isinstance(checkpoints, list)
            or PROMOTED_IMAGE_MODEL not in checkpoints
            or any(not isinstance(item, str) or len(item) > 256 for item in checkpoints)
        ):
            raise WebRequestError("promoted-image-checkpoint-not-available", HTTPStatus.CONFLICT)
        with self.lock:
            self.image_base_url = policy["baseUrl"]
            self.image_timeout_seconds = timeout_seconds
        return {
            "schemaVersion": 1,
            "kind": "image-provider-connection",
            "connected": True,
            "providerId": "comfyui.local-image",
            "trustScope": "loopback",
            "model": PROMOTED_IMAGE_MODEL,
            "profile": "linux-comfyui-sdxl-promoted",
            "configurationPersisted": False,
            "customNodesAllowed": False,
            "externalApiNodesAllowed": False,
            "providerRetainsOutput": True,
        }

    def run_image_capability(
        self,
        prompt: str,
        width: int,
        height: int,
        steps: int,
        seed: int,
    ) -> dict[str, Any]:
        with self.lock:
            base_url = self.image_base_url
            timeout_seconds = self.image_timeout_seconds
        if base_url is None:
            raise WebRequestError("image-provider-not-connected", HTTPStatus.CONFLICT)
        if not isinstance(prompt, str) or not prompt.strip():
            raise WebRequestError("invalid-image-prompt")
        if len(prompt.encode("utf-8")) > MAX_IMAGE_PROMPT_BYTES:
            raise WebRequestError("image-prompt-too-large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        if width not in {512, 768, 1024} or height not in {512, 768, 1024}:
            raise WebRequestError("invalid-image-dimensions")
        if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1 or steps > 30:
            raise WebRequestError("invalid-image-steps")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 or seed > 2**63 - 1:
            raise WebRequestError("invalid-image-seed")
        if not self.image_lock.acquire(blocking=False):
            raise WebRequestError("image-generation-in-progress", HTTPStatus.CONFLICT)
        prompt_id = ""
        try:
            node_prefix = "haven-42/" + uuid.uuid4().hex
            workflow = {
                "3": {"class_type": "KSampler", "inputs": {
                    "seed": seed, "steps": steps, "cfg": 7.0, "sampler_name": "euler",
                    "scheduler": "normal", "denoise": 1.0, "model": ["4", 0],
                    "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0],
                }},
                "4": {"class_type": "CheckpointLoaderSimple", "inputs": {
                    "ckpt_name": PROMOTED_IMAGE_MODEL,
                }},
                "5": {"class_type": "EmptyLatentImage", "inputs": {
                    "width": width, "height": height, "batch_size": 1,
                }},
                "6": {"class_type": "CLIPTextEncode", "inputs": {
                    "text": prompt, "clip": ["4", 1],
                }},
                "7": {"class_type": "CLIPTextEncode", "inputs": {
                    "text": "text, watermark, logo, blurry, distorted", "clip": ["4", 1],
                }},
                "8": {"class_type": "VAEDecode", "inputs": {
                    "samples": ["3", 0], "vae": ["4", 2],
                }},
                "9": {"class_type": "SaveImage", "inputs": {
                    "filename_prefix": node_prefix, "images": ["8", 0],
                }},
            }
            submitted = _provider_json(
                base_url,
                "/prompt",
                timeout_seconds,
                {"prompt": workflow, "client_id": "haven-42-local-web"},
            )
            prompt_id = str(submitted.get("prompt_id", ""))
            if not re.fullmatch(r"[A-Za-z0-9-]{1,128}", prompt_id):
                raise WebRequestError("invalid-image-prompt-id", HTTPStatus.BAD_GATEWAY)
            deadline = time.monotonic() + timeout_seconds
            image_info: dict[str, Any] | None = None
            while time.monotonic() < deadline:
                history = _provider_json(
                    base_url,
                    "/history/" + urllib.parse.quote(prompt_id, safe=""),
                    timeout_seconds,
                )
                job = history.get(prompt_id)
                if isinstance(job, dict) and job.get("outputs"):
                    if job.get("status", {}).get("status_str") != "success":
                        raise WebRequestError("comfyui-image-job-failed", HTTPStatus.BAD_GATEWAY)
                    image_info = job["outputs"]["9"]["images"][0]
                    break
                time.sleep(0.5)
            if not isinstance(image_info, dict):
                raise WebRequestError("image-generation-timeout", HTTPStatus.GATEWAY_TIMEOUT)
            filename = image_info.get("filename")
            subfolder = image_info.get("subfolder", "")
            image_type = image_info.get("type")
            if (
                not isinstance(filename, str) or not filename or len(filename) > 256
                or not isinstance(subfolder, str) or len(subfolder) > 256
                or image_type not in {"output", "temp"}
            ):
                raise WebRequestError("invalid-image-provider-result", HTTPStatus.BAD_GATEWAY)
            query = urllib.parse.urlencode({
                "filename": filename,
                "subfolder": subfolder,
                "type": image_type,
            })
            image_bytes = read_bounded(
                base_url + "/view?" + query,
                timeout_seconds,
                MAX_WEB_IMAGE_BYTES,
            )
            actual_width, actual_height = png_dimensions(image_bytes)
        except WebRequestError:
            raise
        except (OSError, ProviderSecurityError, KeyError, IndexError, TypeError) as error:
            raise WebRequestError("comfyui-image-request-failed", HTTPStatus.BAD_GATEWAY) from error
        finally:
            try:
                _provider_json(base_url, "/history", min(timeout_seconds, 30), {"clear": True})
            except (OSError, ProviderSecurityError):
                pass
            self.image_lock.release()
        artifact = {
            "schemaVersion": 1,
            "artifactType": "image",
            "status": "succeeded",
            "createdAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "sourceCapabilityId": "media.image.create",
            "content": {
                "delivery": "browser-memory",
                "mediaType": "image/png",
                "width": actual_width,
                "height": actual_height,
                "seed": seed,
                "downloadName": "haven42-generated-image.png",
            },
            "policy": {
                "localExecution": True,
                "externalProvider": False,
                "repositoryRead": False,
                "fileWrite": False,
                "networkAccess": True,
                "modelDownload": False,
                "approvalRequired": True,
                "providerRetainedOutput": True,
            },
        }
        return {
            "schemaVersion": 1,
            "kind": "image",
            "capabilityId": "media.image.create",
            "status": "succeeded",
            "providerId": "comfyui.local-image",
            "model": PROMOTED_IMAGE_MODEL,
            "imageBase64": base64.b64encode(image_bytes).decode("ascii"),
            "promptPersisted": False,
            "endpointPersisted": False,
            "events": [
                {"sequence": 1, "type": "accepted", "code": "IMAGE_REQUEST_ACCEPTED"},
                {"sequence": 2, "type": "progress", "code": "IMAGE_PROVIDER_COMPLETED"},
                {"sequence": 3, "type": "warning", "code": "PROVIDER_RETAINS_OUTPUT"},
                {"sequence": 4, "type": "result", "code": "IMAGE_ARTIFACT_READY"},
            ],
            "artifact": artifact,
        }

    def inspect_readiness(self, force: bool) -> dict[str, Any]:
        with self.lock:
            cached = self.readiness_snapshot
            age = time.monotonic() - self.readiness_created
        if not force and cached is not None and age <= 30:
            return cached
        if not self.readiness_lock.acquire(blocking=False):
            raise WebRequestError("readiness-scan-in-progress", HTTPStatus.CONFLICT)
        try:
            snapshot = self.readiness_provider()
            validate_snapshot(snapshot)
            with self.lock:
                self.readiness_snapshot = snapshot
                self.readiness_created = time.monotonic()
            return snapshot
        except ReadinessError as error:
            raise WebRequestError(str(error), HTTPStatus.INTERNAL_SERVER_ERROR) from error
        finally:
            self.readiness_lock.release()

    def setup_plan(self, snapshot_id: str, intent: str) -> dict[str, Any]:
        with self.lock:
            snapshot = self.readiness_snapshot
            age = time.monotonic() - self.readiness_created
        if snapshot is None or age > 300:
            raise WebRequestError("readiness-snapshot-expired", HTTPStatus.CONFLICT)
        if not secrets.compare_digest(str(snapshot.get("snapshotId", "")), snapshot_id):
            raise WebRequestError("readiness-snapshot-mismatch", HTTPStatus.CONFLICT)
        try:
            return build_setup_plan(snapshot, intent)
        except ReadinessError as error:
            raise WebRequestError(str(error)) from error

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
                self.model_digests = {}
                self.ollama_version = None
            try:
                version = _provider_json(base_url, "/api/version", timeout_seconds)
                tags = _provider_json(base_url, "/api/tags", timeout_seconds)
            except (OSError, ProviderSecurityError) as error:
                raise WebRequestError("ollama-connection-failed", HTTPStatus.BAD_GATEWAY) from error
        records = tags.get("models", [])
        if not isinstance(records, list):
            raise WebRequestError("invalid-ollama-model-list", HTTPStatus.BAD_GATEWAY)
        model_digests: dict[str, str] = {}
        for item in records:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model", "")).strip()
            digest = str(item.get("digest", "")).strip().lower()
            if MODEL_NAME.fullmatch(name):
                model_digests[name] = digest if MODEL_DIGEST.fullmatch(digest) else ""
        models = sorted(model_digests)
        with self.lock:
            self.base_url = base_url
            self.trust_scope = policy["trustScope"]
            self.timeout_seconds = timeout_seconds
            self.idle_unload_seconds = idle_unload_seconds
            self.models = tuple(models)
            self.model_digests = model_digests
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
        result.update(build_model_decisions(models, self.model_recommendations, model_digests))
        result["providerHealth"] = {
            "status": "healthy",
            "providerId": "ollama.local-text",
            "trustScope": policy["trustScope"],
            "modelDiscovery": "complete",
            "modelCount": len(models),
            "configurationPersisted": False,
        }
        result["evidenceBoundary"] = {
            "catalogStatus": result["catalogStatus"],
            "recommendationBinding": "model-name-digest-and-capability-evidence",
            "immutableDigestBound": any(
                decision.get("automatic") is True
                and decision.get("digestVerified") is True
                for decision in result["recommendations"].values()
            ),
            "hardwareFitMeasured": False,
            "unknownModelsGainAuthority": False,
        }
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
            model_digests = dict(self.model_digests)
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
                    "think": False,
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
        model_is_evidenced = any(
            record["model"] == model
            and secrets.compare_digest(
                record.get("digest", ""),
                model_digests.get(model, ""),
            )
            for record in self.model_recommendations.get(capability_id, ())
        )
        def bounded_provider_integer(name: str) -> int | None:
            value = response.get(name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**18:
                return None
            return value

        input_tokens = bounded_provider_integer("prompt_eval_count")
        output_tokens = bounded_provider_integer("eval_count")
        total_duration = bounded_provider_integer("total_duration")
        generation_duration = bounded_provider_integer("eval_duration")
        tokens_per_second = (
            round(output_tokens / (generation_duration / 1_000_000_000), 2)
            if output_tokens is not None and generation_duration
            else None
        )
        run_details = {
            "providerReported": True,
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
            "totalTokens": (
                input_tokens + output_tokens
                if input_tokens is not None and output_tokens is not None
                else None
            ),
            "tokensPerSecond": tokens_per_second,
            "totalDurationMs": round(total_duration / 1_000_000, 2) if total_duration is not None else None,
            "loadDurationMs": (
                round(value / 1_000_000, 2)
                if (value := bounded_provider_integer("load_duration")) is not None
                else None
            ),
            "promptDurationMs": (
                round(value / 1_000_000, 2)
                if (value := bounded_provider_integer("prompt_eval_duration")) is not None
                else None
            ),
            "generationDurationMs": (
                round(generation_duration / 1_000_000, 2)
                if generation_duration is not None
                else None
            ),
        }
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        artifact = {
            "schemaVersion": 1,
            "artifactType": artifact_kind,
            "status": "succeeded",
            "createdAtUtc": now,
            "sourceCapabilityId": capability_id,
            "content": {
                "role": "assistant",
                "title": (
                    None
                    if capability_id == "general.chat"
                    else "Generated Writing"
                    if capability_id == "content.write"
                    else "Summary"
                ),
                "text": content,
            },
            "policy": {
                "localExecution": True,
                "externalProvider": False,
                "repositoryRead": False,
                "fileWrite": False,
                "networkAccess": False,
                "modelDownload": False,
                "approvalRequired": False,
            },
        }
        events = [
            {"sequence": 1, "type": "accepted", "code": "TEXT_REQUEST_ACCEPTED"},
            {"sequence": 2, "type": "progress", "code": "TEXT_PROVIDER_COMPLETED"},
        ]
        if not model_is_evidenced:
            events.append({
                "sequence": 3,
                "type": "warning",
                "code": "MODEL_SELECTION_UNVERIFIED_FOR_CAPABILITY",
            })
        events.append({
            "sequence": len(events) + 1,
            "type": "result",
            "code": "TEXT_ARTIFACT_READY",
        })
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
            "modelDigestVerified": model_is_evidenced,
            "runDetails": run_details,
            "modelUnloaded": unloaded,
            "modelResidency": residency,
            "promptPersisted": False,
            "endpointPersisted": False,
            "events": events,
            "artifact": artifact,
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
        value: dict[str, Any] = {"error": error.code}
        if self.path in {"/api/text", "/api/image/run", "/api/workflow-plan"}:
            kind_prefix = (
                "text"
                if self.path == "/api/text"
                else "image"
                if self.path == "/api/image/run"
                else "workflow"
            )
            retryable = error.code in {"ollama-chat-failed", "empty-model-response"}
            if self.path == "/api/image/run":
                retryable = error.code in {
                    "comfyui-image-request-failed",
                    "comfyui-image-job-failed",
                    "image-generation-timeout",
                }
            accepted = error.code in {
                "ollama-chat-failed",
                "empty-model-response",
                "previous-model-unload-failed",
                "comfyui-image-request-failed",
                "comfyui-image-job-failed",
                "image-generation-timeout",
            }
            events = []
            if accepted:
                events.append({
                    "sequence": 1,
                    "type": "accepted",
                    "code": f"{kind_prefix.upper()}_REQUEST_ACCEPTED",
                })
            events.append({
                "sequence": len(events) + 1,
                "type": "error",
                "code": error.code.upper().replace("-", "_"),
            })
            value.update({
                "schemaVersion": 1,
                "kind": f"{kind_prefix}-execution-error",
                "status": "failed",
                "events": events,
                "recovery": {
                    "automaticRetryAttempted": False,
                    "retryAllowed": retryable,
                    "retryRequiresNewRequest": True,
                    "inputMayBeRestored": True,
                },
            })
        self._send_json(error.status, value)

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
            if self.path == "/api/readiness":
                if set(body) != {"force"} or not isinstance(body["force"], bool):
                    raise WebRequestError("invalid-readiness-fields")
                self._send_json(HTTPStatus.OK, self.server.state.inspect_readiness(body["force"]))
                return
            if self.path == "/api/workflows":
                if body:
                    raise WebRequestError("invalid-workflow-catalog-fields")
                self._send_json(HTTPStatus.OK, self.server.state.list_workflows())
                return
            if self.path == "/api/workflow-plan":
                if set(body) != {"workflowId"} or not isinstance(body["workflowId"], str):
                    raise WebRequestError("invalid-workflow-plan-fields")
                self._send_json(
                    HTTPStatus.OK,
                    self.server.state.plan_workflow(body["workflowId"]),
                )
                return
            if self.path == "/api/image/connect":
                if set(body) != {"endpoint", "timeoutSeconds"}:
                    raise WebRequestError("invalid-image-connect-fields")
                self._send_json(
                    HTTPStatus.OK,
                    self.server.state.connect_image_provider(
                        str(body["endpoint"]),
                        int(body["timeoutSeconds"]),
                    ),
                )
                return
            if self.path == "/api/image/run":
                if set(body) != {"prompt", "width", "height", "steps", "seed"}:
                    raise WebRequestError("invalid-image-run-fields")
                self._send_json(
                    HTTPStatus.OK,
                    self.server.state.run_image_capability(
                        body["prompt"],
                        body["width"],
                        body["height"],
                        body["steps"],
                        body["seed"],
                    ),
                )
                return
            if self.path == "/api/setup-plan":
                if set(body) != {"snapshotId", "intent"}:
                    raise WebRequestError("invalid-setup-plan-fields")
                self._send_json(
                    HTTPStatus.OK,
                    self.server.state.setup_plan(str(body["snapshotId"]), str(body["intent"])),
                )
                return
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
            if self.path == "/api/shutdown":
                if body:
                    raise WebRequestError("invalid-shutdown-fields")
                unloaded = self.server.state.unload_used_models()
                if not unloaded:
                    raise WebRequestError("model-cleanup-failed", HTTPStatus.BAD_GATEWAY)
                self._send_json(HTTPStatus.OK, {
                    "shutdownAccepted": True,
                    "modelCleanupVerified": True,
                })
                threading.Thread(target=self.server.shutdown, daemon=True).start()
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
    print(f"Haven 42 is available at {url}", flush=True)
    print(
        "The server is loopback-only. Configuration and text content are not persisted.",
        flush=True,
    )
    if not args.no_open:
        threading.Timer(0.4, lambda: webbrowser.open_new_tab(url)).start()
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
