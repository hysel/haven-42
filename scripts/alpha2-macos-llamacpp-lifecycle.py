#!/usr/bin/env python3
"""Run a fail-closed, privacy-preserving llama.cpp lifecycle cell on Apple M4."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


SCHEMA = "haven42-alpha2-macos-llamacpp-lifecycle-result"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command_text(*args: str) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()


def free_loopback_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def request_json(port: int, key: str | None, timeout: float, *, prompt: str | None = None):
    endpoint = "/health" if prompt is None else "/v1/chat/completions"
    body = None
    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    if prompt is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(
            {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 24,
                "stream": False,
            }
        ).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{endpoint}", data=body, headers=headers
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def wait_ready(process: subprocess.Popen, port: int, key: str, deadline: float) -> None:
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("llama-server-exited-before-ready")
        try:
            status, _ = request_json(port, key, 2)
            if status == 200:
                return
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(0.25)
    raise RuntimeError("llama-server-readiness-timeout")


def stop(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def port_closed(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def full_offload_observed(log_text: str) -> bool:
    if re.search(r"offloaded all layers", log_text, re.IGNORECASE):
        return True
    for match in re.finditer(
        r"offload(?:ed|ing)[^\r\n]*?\b([0-9]+)\s*/\s*([0-9]+)\b[^\r\n]*layers",
        log_text,
        re.IGNORECASE,
    ):
        if int(match.group(1)) > 0 and match.group(1) == match.group(2):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--runtime-commit", required=True)
    parser.add_argument("--expected-server-sha256", required=True)
    parser.add_argument("--expected-model-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise SystemExit("Refused: this cell requires macOS on arm64.")
    hardware = command_text("/usr/sbin/system_profiler", "SPHardwareDataType")
    if "Chip: Apple M4" not in hardware or "Memory: 16 GB" not in hardware:
        raise SystemExit("Refused: this cell requires the exact Apple M4 16 GB profile.")
    if not args.server.is_file() or not os.access(args.server, os.X_OK):
        raise SystemExit("Refused: exact llama-server is unavailable or not executable.")
    if not args.model.is_file():
        raise SystemExit("Refused: exact GGUF model is unavailable.")
    server_hash = sha256(args.server)
    model_hash = sha256(args.model)
    if server_hash != args.expected_server_sha256 or model_hash != args.expected_model_sha256:
        raise SystemExit("Refused: exact runtime or model digest does not match.")

    port = free_loopback_port()
    key = hashlib.sha256(os.urandom(32)).hexdigest()
    log_fd, log_name = tempfile.mkstemp(prefix="haven42-llamacpp-", suffix=".log")
    os.close(log_fd)
    log_path = Path(log_name)
    started = time.monotonic()
    first_tokens = 0
    recovery_tokens = 0
    unauthorized_rejected = False
    forced_timeout_observed = False
    first_process = None
    second_process = None
    try:
        with log_path.open("wb") as log:
            command = [
                str(args.server), "-m", str(args.model), "--host", "127.0.0.1",
                "--port", str(port), "-ngl", "99", "-c", "4096", "-np", "1",
                "--no-webui", "--reasoning", "off", "--verbose", "--api-key", key,
            ]
            first_process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            wait_ready(first_process, port, key, time.monotonic() + 90)
            try:
                request_json(port, None, 3, prompt="Return only UNAUTHORIZED.")
            except urllib.error.HTTPError as error:
                unauthorized_rejected = error.code in {401, 403}
            if not unauthorized_rejected:
                raise RuntimeError("unauthorized-request-was-not-rejected")

            status, response = request_json(
                port, key, 120, prompt="Reply with exactly MAC_LLAMA_OK."
            )
            text = response["choices"][0]["message"]["content"]
            first_tokens = int(response.get("usage", {}).get("completion_tokens", 0))
            if status != 200 or "MAC_LLAMA_OK" not in text or first_tokens < 1:
                raise RuntimeError("bounded-inference-contract-failed")

            try:
                request_json(port, key, 0.001, prompt="Count slowly from one to one hundred.")
            except (TimeoutError, OSError, urllib.error.URLError):
                forced_timeout_observed = True
            if not forced_timeout_observed or first_process.poll() is not None:
                raise RuntimeError("timeout-did-not-preserve-runtime")

            status, response = request_json(
                port, key, 120, prompt="Reply with exactly MAC_LLAMA_RECOVERED."
            )
            text = response["choices"][0]["message"]["content"]
            recovery_tokens = int(response.get("usage", {}).get("completion_tokens", 0))
            if status != 200 or "MAC_LLAMA_RECOVERED" not in text or recovery_tokens < 1:
                raise RuntimeError("post-timeout-recovery-failed")
            stop(first_process)
            if not port_closed(port):
                raise RuntimeError("listener-remained-after-stop")

            second_process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            wait_ready(second_process, port, key, time.monotonic() + 90)
            stop(second_process)
            if not port_closed(port):
                raise RuntimeError("listener-remained-after-restart-stop")

        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        metal = bool(re.search(r"Metal|ggml_metal", log_text, re.IGNORECASE))
        offload = full_offload_observed(log_text)
        if not metal:
            raise RuntimeError("metal-proof-missing")
        if not offload:
            raise RuntimeError("full-offload-proof-missing")

        result = {
            "schemaVersion": 1,
            "kind": SCHEMA,
            "outcome": "passed",
            "profile": {"hardware": "Apple M4", "memoryGiB": 16, "os": "macOS", "architecture": "arm64"},
            "runtime": {"name": "llama.cpp", "commit": args.runtime_commit, "serverSha256": server_hash},
            "model": {"id": "Qwen3.5-0.8B-Q4_0-GGUF", "sha256": model_hash},
            "checks": {
                "loopbackOnly": True,
                "webUiDisabled": True,
                "authenticationRequired": unauthorized_rejected,
                "metalDetected": metal,
                "allLayersOffloaded": offload,
                "boundedInference": True,
                "forcedTimeoutObserved": forced_timeout_observed,
                "postTimeoutRecovery": True,
                "restart": True,
                "listenerClosed": True,
            },
            "metrics": {
                "firstCompletionTokens": first_tokens,
                "recoveryCompletionTokens": recovery_tokens,
                "durationSeconds": round(time.monotonic() - started, 3),
            },
            "authority": {"changesDefaults": False, "changesSupport": False, "changesPackaging": False},
            "privacy": {"containsPrompt": False, "containsResponse": False, "containsPrivatePath": False, "containsCredential": False},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("Apple M4 llama.cpp lifecycle passed.")
        return 0
    finally:
        for process in (first_process, second_process):
            if process is not None and process.poll() is None:
                stop(process)
        log_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
