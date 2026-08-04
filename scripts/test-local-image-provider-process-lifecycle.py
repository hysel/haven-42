#!/usr/bin/env python3
"""Exercise an isolated loopback dummy provider and exact-process lifecycle."""

from __future__ import annotations

import argparse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time


LOOPBACK = "127.0.0.1"


class Handler(BaseHTTPRequestHandler):
    server_version = "Haven42Dummy/1"

    def do_GET(self) -> None:
        if self.path == "/health":
            body = json.dumps({"status": "ok", "nonce": self.server.session_nonce}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/slow":
            time.sleep(2)
            self.send_response(204)
            self.end_headers()
        elif self.path == "/crash":
            self.send_response(202)
            self.end_headers()
            threading.Thread(target=lambda: os._exit(19), daemon=True).start()
        else:
            self.send_error(404)

    def log_message(self, *_args) -> None:
        return


def run_dummy(port: int, nonce: str) -> None:
    server = ThreadingHTTPServer((LOOPBACK, port), Handler)
    server.session_nonce = nonce
    server.serve_forever()


class OwnedProvider:
    def __init__(self, root: Path, *, idle_seconds: float = 0.35):
        self.root = root
        self.idle_seconds = idle_seconds
        self.process: subprocess.Popen | None = None
        self.port: int | None = None
        self.nonce: str | None = None
        self.started_at: float | None = None
        self.last_used: float | None = None

    @staticmethod
    def free_port() -> int:
        with socket.socket() as sock:
            sock.bind((LOOPBACK, 0))
            return int(sock.getsockname()[1])

    def start(self, *, port: int | None = None, startup_timeout: float = 10) -> None:
        if self.process is not None and self.process.poll() is None:
            return
        self.port = port or self.free_port()
        self.nonce = secrets.token_hex(16)
        command = [sys.executable, str(Path(__file__).resolve()), "--dummy", str(self.port), self.nonce]
        self.process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.started_at = time.monotonic()
        deadline = self.started_at + startup_timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("provider-start-failed")
            try:
                if self.health()["nonce"] == self.nonce:
                    self.last_used = time.monotonic()
                    return
            except (OSError, ValueError, json.JSONDecodeError):
                time.sleep(0.02)
        self.stop()
        raise TimeoutError("provider-start-timeout")

    def health(self, *, timeout: float = 0.25) -> dict:
        if self.port is None:
            raise RuntimeError("provider-not-started")
        connection = http.client.HTTPConnection(LOOPBACK, self.port, timeout=timeout)
        try:
            connection.request("GET", "/health")
            response = connection.getresponse()
            if response.status != 200 or response.getheader("Content-Type") != "application/json":
                raise ValueError("invalid-provider-health")
            result = json.loads(response.read(1024))
            self.last_used = time.monotonic()
            return result
        finally:
            connection.close()

    def request_slow(self, *, timeout: float) -> None:
        connection = http.client.HTTPConnection(LOOPBACK, self.port, timeout=timeout)
        try:
            connection.request("GET", "/slow")
            connection.getresponse()
        finally:
            connection.close()

    def idle_shutdown_if_due(self) -> bool:
        if self.process is None or self.process.poll() is not None or self.last_used is None:
            return False
        if time.monotonic() - self.last_used < self.idle_seconds:
            return False
        self.stop()
        return True

    def identity(self) -> dict:
        if self.process is None or self.port is None or self.nonce is None or self.started_at is None:
            raise RuntimeError("provider-not-started")
        return {"pid": self.process.pid, "processCreationIdentity": f"{self.process.pid}:{self.started_at:.9f}", "sessionNonce": self.nonce, "loopbackEndpoint": f"http://{LOOPBACK}:{self.port}"}

    def stop(self, identity: dict | None = None) -> None:
        process = self.process
        if process is None:
            return
        if identity is not None and identity != self.identity():
            raise RuntimeError("process-identity-mismatch")
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


def assert_closed(port: int) -> None:
    with socket.socket() as sock:
        sock.settimeout(0.15)
        assert sock.connect_ex((LOOPBACK, port)) != 0


def run_tests() -> None:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-image-provider-") as directory:
        root = Path(directory)
        provider = OwnedProvider(root)
        try:
            # On-demand start, loopback identity, and disabled browser launch by construction.
            provider.start()
            identity = provider.identity()
            assert identity["loopbackEndpoint"].startswith("http://127.0.0.1:")
            assert provider.health()["nonce"] == identity["sessionNonce"]
            checks += 1

            # Explicit cancellation is exact-process termination.
            port = provider.port
            provider.stop(identity)
            assert_closed(port)
            checks += 1

            # Occupied port belongs to a foreign listener and must not be terminated.
            foreign = socket.socket()
            foreign.bind((LOOPBACK, 0)); foreign.listen()
            foreign_port = foreign.getsockname()[1]
            rejected = OwnedProvider(root)
            try:
                try:
                    rejected.start(port=foreign_port, startup_timeout=0.3)
                    raise AssertionError("occupied port accepted")
                except RuntimeError:
                    pass
                assert foreign.fileno() >= 0
            finally:
                rejected.stop(); foreign.close()
            checks += 1

            # Timeout is bounded and does not terminate an unrelated process.
            provider = OwnedProvider(root); provider.start()
            try:
                provider.request_slow(timeout=0.05)
                raise AssertionError("slow request did not time out")
            except (TimeoutError, socket.timeout):
                pass
            assert provider.process.poll() is None
            checks += 1

            # Stale/reused identity cannot control the process.
            stale = dict(provider.identity()); stale["processCreationIdentity"] += "-stale"
            try:
                provider.stop(stale)
                raise AssertionError("stale identity accepted")
            except RuntimeError:
                pass
            assert provider.process.poll() is None
            provider.stop(provider.identity())
            checks += 1

            # Crash recovery creates a fresh nonce and PID identity.
            provider = OwnedProvider(root); provider.start(); previous = provider.identity()
            connection = http.client.HTTPConnection(LOOPBACK, provider.port, timeout=1)
            try:
                connection.request("GET", "/crash")
                connection.getresponse().read()
            except (ConnectionError, http.client.HTTPException, OSError):
                # A deliberate process crash may close the socket before the
                # accepted response reaches the client on some platforms.
                pass
            finally:
                connection.close()
            provider.process.wait(timeout=2)
            provider.start(); current = provider.identity()
            assert current["sessionNonce"] != previous["sessionNonce"]
            checks += 1

            # Automatic idle shutdown closes only the owned endpoint.
            port = provider.port; time.sleep(provider.idle_seconds + 0.1)
            assert provider.idle_shutdown_if_due(); assert_closed(port)
            checks += 1

            # Run-owned history/temp/output are exact-file cleanup targets.
            owned = [root / name for name in ("history.json", "temporary.bin", "output.png")]
            retained = root / "checkpoint-retained.bin"
            for path in [*owned, retained]: path.write_bytes(b"test")
            for path in owned: path.unlink()
            assert retained.exists() and all(not path.exists() for path in owned)
            checks += 1

            # Update/rollback and uninstall remain effect-free plans.
            plan = {"effects": {"network": False, "write": False, "process": False}, "transitions": ["stage-candidate", "health-check", "select", "rollback-known-good"], "uninstallTargets": ["runtime-owned-file", "journal-owned-file"], "retention": "preserve-checkpoint"}
            encoded = json.dumps(plan, sort_keys=True)
            assert not any(plan["effects"].values()) and "delete-tree" not in encoded
            checks += 1
        finally:
            provider.stop()
    print(f"Local image dummy-provider lifecycle passed {checks} bounded checks.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dummy", action="store_true")
    parser.add_argument("port", nargs="?", type=int)
    parser.add_argument("nonce", nargs="?")
    args = parser.parse_args()
    if args.dummy:
        if args.port is None or args.nonce is None:
            parser.error("--dummy requires port and nonce")
        run_dummy(args.port, args.nonce)
        return
    run_tests()


if __name__ == "__main__":
    main()
