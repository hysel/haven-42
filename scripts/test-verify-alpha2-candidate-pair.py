#!/usr/bin/env python3
"""Effect-free hostile tests for cross-platform Alpha 2 candidate pairing."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "alpha2_candidate_pair",
    ROOT / "scripts" / "verify-alpha2-candidate-pair.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(call, expected: str) -> None:
    try:
        call()
    except ValueError as error:
        assert str(error) == expected, (str(error), expected)
        return
    raise AssertionError(f"unsafe candidate pair accepted: {expected}")


def candidate(directory: Path, builder, platform: str, commit: str) -> None:
    directory.mkdir(parents=True)
    for name in builder.CANDIDATE_EVIDENCE:
        (directory / name).write_text(f"{name}\n", encoding="utf-8")
    archive = directory / builder.ARCHIVE_NAME
    archive.write_bytes(f"{platform}-candidate".encode("ascii"))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    limitations = directory / builder.KNOWN_LIMITATIONS_NAME
    limitations_digest = hashlib.sha256(limitations.read_bytes()).hexdigest()
    manifest = {
        "schemaVersion": 1,
        "kind": f"unsigned-{platform.split('-')[0]}-alpha2-release-candidate",
        "version": builder.VERSION,
        "platform": platform,
        "archive": {
            "name": builder.ARCHIVE_NAME,
            "sizeBytes": archive.stat().st_size,
            "sha256": digest,
        },
        "knownLimitations": {
            "name": builder.KNOWN_LIMITATIONS_NAME,
            "sha256": limitations_digest,
        },
        "sourceCommit": commit,
        "exactSourceCommit": True,
        "treeState": "exact-commit",
        "signed": False,
        "publicReleaseAllowed": False,
        "distributionAuthorized": False,
        "productionReady": False,
        "nativeValidationRequired": True,
        "alpha1AssetsMayBeModified": False,
    }
    (directory / "candidate-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    (directory / f"{builder.ARCHIVE_NAME}.sha256").write_text(
        f"{digest}  {builder.ARCHIVE_NAME}\n", encoding="ascii"
    )


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-alpha2-pair-") as temporary:
        root = Path(temporary)
        commit = "a" * 40
        windows = root / "windows"
        linux = root / "linux"
        candidate(windows, MODULE.WINDOWS, "windows-x64", commit)
        candidate(linux, MODULE.LINUX, "linux-x64", commit)
        report = MODULE.verify_pair(windows, linux, commit)
        assert report["sourceCommit"] == commit
        assert report["sameSourceCommit"] is True
        assert report["candidatePairReadyForNativeValidation"] is True
        assert report["nativeValidationComplete"] is False
        assert report["publicationAllowed"] is False
        assert report["productionReady"] is False
        checks += 6

        refused(
            lambda: MODULE.verify_pair(windows, linux, "b" * 40),
            "candidate-unexpected-source-commit",
        )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-alpha2-pair-mismatch-") as temporary:
        root = Path(temporary)
        windows = root / "windows"
        linux = root / "linux"
        candidate(windows, MODULE.WINDOWS, "windows-x64", "a" * 40)
        candidate(linux, MODULE.LINUX, "linux-x64", "b" * 40)
        refused(
            lambda: MODULE.verify_pair(windows, linux),
            "candidate-source-commit-mismatch",
        )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-alpha2-pair-limitations-") as temporary:
        root = Path(temporary)
        windows = root / "windows"
        linux = root / "linux"
        candidate(windows, MODULE.WINDOWS, "windows-x64", "a" * 40)
        candidate(linux, MODULE.LINUX, "linux-x64", "a" * 40)
        limitations = linux / MODULE.LINUX.KNOWN_LIMITATIONS_NAME
        limitations.write_text("different limitations\n", encoding="utf-8")
        manifest_path = linux / "candidate-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["knownLimitations"]["sha256"] = hashlib.sha256(
            limitations.read_bytes()
        ).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        refused(
            lambda: MODULE.verify_pair(windows, linux),
            "candidate-known-limitations-mismatch",
        )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-alpha2-pair-authority-") as temporary:
        root = Path(temporary)
        windows = root / "windows"
        linux = root / "linux"
        candidate(windows, MODULE.WINDOWS, "windows-x64", "a" * 40)
        candidate(linux, MODULE.LINUX, "linux-x64", "a" * 40)
        manifest_path = linux / "candidate-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["publicReleaseAllowed"] = True
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        refused(
            lambda: MODULE.verify_pair(windows, linux),
            "candidate-authority-invalid",
        )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-alpha2-pair-output-") as temporary:
        refused(
            lambda: MODULE.safe_output(str(Path(temporary) / "report.json")),
            "output-must-remain-inside-repository",
        )
        checks += 1

    print(f"Alpha 2 candidate pair verification passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
