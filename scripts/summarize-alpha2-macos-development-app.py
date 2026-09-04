#!/usr/bin/env python3
"""Create sanitized physical-Mac evidence for the unsigned development app."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parent.parent
SUCCESS_MARKER = (
    "Portable package parity, relocation, read-only startup, abrupt-exit recovery, "
    "repeated lifecycle, port collision, shutdown authority, hostile environment, "
    "and integrity tests passed."
)
BROWSER_SUCCESS = re.compile(
    r"Haven 42 headless browser flow passed: ([1-9][0-9]*) checks\."
)
BROWSER_EVIDENCE = (
    "Haven 42 browser evidence gates passed: bounded-attachments, "
    "automated-accessibility, local-privacy-boundary."
)


def load_validator():
    path = ROOT / "scripts" / "validate-macos-development-app.py"
    spec = importlib.util.spec_from_file_location("macos_app_validator_for_summary", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def load_portable_validator():
    path = ROOT / "scripts" / "verify-portable-development-artifacts.py"
    spec = importlib.util.spec_from_file_location("portable_validator_for_app_summary", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PORTABLE_VALIDATOR = load_portable_validator()


class SummaryError(RuntimeError):
    """Raised when the physical app evidence cannot be proven."""


def logical_file_records(root: Path, prefix: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if root.is_file():
        return [{
            "path": prefix,
            "sha256": VALIDATOR.sha256(root),
            "sizeBytes": root.stat().st_size,
        }]
    for current, directories, files in os.walk(root, followlinks=True):
        directories.sort()
        files.sort()
        current_path = Path(current)
        for name in files:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            records.append({
                "path": f"{prefix}/{relative}",
                "sha256": VALIDATOR.sha256(path),
                "sizeBytes": path.stat().st_size,
            })
    return records


def wrapped_package_records(app: Path) -> list[dict[str, object]]:
    records = logical_file_records(app / "Contents" / "MacOS" / "haven42", "haven42")
    frameworks = app / "Contents" / "Frameworks"
    for name in sorted(
        {
            "Python", "Python.framework", "base_library.zip", "config", "examples",
            "libcrypto.3.dylib", "libssl.3.dylib", "libzstd.1.dylib",
            "package", "python3.14", "scripts", "web",
        }
    ):
        records.extend(logical_file_records(frameworks / name, f"_internal/{name}"))
    portable = app / "Contents" / "Resources" / "PortablePackage"
    for name in (
        "DEVELOPMENT-BUILD.txt", "LICENSE.txt", "THIRD-PARTY-NOTICES.txt",
        "licenses",
    ):
        records.extend(logical_file_records(portable / name, name))
    return sorted(records, key=lambda item: str(item["path"]))


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SummaryError("invalid-json-input") from error
    if not isinstance(value, dict):
        raise SummaryError("invalid-json-input")
    return value


def tool(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SummaryError("platform-tool-failed") from error


def summarize(
    artifact_directory: Path,
    portable_artifact_directory: Path,
    hardware_result_path: Path,
    package_test_log: Path,
    browser_test_log: Path | None = None,
) -> dict[str, object]:
    try:
        app_result = VALIDATOR.validate(artifact_directory)
    except VALIDATOR.ValidationError as error:
        raise SummaryError(f"invalid-app-artifact:{error}") from error
    try:
        PORTABLE_VALIDATOR.verify(portable_artifact_directory, "0.4.0-alpha.2")
    except PORTABLE_VALIDATOR.ArtifactVerificationError as error:
        raise SummaryError(f"invalid-portable-artifact:{error}") from error
    provenance = load_json(portable_artifact_directory / "build-provenance.json")
    package_inventory = load_json(
        portable_artifact_directory / "package-file-inventory.json"
    )
    hardware = load_json(hardware_result_path)
    if (
        provenance.get("application") != {
            "name": "Haven 42", "version": app_result["application"]["version"],
        }
        or provenance.get("environment", {}).get("operatingSystem") != "darwin"
        or provenance.get("environment", {}).get("architecture") != "arm64"
        or hardware.get("hardwareProfile") != {
            "profileId": "apple-m4-16gib-macos26-metal",
            "platformFamily": "macos",
            "architecture": "arm64",
            "backend": "metal",
            "systemMemoryGiB": 16,
        }
        or hardware.get("kind")
        != "haven42-apple-silicon-model-qualification-result"
    ):
        raise SummaryError("incompatible-source-or-hardware-evidence")
    package_files = package_inventory.get("files")
    if not isinstance(package_files, list):
        raise SummaryError("invalid-portable-package-inventory")
    app = artifact_directory / "Haven 42.app"
    if wrapped_package_records(app) != package_files:
        raise SummaryError("app-portable-package-parity-mismatch")
    try:
        package_log = package_test_log.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SummaryError("invalid-package-test-log") from error
    if package_log.strip() != SUCCESS_MARKER:
        raise SummaryError("package-test-marker-missing-or-ambiguous")
    browser_checks = 0
    if browser_test_log is not None:
        try:
            browser_log = browser_test_log.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError) as error:
            raise SummaryError("invalid-browser-test-log") from error
        browser_lines = browser_log.splitlines()
        if len(browser_lines) != 2 or browser_lines[0] != BROWSER_EVIDENCE:
            raise SummaryError("browser-evidence-marker-missing-or-ambiguous")
        browser_match = BROWSER_SUCCESS.fullmatch(browser_lines[1])
        if browser_match is None:
            raise SummaryError("browser-test-marker-missing-or-ambiguous")
        browser_checks = int(browser_match.group(1))

    executable = app / "Contents" / "MacOS" / "haven42"
    file_probe = tool(["/usr/bin/file", "-b", str(executable)])
    if file_probe.returncode != 0 or not re.search(
        r"Mach-O 64-bit executable arm64", file_probe.stdout,
    ):
        raise SummaryError("native-arm64-executable-not-proven")
    code_signature = tool(["/usr/bin/codesign", "--verify", "--deep", "--strict", str(app)])
    gatekeeper = tool(["/usr/sbin/spctl", "--assess", "--type", "execute", str(app)])
    archive = artifact_directory / VALIDATOR.ARCHIVE_NAME
    portable_archives = [
        path for path in portable_artifact_directory.iterdir()
        if path.is_file() and (path.name.endswith(".zip") or path.name.endswith(".tar.gz"))
    ]
    if len(portable_archives) != 1:
        raise SummaryError("portable-archive-identity-ambiguous")
    inventory = app_result["inventory"]
    return {
        "schemaVersion": 1,
        "kind": "haven42-sanitized-physical-macos-development-app-result",
        "release": app_result["application"]["version"],
        "observedAtUtc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "partial-pass",
        "hardwareProfile": hardware["hardwareProfile"],
        "source": provenance["source"],
        "app": {
            "bundleIdentifier": app_result["application"]["bundleIdentifier"],
            "bundleShortVersion": app_result["application"]["bundleShortVersion"],
            "bundleVersion": app_result["application"]["bundleVersion"],
            "minimumSystemVersion": app_result["application"]["minimumSystemVersion"],
            "archiveSha256": VALIDATOR.sha256(archive),
            "portablePackageArchiveSha256": VALIDATOR.sha256(portable_archives[0]),
            "portableBuildProvenanceSha256": VALIDATOR.sha256(
                portable_artifact_directory / "build-provenance.json"
            ),
            "inventoryCanonicalSha256": inventory["canonicalSha256"],
            "fileCount": inventory["fileCount"],
            "nativeArchitecture": "arm64",
            "globalPythonRequired": False,
        },
        "tests": {
            "bundleStructure": True,
            "infoPlistIdentity": True,
            "exactFileInventory": True,
            "archiveParity": True,
            "archiveChecksums": True,
            "nativeArm64Executable": True,
            "sourcePackageParity": True,
            "relocation": True,
            "readOnlyStartup": True,
            "abruptExitRecovery": True,
            "repeatedLifecycle": True,
            "occupiedPortRefusal": True,
            "shutdownAuthority": True,
            "hostileEnvironment": True,
            "resourceIntegrity": True,
            "packagedBrowserFlow": browser_checks > 0,
            "packagedBrowserChecks": browser_checks,
            "boundedAttachmentFlow": browser_checks > 0,
            "automatedAccessibilityFlow": browser_checks > 0,
            "localPrivacyBoundary": browser_checks > 0,
        },
        "platformTrust": {
            "codeSignatureStructureValid": code_signature.returncode == 0,
            "developerIdSigned": False,
            "notarized": False,
            "gatekeeperAdmittedOnTestHost": gatekeeper.returncode == 0,
            "publicDistributionAllowed": False,
        },
        "open": [
            "developer-id-signing", "notarization", "gatekeeper-public-admission",
            "clean-machine-beginner-review", "manual-screen-reader",
            "manual-keyboard", "manual-zoom", "manual-reduced-motion",
        ] + ([] if browser_checks else ["packaged-real-browser-flow"]),
        "authority": {
            "releasePublicationAllowed": False,
            "automaticUpdateAllowed": False,
            "productionAdmissionGranted": False,
        },
        "privacy": {
            "privateIdentityRetained": False,
            "privatePathsRetained": False,
            "rawUserContentRetained": False,
            "rawToolOutputRetained": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-directory", required=True)
    parser.add_argument("--portable-artifact-directory", required=True)
    parser.add_argument("--hardware-result", required=True)
    parser.add_argument("--package-test-log", required=True)
    parser.add_argument("--browser-test-log")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = summarize(
            Path(args.artifact_directory).resolve(),
            Path(args.portable_artifact_directory).resolve(),
            Path(args.hardware_result).resolve(),
            Path(args.package_test_log).resolve(),
            Path(args.browser_test_log).resolve() if args.browser_test_log else None,
        )
    except SummaryError as error:
        parser.error(str(error))
    output = Path(args.output).resolve()
    if output.exists() or output.is_symlink():
        parser.error("output-already-exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
