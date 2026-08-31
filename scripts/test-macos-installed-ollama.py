#!/usr/bin/env python3
"""Fail-closed tests for approval-gated startup of installed macOS Ollama."""

from __future__ import annotations

import importlib.util
import plistlib
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "macos_installed_ollama", ROOT / "scripts/macos_installed_ollama.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def expect_error(code: str, function, *arguments) -> None:
    try:
        function(*arguments)
    except MODULE.MacOSInstalledOllamaError as error:
        assert str(error) == code
    else:
        raise AssertionError(f"expected-{code}")


def make_app(parent: Path, bundle_id: str = MODULE.OLLAMA_BUNDLE_ID) -> Path:
    app = parent / "Ollama.app"
    resources = app / "Contents" / "Resources"
    resources.mkdir(parents=True)
    (resources / "ollama").write_bytes(b"fixed-test-binary")
    (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps({
        "CFBundleIdentifier": bundle_id,
        "CFBundleShortVersionString": "0.33.2",
    }))
    return app


class FakeProcess:
    def __init__(self) -> None:
        self.pid = 424242
        self.finished = False

    def poll(self):
        return 0 if self.finished else None

    def wait(self, timeout=None):
        del timeout
        self.finished = True
        return 0


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-macos-ollama-") as directory:
        app = make_app(Path(directory))
        calls: list[tuple[tuple[str, ...], int]] = []

        def runner(arguments: list[str], timeout: int):
            calls.append((tuple(arguments), timeout))
            if arguments[0] == "/usr/bin/codesign" and "-d" in arguments:
                return 0, (
                    f"Identifier={MODULE.OLLAMA_BUNDLE_ID}\n"
                    f"TeamIdentifier={MODULE.OLLAMA_TEAM_ID}\n"
                )
            if arguments[0] == "/usr/sbin/spctl":
                return 0, "accepted\nsource=Notarized Developer ID\n"
            return 0, "valid on disk\n"

        verified = MODULE.inspect_installed_ollama(app, runner)
        assert verified["status"] == "verified"
        assert verified["version"] == "0.33.2"
        assert verified["signatureVerified"] is True
        assert verified["gatekeeperAccepted"] is True
        assert verified["privatePathsReturned"] is False
        assert verified["binary"] == (app / MODULE.OLLAMA_BINARY_RELATIVE).resolve()
        assert len(calls) == 3 and all(timeout == 15 for _, timeout in calls)
        assert calls[0][0][:5] == (
            "/usr/bin/codesign", "--verify", "--deep", "--strict", "--verbose=2",
        )
        assert calls[1][0][:3] == ("/usr/bin/codesign", "-d", "--verbose=4")
        assert calls[2][0][:5] == (
            "/usr/sbin/spctl", "--assess", "--type", "execute", "--verbose=4",
        )
        checks += 8

        readiness = MODULE.readiness_item(app)
        assert readiness == {
            "componentId": "ollama", "state": "installed-unverified",
            "version": "0.33.2", "source": "registered-app-bundle-probe",
            "confidence": "medium",
        }
        checks += 1

        wrong = make_app(Path(directory) / "wrong", "untrusted.bundle")
        expect_error(
            "macos-ollama-identity-unverified",
            MODULE.inspect_installed_ollama,
            wrong,
            runner,
        )
        missing = MODULE.readiness_item(Path(directory) / "missing.app")
        assert missing["state"] == "not-detected" and missing["version"] is None
        checks += 2

        def bad_publisher(arguments: list[str], timeout: int):
            del timeout
            if "-d" in arguments:
                return 0, f"Identifier={MODULE.OLLAMA_BUNDLE_ID}\nTeamIdentifier=WRONG\n"
            if arguments[0] == "/usr/sbin/spctl":
                return 0, "accepted\n"
            return 0, "valid\n"

        expect_error(
            "macos-ollama-publisher-unverified",
            MODULE.inspect_installed_ollama,
            app,
            bad_publisher,
        )
        checks += 1

        factory_calls: list[dict] = []
        fake_process = FakeProcess()

        def factory(*arguments, **keywords):
            factory_calls.append({"arguments": arguments, "keywords": keywords})
            return fake_process

        coordinator = MODULE.MacOSInstalledOllamaCoordinator(
            "A" * 32,
            app_path=app,
            inspector=lambda path: MODULE.inspect_installed_ollama(path, runner),
            process_factory=factory,
        )
        coordinator._port_available = lambda: True
        coordinator._trusted_user_environment = lambda: {
            "HOME": "/Users/test", "USER": "test", "LOGNAME": "test",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "TMPDIR": "/tmp",
            "OLLAMA_HOST": MODULE.OLLAMA_HOST, "OLLAMA_ORIGINS": "http://127.0.0.1",
            "OLLAMA_NO_CLOUD": "1", "OLLAMA_NOHISTORY": "1",
        }

        def ready(process, timeout=20):
            assert process is fake_process and timeout == 20
            fake_process.finished = True
            return "0.33.2"

        coordinator._wait_ready = ready
        plan = coordinator.register_plan()
        assert plan["approvalRequired"] is True
        assert plan["downloadPerformed"] is False
        assert plan["installationPerformed"] is False
        assert plan["modelDownloadPerformed"] is False
        expect_error(
            "macos-ollama-approval-does-not-match-plan",
            coordinator.approve,
            plan["planId"],
            [],
        )
        token = coordinator.approve(plan["planId"], plan["effects"])
        result = coordinator.start(token)
        assert result["status"] == "started"
        assert result["endpoint"] == MODULE.OLLAMA_URL
        assert result["ownedProcess"] is True and result["approvalConsumed"] is True
        assert result["downloadPerformed"] is False
        assert result["installationPerformed"] is False
        assert result["appBundleChanged"] is False
        assert result["modelDownloadPerformed"] is False
        assert result["persisted"] is False
        assert factory_calls[0]["arguments"][0] == [
            str((app / MODULE.OLLAMA_BINARY_RELATIVE).resolve()), "serve",
        ]
        assert factory_calls[0]["keywords"]["shell"] is False
        assert factory_calls[0]["keywords"]["start_new_session"] is True
        assert coordinator.close() is True
        expect_error("invalid-macos-ollama-approval", coordinator.start, token)
        checks += 17

    print(f"macOS installed Ollama checks passed: {checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
