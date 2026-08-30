#!/usr/bin/env python3
"""Validate one sanitized Haven 42 macOS signing/notarization result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ARCHIVE_NAME = "haven42-darwin-arm64-developer-id-notarized.zip"
EVIDENCE_NAME = "macos-signing-notarization-result.json"
EXPECTED_FILES = {ARCHIVE_NAME, EVIDENCE_NAME, "SHA256SUMS"}
SHA256 = re.compile(r"[0-9a-f]{64}")
UTC_TIMESTAMP = re.compile(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class ValidationError(RuntimeError):
    """Raised when signing evidence is unsafe or inconsistent."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_manifest(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValidationError("checksum-manifest-invalid") from error
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9._-]+)", line)
        if match is None or match.group(2) in parsed:
            raise ValidationError("checksum-manifest-invalid")
        parsed[match.group(2)] = match.group(1)
    return parsed


def validate(directory: Path) -> dict[str, object]:
    require(directory.is_dir() and not directory.is_symlink(), "result-directory-invalid")
    require(
        {path.name for path in directory.iterdir()} == EXPECTED_FILES,
        "unexpected-result-entry",
    )
    archive = directory / ARCHIVE_NAME
    evidence_path = directory / EVIDENCE_NAME
    require(archive.is_file() and not archive.is_symlink(), "artifact-invalid")
    require(evidence_path.is_file() and not evidence_path.is_symlink(), "evidence-invalid")
    try:
        value = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError("evidence-invalid") from error

    require(
        isinstance(value, dict)
        and set(value) == {
            "schemaVersion", "kind", "release", "observedAtUtc", "status",
            "source", "artifact", "platformTrust", "privacy", "authority",
        },
        "evidence-shape-invalid",
    )
    require(
        value["schemaVersion"] == 1
        and value["kind"] == "haven42-sanitized-macos-developer-id-notarization-result"
        and value["release"] == "0.4.0-alpha.2"
        and value["status"] == "passed"
        and isinstance(value["observedAtUtc"], str)
        and UTC_TIMESTAMP.fullmatch(value["observedAtUtc"]) is not None,
        "evidence-identity-invalid",
    )
    artifact = value["artifact"]
    source = value["source"]
    require(
        isinstance(source, dict)
        and set(source) == {
            "unsignedArtifactSha256", "buildEvidenceSha256",
            "appInventoryCanonicalSha256",
        }
        and all(
            isinstance(source[key], str) and SHA256.fullmatch(source[key]) is not None
            for key in source
        ),
        "source-binding-invalid",
    )
    require(
        isinstance(artifact, dict)
        and set(artifact) == {"name", "sha256", "sizeBytes"}
        and artifact["name"] == ARCHIVE_NAME
        and isinstance(artifact["sha256"], str)
        and SHA256.fullmatch(artifact["sha256"]) is not None
        and type(artifact["sizeBytes"]) is int
        and artifact["sizeBytes"] > 0,
        "artifact-record-invalid",
    )
    require(
        artifact["sha256"] == sha256(archive)
        and artifact["sizeBytes"] == archive.stat().st_size,
        "artifact-record-mismatch",
    )
    require(
        value["platformTrust"] == {
            "developerIdSigned": True,
            "hardenedRuntime": True,
            "notarized": True,
            "ticketStapled": True,
            "gatekeeperAdmittedOnTestHost": True,
        },
        "platform-trust-incomplete",
    )
    require(
        value["privacy"] == {
            "certificateIdentityRetained": False,
            "teamIdentifierRetained": False,
            "notaryProfileRetained": False,
            "notaryCredentialRetained": False,
            "rawToolOutputRetained": False,
        },
        "privacy-boundary-invalid",
    )
    require(
        value["authority"] == {
            "automaticUpdateActivationGranted": False,
            "releasePublicationGranted": False,
        },
        "authority-overstated",
    )
    require(
        checksum_manifest(directory / "SHA256SUMS") == {
            ARCHIVE_NAME: sha256(archive),
            EVIDENCE_NAME: sha256(evidence_path),
        },
        "checksum-manifest-mismatch",
    )
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_directory", type=Path)
    args = parser.parse_args()
    try:
        value = validate(args.result_directory.expanduser().resolve())
    except (OSError, ValidationError) as error:
        parser.error(str(error))
    print(json.dumps({
        "artifactSha256": value["artifact"]["sha256"],
        "release": value["release"],
        "status": "passed",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
