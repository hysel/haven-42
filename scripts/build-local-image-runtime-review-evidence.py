#!/usr/bin/env python3
"""Build deterministic, explicitly incomplete evidence from a runtime audit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys


SHA256 = re.compile(r"^[0-9a-f]{64}$")
MAX_DISTRIBUTIONS = 2048
MAX_NATIVE_ARTIFACTS = 10000
MAX_LICENSE_EVIDENCE = 8192
REQUIRED_FALSE_DECISIONS = (
    "installationAllowed",
    "redistributionAllowed",
    "packagingAllowed",
    "providerPromoted",
)


class EvidenceError(ValueError):
    pass


def reject_duplicate_object(pairs: list[tuple[str, object]]) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError("duplicate-audit-report-key")
        value[key] = item
    return value


def load_report(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError("invalid-audit-report")
    if path.stat().st_size > 64 * 1024 * 1024:
        raise EvidenceError("audit-report-too-large")
    try:
        report = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError("invalid-audit-report") from error
    if not isinstance(report, dict) or report.get("schemaVersion") != 1:
        raise EvidenceError("invalid-audit-report")
    return report


def safe_text(value: object, field: str, maximum: int = 500) -> str:
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise EvidenceError(f"invalid-{field}")
    if any(ord(character) < 32 for character in value):
        raise EvidenceError(f"invalid-{field}")
    return value


def safe_relative(value: object) -> str:
    text = safe_text(value, "relative-path", 1200)
    if "\\" in text or ":" in text:
        raise EvidenceError("unsafe-relative-path")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise EvidenceError("unsafe-relative-path")
    return path.as_posix()


def safe_sha(value: object) -> str:
    text = safe_text(value, "sha256", 64)
    if not SHA256.fullmatch(text):
        raise EvidenceError("invalid-sha256")
    return text


def safe_count(value: object, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise EvidenceError(f"invalid-{field}")
    return value


def validate_report(report: dict) -> None:
    if report.get("status") not in {"review-required", "metadata-inventory-complete-not-admitted"}:
        raise EvidenceError("audit-status-not-reviewable")
    artifact = report.get("artifact")
    if not isinstance(artifact, dict) or artifact.get("archiveIndependentlyVerified") is not True:
        raise EvidenceError("archive-not-independently-verified")
    safe_sha(artifact.get("sha256"))
    profile = report.get("profile")
    if not isinstance(profile, dict):
        raise EvidenceError("invalid-profile")
    for field in ("id", "operatingSystem", "accelerator", "provider", "providerVersion"):
        safe_text(profile.get(field), f"profile-{field}", 100)
    decision = report.get("decision")
    if not isinstance(decision, dict) or any(decision.get(field) is not False for field in REQUIRED_FALSE_DECISIONS):
        raise EvidenceError("authority-must-remain-false")
    privacy = report.get("privacy")
    if not isinstance(privacy, dict) or any(privacy.get(field) is not False for field in (
        "absolutePathsRecorded", "hostnamesRecorded", "usernamesRecorded", "endpointsRecorded"
    )):
        raise EvidenceError("privacy-boundary-invalid")
    distributions = report.get("distributions")
    native = report.get("nativeArtifacts")
    global_licenses = report.get("globalLicenseEvidence")
    if not isinstance(distributions, list) or not 1 <= len(distributions) <= MAX_DISTRIBUTIONS:
        raise EvidenceError("invalid-distributions")
    if not isinstance(native, list) or len(native) > MAX_NATIVE_ARTIFACTS:
        raise EvidenceError("invalid-native-artifacts")
    if not isinstance(global_licenses, list) or len(global_licenses) > MAX_LICENSE_EVIDENCE:
        raise EvidenceError("invalid-license-evidence")


def distribution_component(item: dict) -> dict:
    name = safe_text(item.get("name"), "distribution-name", 200)
    normalized = safe_text(item.get("normalizedName"), "distribution-normalized-name", 200)
    version = safe_text(item.get("version"), "distribution-version", 200)
    scope = safe_text(item.get("installationScope"), "distribution-scope", 300)
    blockers = item.get("blockers")
    if not isinstance(blockers, list) or any(not isinstance(value, str) for value in blockers):
        raise EvidenceError("invalid-distribution-blockers")
    expression = item.get("reviewedLicenseExpression") or item.get("licenseExpression") or item.get("legacyLicense")
    if expression is None:
        classifiers = item.get("licenseClassifiers", [])
        if not isinstance(classifiers, list) or any(not isinstance(value, str) for value in classifiers):
            raise EvidenceError("invalid-license-classifiers")
        expression = "; ".join(classifiers) if classifiers else "NOASSERTION"
    expression = safe_text(expression, "license-expression", 1000)
    return {
        "type": "library",
        "bom-ref": f"pkg:pypi/{normalized}@{version}?scope={scope.replace('/', '-')}",
        "name": name,
        "version": version,
        "licenses": [{"expression": expression}],
        "properties": [
            {"name": "haven42:review-status", "value": "blocked" if blockers else "metadata-recorded-review-required"},
            {"name": "haven42:blockers", "value": ",".join(sorted(blockers)) or "manual-review-required"},
            {"name": "haven42:installation-scope", "value": scope},
        ],
    }


def native_component(item: dict, index: int) -> dict:
    relative = safe_relative(item.get("relativePath"))
    size = safe_count(item.get("bytes"), "native-bytes", 64 * 1024 * 1024 * 1024)
    digest = safe_sha(item.get("sha256"))
    return {
        "type": "file",
        "bom-ref": f"native:{index}:{digest}",
        "name": PurePosixPath(relative).name,
        "hashes": [{"alg": "SHA-256", "content": digest}],
        "properties": [
            {"name": "haven42:relative-path", "value": relative},
            {"name": "haven42:bytes", "value": str(size)},
            {"name": "haven42:review-status", "value": "origin-and-license-unresolved"},
        ],
    }


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def build(report: dict) -> dict[str, bytes]:
    validate_report(report)
    profile = report["profile"]
    artifact_sha = report["artifact"]["sha256"]
    distributions = [distribution_component(item) for item in report["distributions"]]
    native = [native_component(item, index) for index, item in enumerate(report["nativeArtifacts"], 1)]
    blockers = sorted({safe_text(value, "blocker", 200) for value in report.get("blockers", [])})
    inventory = {
        "schemaVersion": 1,
        "status": "candidate-evidence-not-for-distribution",
        "profile": profile,
        "archiveSha256": artifact_sha,
        "distributions": report["distributions"],
        "globalLicenseEvidence": report["globalLicenseEvidence"],
        "blockers": blockers,
        "authority": {field: False for field in REQUIRED_FALSE_DECISIONS},
    }
    native_inventory = {
        "schemaVersion": 1,
        "status": "exact-files-origin-and-license-unresolved",
        "profileId": profile["id"],
        "archiveSha256": artifact_sha,
        "artifacts": report["nativeArtifacts"],
        "redistributionAllowed": False,
    }
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{artifact_sha[:8]}-{artifact_sha[8:12]}-{artifact_sha[12:16]}-{artifact_sha[16:20]}-{artifact_sha[20:32]}",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": profile["provider"],
                "version": profile["providerVersion"],
                "bom-ref": f"runtime:{profile['id']}:{artifact_sha}",
                "hashes": [{"alg": "SHA-256", "content": artifact_sha}],
            },
            "properties": [
                {"name": "haven42:status", "value": "candidate-evidence-not-admitted"},
                {"name": "haven42:redistribution-allowed", "value": "false"},
            ],
        },
        "components": distributions + native,
    }
    notice_lines = [
        "HAVEN 42 IMAGE RUNTIME THIRD-PARTY NOTICE CANDIDATE",
        "",
        "This is incomplete development evidence. It is not a shipping notice or redistribution clearance.",
        f"Profile: {profile['id']}",
        f"Archive SHA-256: {artifact_sha}",
        "",
        "Unresolved blockers:",
        *[f"- {value}" for value in blockers or ["manual-review-required"]],
        "",
        "Python distributions (reported metadata only):",
    ]
    for component in distributions:
        notice_lines.append(
            f"- {component['name']} {component['version']} | {component['licenses'][0]['expression']} | "
            f"{component['properties'][0]['value']}"
        )
    notice_lines.extend([
        "",
        f"Native files requiring exact origin/license review: {len(native)}",
        "Do not distribute this runtime from this evidence.",
    ])
    files = {
        "dependency-license-inventory.json": canonical_json(inventory),
        "native-file-inventory.json": canonical_json(native_inventory),
        "image-runtime.cdx.json": canonical_json(sbom),
        "THIRD-PARTY-NOTICES-CANDIDATE.txt": ("\n".join(notice_lines) + "\n").encode("utf-8"),
    }
    summary = {
        "schemaVersion": 1,
        "status": "candidate-evidence-not-for-distribution",
        "profileId": profile["id"],
        "archiveSha256": artifact_sha,
        "distributionCount": len(distributions),
        "nativeFileCount": len(native),
        "blockers": blockers,
        "files": [
            {"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            for name, data in sorted(files.items())
        ],
        "installationAllowed": False,
        "redistributionAllowed": False,
        "packagingAllowed": False,
        "providerPromoted": False,
    }
    files["review-summary.json"] = canonical_json(summary)
    return files


def write_exclusive(output: Path, files: dict[str, bytes]) -> None:
    if output.exists():
        raise EvidenceError("output-already-exists")
    output.mkdir(parents=True)
    for name, data in files.items():
        path = output / name
        with path.open("xb") as stream:
            stream.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-report", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    args = parser.parse_args()
    try:
        files = build(load_report(args.audit_report))
        write_exclusive(args.output_directory, files)
    except (EvidenceError, OSError) as error:
        print(f"Evidence build refused: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "candidate-evidence-not-for-distribution", "files": sorted(files)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
