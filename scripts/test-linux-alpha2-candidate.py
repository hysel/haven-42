#!/usr/bin/env python3
"""Effect-free tests for the isolated Linux Alpha 2 candidate assembler."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "linux_alpha2_candidate",
    ROOT / "scripts" / "build-linux-alpha2-candidate.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def refused(call, expected: str) -> None:
    try:
        call()
    except ValueError as error:
        assert str(error) == expected, (str(error), expected)
    else:
        raise AssertionError(f"Candidate operation unexpectedly accepted: {expected}")


def fixture(root: Path, version: str = MODULE.VERSION) -> Path:
    portable = root / "portable"
    artifacts = portable / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / MODULE.PORTABLE_ARCHIVE).write_bytes(b"linux-alpha2-candidate")
    for name in MODULE.REQUIRED_EVIDENCE:
        (artifacts / name).write_text("evidence\n", encoding="utf-8")
    provenance = {
        "application": {"name": "Haven 42", "version": version},
        "environment": {"operatingSystem": "linux", "architecture": "x86_64"},
        "security": {"signed": False, "releasePublished": False},
        "source": {
            "commit": "2" * 40,
            "commitIsExactSource": True,
            "treeState": "exact-commit",
        },
    }
    (artifacts / "build-provenance.json").write_text(
        json.dumps(provenance), encoding="utf-8"
    )
    return portable


def rewrite_provenance(portable: Path, **source_changes: object) -> None:
    path = portable / "artifacts" / "build-provenance.json"
    provenance = json.loads(path.read_text(encoding="utf-8"))
    provenance["source"].update(source_changes)
    path.write_text(json.dumps(provenance), encoding="utf-8")


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="haven42-linux-alpha2-candidate-") as temporary:
        root = Path(temporary)
        portable = fixture(root)
        output = root / "candidate"
        with (
            patch.object(MODULE.platform, "system", return_value="Linux"),
            patch.object(MODULE.platform, "machine", return_value="x86_64"),
        ):
            manifest = MODULE.build(portable, output)
        assert manifest["version"] == MODULE.VERSION
        assert manifest["archive"]["name"] == MODULE.ARCHIVE_NAME
        assert manifest["platform"] == "linux-x64"
        assert manifest["alpha1AssetsMayBeModified"] is False
        assert manifest["publicReleaseAllowed"] is False
        assert MODULE.verify(output) == manifest
        checks += 6

        archive = output / MODULE.ARCHIVE_NAME
        archive.write_bytes(b"tampered")
        refused(lambda: MODULE.verify(output), "candidate-archive-integrity-failed")
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-linux-alpha2-wrong-version-") as temporary:
        root = Path(temporary)
        portable = fixture(root, "0.4.0-alpha.1")
        with (
            patch.object(MODULE.platform, "system", return_value="Linux"),
            patch.object(MODULE.platform, "machine", return_value="x86_64"),
        ):
            refused(
                lambda: MODULE.build(portable, root / "candidate"),
                "candidate-provenance-mismatch",
            )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-linux-alpha2-wrong-host-") as temporary:
        root = Path(temporary)
        portable = fixture(root)
        with patch.object(MODULE.platform, "system", return_value="Windows"):
            refused(
                lambda: MODULE.build(portable, root / "candidate"),
                "linux-x64-required",
            )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-linux-alpha2-dirty-source-") as temporary:
        root = Path(temporary)
        portable = fixture(root)
        rewrite_provenance(
            portable,
            commitIsExactSource=False,
            treeState="modified-uncommitted",
        )
        with (
            patch.object(MODULE.platform, "system", return_value="Linux"),
            patch.object(MODULE.platform, "machine", return_value="x86_64"),
        ):
            refused(
                lambda: MODULE.build(portable, root / "candidate"),
                "candidate-provenance-mismatch",
            )
        checks += 1

    with tempfile.TemporaryDirectory(prefix="haven42-linux-alpha2-manifest-source-") as temporary:
        root = Path(temporary)
        portable = fixture(root)
        output = root / "candidate"
        with (
            patch.object(MODULE.platform, "system", return_value="Linux"),
            patch.object(MODULE.platform, "machine", return_value="x86_64"),
        ):
            MODULE.build(portable, output)
        manifest_path = output / "candidate-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["exactSourceCommit"] = False
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        refused(lambda: MODULE.verify(output), "candidate-authority-invalid")
        checks += 1

    print(f"Linux Alpha 2 candidate isolation passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
