#!/usr/bin/env python3
"""Inventory an extracted image runtime without executing or importing it."""

from __future__ import annotations

import argparse
import base64
from collections import Counter
import csv
from email.parser import BytesParser
from email.policy import compat32
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config" / "local-image-runtime-license-contract.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9.-]{2,79}$")
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+ -]{0,199}$")
WINDOWS_RESERVED_NAME = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE
)
LICENSE_OVERRIDE_ID = re.compile(
    r"^[a-z0-9][a-z0-9._+-]{0,199}@[A-Za-z0-9][A-Za-z0-9._+-]{0,99}$"
)
LIMIT_CEILINGS = {
    "maxFiles": 500_000,
    "maxDepth": 64,
    "maxMetadataBytes": 8 * 1024 * 1024,
    "maxRecordBytes": 32 * 1024 * 1024,
    "maxRecordRowsPerDistribution": 500_000,
    "maxLicenseBytes": 8 * 1024 * 1024,
    "maxGlobalLicenseBytes": 64 * 1024 * 1024,
    "maxLicenseFilesPerDistribution": 128,
    "maxGlobalLicenseFiles": 4096,
    "maxNativeBasenames": 8192,
}


class AuditError(ValueError):
    pass


def reject_duplicate_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise AuditError("duplicate-contract-key")
        value[key] = item
    return value


def load_json(path: Path) -> dict:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuditError("invalid-contract") from error
    if not isinstance(value, dict):
        raise AuditError("invalid-contract")
    return value


def validate_contract(contract: dict) -> None:
    if contract.get("schemaVersion") != 1:
        raise AuditError("unsupported-contract-schema")
    limits = contract.get("limits")
    if not isinstance(limits, dict):
        raise AuditError("invalid-contract-limits")
    for name, ceiling in LIMIT_CEILINGS.items():
        value = limits.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= ceiling:
            raise AuditError("invalid-contract-limits")
    for name in ("nativeSuffixes", "licenseBasenamePrefixes", "mandatoryBlockers", "prohibitions"):
        values = contract.get(name)
        if not isinstance(values, list) or not values or len(values) > 64:
            raise AuditError("invalid-contract-list")
        if any(not isinstance(value, str) or not value or len(value) > 100 for value in values):
            raise AuditError("invalid-contract-list")
    profiles = contract.get("profiles")
    if not isinstance(profiles, dict) or not profiles or len(profiles) > 32:
        raise AuditError("invalid-contract-profiles")
    for profile_id, profile in profiles.items():
        if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
            raise AuditError("invalid-contract-profile")
        if not isinstance(profile, dict) or not SHA256.fullmatch(str(profile.get("archiveSha256", ""))):
            raise AuditError("invalid-contract-profile")
        for field in ("operatingSystem", "accelerator", "provider", "providerVersion", "embeddedRuntime"):
            if clean_field(profile.get(field)) is None:
                raise AuditError("invalid-contract-profile")
    overrides = contract.get("reviewedDistributionLicenses", {})
    if not isinstance(overrides, dict) or len(overrides) > 256:
        raise AuditError("invalid-license-overrides")
    for identity, override in overrides.items():
        if not isinstance(identity, str) or not LICENSE_OVERRIDE_ID.fullmatch(identity):
            raise AuditError("invalid-license-overrides")
        if not isinstance(override, dict):
            raise AuditError("invalid-license-overrides")
        if clean_field(override.get("licenseExpression")) is None:
            raise AuditError("invalid-license-overrides")
        if not SHA256.fullmatch(str(override.get("packagedLicenseSha256", ""))):
            raise AuditError("invalid-license-overrides")
        if clean_field(override.get("reviewStatus")) is None:
            raise AuditError("invalid-license-overrides")


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_field(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    if not cleaned or len(cleaned) > 500 or any(ord(char) < 32 for char in cleaned):
        return None
    return cleaned


def normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def safe_name(value: str) -> bool:
    return bool(
        SAFE_NAME.fullmatch(value)
        and value not in {".", ".."}
        and not value.endswith((".", " "))
        and not WINDOWS_RESERVED_NAME.fullmatch(value)
    )


def is_link_or_reparse(path: Path, info: os.stat_result) -> bool:
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or stat.S_ISLNK(info.st_mode) or bool(attributes & reparse_flag)


def runtime_filesystem_root(path: Path) -> Path:
    """Use Win32 extended-length syntax without changing the recorded path boundary."""
    if os.name != "nt":
        return path
    value = str(path)
    if value.startswith("\\\\?\\"):
        return path
    if value.startswith("\\\\"):
        return Path("\\\\?\\UNC\\" + value[2:])
    return Path("\\\\?\\" + value)


def walk_regular_files(root: Path, limits: dict) -> tuple[list[Path], list[Path]]:
    files: list[Path] = []
    directories: list[Path] = []
    stack = [(root, 0)]
    while stack:
        directory, depth = stack.pop()
        if depth > limits["maxDepth"]:
            raise AuditError("maximum-depth-exceeded")
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name.casefold())
        except OSError as error:
            raise AuditError("runtime-read-failed") from error
        for entry in entries:
            path = Path(entry.path)
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as error:
                raise AuditError("runtime-read-failed") from error
            if is_link_or_reparse(path, info):
                raise AuditError("link-entry-rejected")
            if stat.S_ISDIR(info.st_mode):
                directories.append(path)
                stack.append((path, depth + 1))
            elif stat.S_ISREG(info.st_mode):
                files.append(path)
                if len(files) > limits["maxFiles"]:
                    raise AuditError("maximum-file-count-exceeded")
            else:
                raise AuditError("non-regular-entry-rejected")
    return files, directories


