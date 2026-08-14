#!/usr/bin/env python3
"""Assemble a local, unsigned, non-distributable Windows Alpha test packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.4.0-alpha.1"
ARCHIVE_NAME = f"haven42-{VERSION}-windows-x64-unsigned.zip"
ISSUE_ARCHIVE = re.compile(
    rf"^haven42-{re.escape(VERSION)}-issue([1-9][0-9]{{0,5}})-test([1-9][0-9]{{0,2}})-windows-x64-unsigned\.zip$"
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_EVIDENCE = {
    "APACHE-2.0.txt", "CPYTHON-3.14.6-LICENSE.txt", "LIBFFI-3.4.4-LICENSE.txt",
    "OLLAMA-MIT-LICENSE.txt",
    "THIRD-PARTY-NOTICES.txt", "build-provenance.json", "dependency-inventory.json",
    "haven42.cdx.json", "package-file-inventory.json", "runtime-component-inventory.json",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def build(portable_root: Path, output: Path) -> dict:
    if platform.system() != "Windows" or platform.machine().casefold() not in {"amd64", "x86_64"}:
        raise ValueError("windows-x64-required")
    source_artifacts = portable_root / "artifacts"
    archives = list(source_artifacts.glob("haven42-windows-amd64-unsigned-development.zip"))
    if len(archives) != 1:
        raise ValueError("exact-portable-archive-required")
    missing = sorted(name for name in REQUIRED_EVIDENCE if not (source_artifacts / name).is_file())
    if missing:
        raise ValueError("candidate-evidence-incomplete")
    provenance = json.loads((source_artifacts / "build-provenance.json").read_text(encoding="utf-8"))
    if (
        provenance.get("application") != {"name": "Haven 42", "version": VERSION}
        or provenance.get("security", {}).get("signed") is not False
        or provenance.get("security", {}).get("releasePublished") is not False
    ):
        raise ValueError("candidate-provenance-mismatch")
    output.mkdir(parents=True, exist_ok=True)
    candidate = output / ARCHIVE_NAME
    if candidate.exists():
        candidate.unlink()
    shutil.copy2(archives[0], candidate)
    for name in sorted(REQUIRED_EVIDENCE):
        shutil.copy2(source_artifacts / name, output / name)
    sha = digest(candidate)
    manifest = {
        "schemaVersion": 1,
        "kind": "unsigned-windows-private-alpha-test-packet",
        "version": VERSION,
        "platform": "windows-x64",
        "archive": {"name": ARCHIVE_NAME, "sizeBytes": candidate.stat().st_size, "sha256": sha},
        "sourceCommit": provenance["source"]["commit"],
        "exactSourceCommit": provenance["source"]["commitIsExactSource"],
        "treeState": provenance["source"]["treeState"],
        "signed": False,
        "publicReleaseAllowed": False,
        "distributionAuthorized": False,
        "productionReady": False,
        "testerReviewRequired": True,
    }
    (output / "candidate-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    (output / f"{ARCHIVE_NAME}.sha256").write_text(f"{sha}  {ARCHIVE_NAME}\n", encoding="ascii")
    return manifest


def build_issue_verification(
    portable_root: Path,
    output: Path,
    issue_number: int,
    iteration: int,
) -> dict:
    """Build one explicitly authorized, unsigned issue-verification packet."""
    if (
        isinstance(issue_number, bool)
        or not isinstance(issue_number, int)
        or not 1 <= issue_number <= 999999
        or isinstance(iteration, bool)
        or not isinstance(iteration, int)
        or not 1 <= iteration <= 999
    ):
        raise ValueError("invalid-issue-verification-identity")
    provenance = json.loads(
        (portable_root / "artifacts" / "build-provenance.json").read_text(encoding="utf-8")
    )
    source = provenance.get("source", {})
    if (
        source.get("commitIsExactSource") is not True
        or source.get("treeState") != "clean"
        or not FULL_COMMIT.fullmatch(str(source.get("commit", "")))
    ):
        raise ValueError("issue-verification-requires-clean-exact-source")
    manifest = build(portable_root, output)
    original = output / ARCHIVE_NAME
    archive_name = (
        f"haven42-{VERSION}-issue{issue_number}-test{iteration}-"
        "windows-x64-unsigned.zip"
    )
    archive = output / archive_name
    original.replace(archive)
    (output / f"{ARCHIVE_NAME}.sha256").unlink()
    manifest.update({
        "kind": "unsigned-windows-issue-verification-packet",
        "issueNumber": issue_number,
        "iteration": iteration,
        "publicReleaseAllowed": True,
        "distributionAuthorized": True,
    })
    manifest["archive"]["name"] = archive_name
    (output / "candidate-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    (output / f"{archive_name}.sha256").write_text(
        f"{manifest['archive']['sha256']}  {archive_name}\n", encoding="ascii",
    )
    return manifest


def verify(output: Path) -> dict:
    manifest = json.loads((output / "candidate-manifest.json").read_text(encoding="utf-8"))
    private_keys = {
        "schemaVersion", "kind", "version", "platform", "archive", "sourceCommit",
        "exactSourceCommit", "treeState", "signed", "publicReleaseAllowed",
        "distributionAuthorized", "productionReady", "testerReviewRequired",
    }
    issue_keys = private_keys | {"issueNumber", "iteration"}
    manifest_keys = frozenset(manifest)
    if manifest_keys not in {frozenset(private_keys), frozenset(issue_keys)} or manifest["schemaVersion"] != 1:
        raise ValueError("invalid-candidate-manifest")
    is_issue_verification = manifest["kind"] == "unsigned-windows-issue-verification-packet"
    archive_name = manifest.get("archive", {}).get("name")
    if (
        manifest["version"] != VERSION
        or not isinstance(archive_name, str)
        or not FULL_COMMIT.fullmatch(str(manifest.get("sourceCommit", "")))
    ):
        raise ValueError("invalid-candidate-identity")
    if is_issue_verification:
        match = ISSUE_ARCHIVE.fullmatch(archive_name)
        if (
            set(manifest) != issue_keys
            or not match
            or manifest["issueNumber"] != int(match.group(1))
            or manifest["iteration"] != int(match.group(2))
            or manifest["exactSourceCommit"] is not True
            or manifest["treeState"] != "clean"
            or manifest["signed"] is not False
            or manifest["publicReleaseAllowed"] is not True
            or manifest["distributionAuthorized"] is not True
            or manifest["productionReady"] is not False
            or manifest["testerReviewRequired"] is not True
        ):
            raise ValueError("issue-verification-authority-invalid")
    elif (
        manifest["kind"] != "unsigned-windows-private-alpha-test-packet"
        or archive_name != ARCHIVE_NAME
        or any(manifest[key] is not False for key in (
            "signed", "publicReleaseAllowed", "distributionAuthorized", "productionReady",
        ))
        or manifest["testerReviewRequired"] is not True
    ):
        raise ValueError("candidate-authority-broadened")
    archive = output / archive_name
    if (
        not archive.is_file() or archive.is_symlink()
        or archive.stat().st_size != manifest["archive"]["sizeBytes"]
        or not SHA256.fullmatch(manifest["archive"]["sha256"])
        or digest(archive) != manifest["archive"]["sha256"]
    ):
        raise ValueError("candidate-archive-integrity-failed")
    checksum = (output / f"{archive_name}.sha256").read_text(encoding="ascii")
    if checksum != f"{manifest['archive']['sha256']}  {archive_name}\n":
        raise ValueError("candidate-checksum-mismatch")
    if any(not (output / name).is_file() for name in REQUIRED_EVIDENCE):
        raise ValueError("candidate-evidence-incomplete")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portable-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--issue-verification", type=int)
    parser.add_argument("--iteration", type=int, default=1)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if args.verify_only:
        result = verify(output)
    elif args.issue_verification is not None:
        result = build_issue_verification(
            Path(args.portable_root).resolve(), output,
            args.issue_verification, args.iteration,
        )
    else:
        result = build(Path(args.portable_root).resolve(), output)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