def safe_relative(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    if len(relative.parts) > 24 or any(not safe_name(part) for part in relative.parts):
        return "redacted-unsafe-name/" + hashlib.sha256(str(relative).encode("utf-8")).hexdigest()
    value = relative.as_posix()
    if len(value) > 1000:
        return "redacted-long-name/" + hashlib.sha256(value.encode("utf-8")).hexdigest()
    return value


def is_contracted_embedded_runtime_path(relative_parts: tuple[str, ...]) -> bool:
    """Recognize only the two admitted extraction-root shapes for embedded CPython."""
    if len(relative_parts) >= 2 and relative_parts[0] == "python_embeded":
        return True
    return (
        len(relative_parts) >= 3
        and relative_parts[:2] == ("ComfyUI_windows_portable", "python_embeded")
    )


def reject_case_collisions(paths: list[Path], root: Path) -> None:
    casefold_paths: dict[str, str] = {}
    for path in paths:
        relative = path.relative_to(root).as_posix()
        key = relative.casefold()
        if key in casefold_paths and casefold_paths[key] != relative:
            raise AuditError("case-collision-rejected")
        casefold_paths[key] = relative


def license_files(dist_info: Path, files_by_parent: dict[Path, list[Path]], contract: dict) -> list[dict]:
    limits = contract["limits"]
    prefixes = tuple(item.casefold() for item in contract["licenseBasenamePrefixes"])
    matches: list[Path] = []
    for parent, paths in files_by_parent.items():
        try:
            parent.relative_to(dist_info)
        except ValueError:
            continue
        for path in paths:
            if path.name.casefold().startswith(prefixes):
                matches.append(path)
    if len(matches) > limits["maxLicenseFilesPerDistribution"]:
        raise AuditError("maximum-license-file-count-exceeded")
    evidence = []
    for path in sorted(matches, key=lambda item: str(item).casefold()):
        size = path.stat(follow_symlinks=False).st_size
        if size > limits["maxLicenseBytes"]:
            raise AuditError("maximum-license-size-exceeded")
        name = path.name if safe_name(path.name) else "redacted-unsafe-name"
        evidence.append({"name": name, "bytes": size, "sha256": digest_file(path)})
    return evidence


def distribution_scope(metadata_path: Path) -> str:
    site_packages = next(
        (parent for parent in metadata_path.parents if parent.name.casefold() == "site-packages"),
        None,
    )
    if site_packages is None:
        return "embedded"
    relative = metadata_path.parent.relative_to(site_packages)
    if len(relative.parts) == 1:
        return "top-level"
    owner = relative.parts[0]
    return f"vendored/{owner}" if safe_name(owner) else "vendored/redacted"


def distribution_record(metadata_path: Path, evidence: list[dict], max_bytes: int) -> dict:
    size = metadata_path.stat(follow_symlinks=False).st_size
    if size > max_bytes:
        raise AuditError("maximum-metadata-size-exceeded")
    try:
        message = BytesParser(policy=compat32).parsebytes(metadata_path.read_bytes(), headersonly=True)
    except (OSError, ValueError) as error:
        raise AuditError("invalid-distribution-metadata") from error
    for field in ("Name", "Version", "License-Expression", "License"):
        if len(message.get_all(field, [])) > 1:
            raise AuditError("ambiguous-distribution-metadata")
    name = clean_field(message.get("Name"))
    version = clean_field(message.get("Version"))
    if name is None or version is None:
        raise AuditError("incomplete-distribution-identity")
    expression = clean_field(message.get("License-Expression"))
    legacy = clean_field(message.get("License"))
    classifiers = sorted(
        cleaned
        for value in message.get_all("Classifier", [])
        if (cleaned := clean_field(value)) and cleaned.startswith("License ::")
    )
    declared = expression or legacy or ("; ".join(classifiers) if classifiers else None)
    blockers = []
    if declared is None:
        blockers.append("license-metadata-missing")
    if not evidence:
        blockers.append("license-evidence-missing")
    return {
        "name": name,
        "normalizedName": normalized_name(name),
        "version": version,
        "installationScope": distribution_scope(metadata_path),
        "licenseExpression": expression,
        "legacyLicense": legacy,
        "licenseClassifiers": classifiers,
        "licenseEvidence": evidence,
        "blockers": blockers,
    }


def record_path_parts(value: str, *, allow_windows_separators: bool) -> tuple[str, ...]:
    if not value or "\x00" in value or any(ord(char) < 32 for char in value):
        raise AuditError("invalid-record-row")
    if allow_windows_separators and ":" in value:
        raise AuditError("invalid-record-row")
    if "\\" in value:
        if (
            not allow_windows_separators
            or "/" in value
            or value.startswith("\\")
            or "\\\\" in value
        ):
            raise AuditError("invalid-record-row")
        value = value.replace("\\", "/")
        raw_parts = value.split("/")
        if any(part in {"", ".", ".."} for part in raw_parts):
            raise AuditError("invalid-record-row")
    return PurePosixPath(value).parts


def record_native_claims(
    dist_info: Path,
    distribution: dict,
    runtime_root: Path,
    native_suffixes: set[str],
    limits: dict,
    *,
    allow_windows_separators: bool,
) -> dict[Path, dict]:
    record = dist_info / "RECORD"
    if not record.is_file():
        return {}
    size = record.stat(follow_symlinks=False).st_size
    if size > limits["maxRecordBytes"]:
        raise AuditError("maximum-record-size-exceeded")
    claims: dict[Path, dict] = {}
    try:
        with record.open("r", encoding="utf-8", newline="") as stream:
            for index, row in enumerate(csv.reader(stream), 1):
                if index > limits["maxRecordRowsPerDistribution"]:
                    raise AuditError("maximum-record-row-count-exceeded")
                if len(row) != 3:
                    raise AuditError("invalid-record-row")
                parts = record_path_parts(
                    row[0], allow_windows_separators=allow_windows_separators
                )
                candidate = (dist_info.parent / Path(*parts)).resolve(strict=False)
                try:
                    candidate.relative_to(runtime_root)
                except ValueError as error:
                    raise AuditError("record-path-escape") from error
                if candidate.suffix.casefold() not in native_suffixes:
                    continue
                recorded_sha = None
                if row[1]:
                    if not row[1].startswith("sha256="):
                        raise AuditError("unsupported-record-hash")
                    encoded = row[1].split("=", 1)[1]
                    try:
                        decoded = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
                    except (ValueError, TypeError) as error:
                        raise AuditError("invalid-record-hash") from error
                    if len(decoded) != 32:
                        raise AuditError("invalid-record-hash")
                    recorded_sha = decoded.hex()
                claims[candidate] = {
                    "distribution": distribution["name"],
                    "version": distribution["version"],
                    "recordSha256": recorded_sha,
                }
    except (OSError, UnicodeError, csv.Error) as error:
        raise AuditError("invalid-distribution-record") from error
    return claims


def audit(args: argparse.Namespace) -> dict:
    contract = load_json(args.contract)
    validate_contract(contract)
    profile = contract.get("profiles", {}).get(args.profile)
    if profile is None or not PROFILE_ID.fullmatch(args.profile):
        raise AuditError("unknown-profile")
    artifact_sha = args.artifact_sha256.lower()
    if not SHA256.fullmatch(artifact_sha) or artifact_sha != profile.get("archiveSha256"):
        raise AuditError("artifact-digest-not-contracted")

    resolved_root = args.runtime.resolve(strict=True)
    root_info = args.runtime.stat(follow_symlinks=False)
    if not resolved_root.is_dir() or is_link_or_reparse(args.runtime, root_info):
        raise AuditError("invalid-runtime-root")
    root = runtime_filesystem_root(resolved_root)
    output = args.output.resolve(strict=False)
    if output.exists():
        raise AuditError("output-already-exists")
    if not safe_name(args.output.name):
        raise AuditError("invalid-output-name")
    output_parent = args.output.parent
    if not output_parent.is_dir():
        raise AuditError("invalid-output-parent")
    output_parent_info = output_parent.stat(follow_symlinks=False)
    if is_link_or_reparse(output_parent, output_parent_info):
        raise AuditError("output-parent-link-rejected")
    if os.path.normcase(str(output_parent.resolve())) != os.path.normcase(str(output_parent.absolute())):
        raise AuditError("output-parent-redirect-rejected")
    try:
        output.relative_to(resolved_root)
    except ValueError:
        pass
    else:
        raise AuditError("output-inside-runtime-rejected")

    archive_verified = False
    if args.archive is not None:
        archive = args.archive.resolve(strict=True)
        archive_info = args.archive.stat(follow_symlinks=False)
        if not archive.is_file() or is_link_or_reparse(args.archive, archive_info):
            raise AuditError("invalid-archive")
        if digest_file(archive) != artifact_sha:
            raise AuditError("archive-digest-mismatch")
        archive_verified = True

    files, directories = walk_regular_files(root, contract["limits"])
    reject_case_collisions(files + directories, root)
    by_parent: dict[Path, list[Path]] = {}
    for path in files:
        by_parent.setdefault(path.parent, []).append(path)
    metadata = [path for path in files if path.name == "METADATA" and path.parent.name.endswith(".dist-info")]
    dist_directories = [path for path in directories if path.name.endswith(".dist-info")]
    missing_metadata = sorted(
        safe_relative(path, root)
        for path in dist_directories
        if not (path / "METADATA").is_file()
    )
    distributions = []
    distribution_paths = []
    for path in sorted(metadata, key=lambda item: str(item).casefold()):
        evidence = license_files(path.parent, by_parent, contract)
        distribution = distribution_record(path, evidence, contract["limits"]["maxMetadataBytes"])
        identity = f'{distribution["normalizedName"]}@{distribution["version"]}'
        override = contract.get("reviewedDistributionLicenses", {}).get(identity)
        if override is not None:
            evidence_hashes = {item["sha256"] for item in evidence}
            if override["packagedLicenseSha256"] not in evidence_hashes:
                raise AuditError("reviewed-license-evidence-mismatch")
            distribution["reviewedLicenseExpression"] = override["licenseExpression"]
            distribution["reviewStatus"] = override["reviewStatus"]
            distribution["blockers"] = [
                blocker for blocker in distribution["blockers"] if blocker != "license-metadata-missing"
            ]
        else:
            distribution["reviewedLicenseExpression"] = None
            distribution["reviewStatus"] = "metadata-only-review-required"
        distributions.append(distribution)
        distribution_paths.append(path.parent)

    counts = Counter((item["normalizedName"], item["installationScope"]) for item in distributions)
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    for item in distributions:
        if (item["normalizedName"], item["installationScope"]) in duplicates:
            item["blockers"].append("duplicate-distribution")

    native_suffixes = {item.casefold() for item in contract["nativeSuffixes"]}
    native = [path for path in files if path.suffix.casefold() in native_suffixes]
    native_names = sorted({path.name for path in native if safe_name(path.name)}, key=str.casefold)
    if len(native_names) > contract["limits"]["maxNativeBasenames"]:
        raise AuditError("maximum-native-basename-count-exceeded")

    global_license_paths = [
        path
        for path in files
        if path.name.casefold().startswith(tuple(item.casefold() for item in contract["licenseBasenamePrefixes"]))
    ]
    if len(global_license_paths) > contract["limits"]["maxGlobalLicenseFiles"]:
        raise AuditError("maximum-global-license-file-count-exceeded")
    global_license_evidence = []
    for path in sorted(global_license_paths, key=lambda item: str(item).casefold()):
        size = path.stat(follow_symlinks=False).st_size
        if size > contract["limits"]["maxGlobalLicenseBytes"]:
            raise AuditError("maximum-license-size-exceeded")
        global_license_evidence.append({
            "relativePath": safe_relative(path, root),
            "bytes": size,
            "sha256": digest_file(path),
        })

    ownership: dict[Path, list[dict]] = {}
    for dist_info, distribution in zip(distribution_paths, distributions):
        for path, claim in record_native_claims(
            dist_info,
            distribution,
            root,
            native_suffixes,
            contract["limits"],
            allow_windows_separators=profile["operatingSystem"] == "windows",
        ).items():
            ownership.setdefault(path, []).append(claim)

    native_artifacts = []
    missing_owner = False
    missing_record_hash = False
    mismatched_record_hash = False
    for path in sorted(native, key=lambda item: str(item).casefold()):
        digest = digest_file(path)
        owners = []
        for claim in sorted(
            ownership.get(path, []),
            key=lambda item: (item["distribution"].casefold(), item["version"]),
        ):
            recorded = claim["recordSha256"]
            matches = recorded == digest if recorded is not None else None
            if recorded is None:
                missing_record_hash = True
            elif not matches:
                mismatched_record_hash = True
            owners.append({**claim, "recordSha256Matches": matches})
        relative_parts = path.relative_to(root).parts
        if (
            not owners
            and profile["operatingSystem"] == "windows"
            and is_contracted_embedded_runtime_path(relative_parts)
        ):
            owners.append({
                "distribution": profile["embeddedRuntime"],
                "version": profile["embeddedRuntime"].split(" ", 2)[1],
                "recordSha256": None,
                "recordSha256Matches": None,
                "ownershipEvidence": "contracted-embedded-runtime-path",
            })
        if not owners:
            missing_owner = True
        native_artifacts.append({
            "relativePath": safe_relative(path, root),
            "bytes": path.stat(follow_symlinks=False).st_size,
            "sha256": digest,
            "owners": owners,
        })

    blockers = sorted({blocker for item in distributions for blocker in item["blockers"]})
    if not distributions:
        blockers.append("distribution-inventory-empty")
    if missing_metadata:
        blockers.append("distribution-metadata-missing")
    if not archive_verified:
        blockers.append("archive-not-independently-verified")
    if native:
        blockers.append("native-components-require-exact-review")
    if missing_owner:
        blockers.append("native-component-owner-missing")
    if missing_record_hash:
        blockers.append("native-component-record-hash-missing")
    if mismatched_record_hash:
        blockers.append("native-component-record-hash-mismatch")
    blockers = sorted(set(blockers))
    report = {
        "schemaVersion": 1,
        "status": "review-required" if blockers else "metadata-inventory-complete-not-admitted",
        "profile": {"id": args.profile, **profile},
        "artifact": {"sha256": artifact_sha, "archiveIndependentlyVerified": archive_verified},
        "scope": {
            "regularFileCount": len(files),
            "distributionCount": len(distributions),
            "nativeFileCount": len(native),
            "nativeBasenameCount": len(native_names),
        },
        "distributions": distributions,
        "distributionDirectoriesMissingMetadata": missing_metadata,
        "globalLicenseEvidence": global_license_evidence,
        "nativeBasenames": native_names,
        "nativeArtifacts": native_artifacts,
        "blockers": blockers,
        "decision": {
            "installationAllowed": False,
            "redistributionAllowed": False,
            "packagingAllowed": False,
            "providerPromoted": False,
        },
        "privacy": {
            "absolutePathsRecorded": False,
            "hostnamesRecorded": False,
            "usernamesRecorded": False,
            "endpointsRecorded": False,
        },
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, ensure_ascii=True)
        stream.write("\n")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--artifact-sha256", required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    try:
        report = audit(parse_args())
    except (AuditError, FileNotFoundError, OSError) as error:
        print(f"Audit refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "blockers": report["blockers"], "scope": report["scope"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
