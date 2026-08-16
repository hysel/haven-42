#!/usr/bin/env python3
"""Discover exact official runtime releases and prepare a certification queue."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


MAX_RESPONSE_BYTES = 4 * 1024 * 1024
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CertificationDiscoveryError(ValueError):
    """The runtime discovery input or official release metadata was unsafe."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        raise CertificationDiscoveryError("runtime-discovery-redirect-refused")


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_RESPONSE_BYTES:
            raise CertificationDiscoveryError(f"unsafe-{label}")
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise CertificationDiscoveryError(f"invalid-{label}") from error
    if not isinstance(value, dict):
        raise CertificationDiscoveryError(f"invalid-{label}")
    return value


def _validate_contract(contract: dict[str, Any]) -> None:
    if (
        set(contract) != {
            "schemaVersion", "contractId", "defaultDecision", "rules",
            "requiredCertificationGates", "sources",
        }
        or contract.get("schemaVersion") != 1
        or contract.get("contractId") != "haven42.on-demand-runtime-certification"
        or contract.get("defaultDecision") != "deny"
    ):
        raise CertificationDiscoveryError("invalid-runtime-certification-contract")
    rules = contract.get("rules")
    expected_rules = {
        "officialReleaseSourcesOnly": True,
        "draftReleasesAllowed": False,
        "prereleaseReleasesAllowed": False,
        "mutableLatestAllowedForDiscoveryOnly": True,
        "immutableTagRequiredForEvidence": True,
        "artifactSha256Required": True,
        "artifactByteLengthRequired": True,
        "downloadsModelsOrRuntimes": False,
        "startsNativeTests": False,
        "writesCompatibilityRegistry": False,
        "changesManagedDefaults": False,
        "changesSupportLabels": False,
        "changesReleasePolicy": False,
    }
    if rules != expected_rules:
        raise CertificationDiscoveryError("invalid-runtime-certification-rules")
    gates = contract.get("requiredCertificationGates")
    if not isinstance(gates, list) or len(gates) < 8 or len(gates) != len(set(gates)):
        raise CertificationDiscoveryError("invalid-runtime-certification-gates")
    sources = contract.get("sources")
    if not isinstance(sources, list) or not sources:
        raise CertificationDiscoveryError("invalid-runtime-certification-sources")
    seen: set[str] = set()
    for source in sources:
        expected = {
            "id", "displayName", "repository", "releaseApi", "releasePagePrefix",
            "downloadPrefix", "tagPattern", "trackedCollection", "assetProfiles",
        }
        if not isinstance(source, dict) or set(source) != expected:
            raise CertificationDiscoveryError("invalid-runtime-certification-source")
        source_id = source.get("id")
        repository = source.get("repository")
        if (
            not isinstance(source_id, str)
            or not SAFE_ID.fullmatch(source_id)
            or source_id in seen
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", str(repository))
            or source.get("releaseApi")
            != f"https://api.github.com/repos/{repository}/releases/latest"
            or source.get("releasePagePrefix")
            != f"https://github.com/{repository}/releases/tag/"
            or source.get("downloadPrefix")
            != f"https://github.com/{repository}/releases/download/"
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", str(source.get("trackedCollection")))
        ):
            raise CertificationDiscoveryError("invalid-runtime-certification-source")
        try:
            tag_pattern = re.compile(str(source.get("tagPattern")))
        except re.error as error:
            raise CertificationDiscoveryError("invalid-runtime-tag-pattern") from error
        if tag_pattern.groups != 1:
            raise CertificationDiscoveryError("invalid-runtime-tag-pattern")
        profiles = source.get("assetProfiles")
        if not isinstance(profiles, list) or not profiles:
            raise CertificationDiscoveryError("invalid-runtime-asset-profiles")
        profile_keys: set[tuple[str, str, str]] = set()
        for profile in profiles:
            if not isinstance(profile, dict) or set(profile) != {
                "platform", "backend", "role", "namePattern",
            }:
                raise CertificationDiscoveryError("invalid-runtime-asset-profile")
            key = (profile["platform"], profile["backend"], profile["role"])
            if key in profile_keys:
                raise CertificationDiscoveryError("duplicate-runtime-asset-profile")
            profile_keys.add(key)
            try:
                re.compile(profile["namePattern"])
            except (TypeError, re.error) as error:
                raise CertificationDiscoveryError("invalid-runtime-asset-pattern") from error
        seen.add(source_id)


def _fetch_json(url: str, timeout_seconds: int) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "api.github.com" or parsed.username or parsed.password:
        raise CertificationDiscoveryError("runtime-discovery-origin-refused")
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Haven-42-runtime-certification/1"},
    )
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get_content_type()
            body = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, urllib.error.URLError) as error:
        raise CertificationDiscoveryError("runtime-discovery-request-failed") from error
    if content_type not in {"application/json", "application/vnd.github+json"} or len(body) > MAX_RESPONSE_BYTES:
        raise CertificationDiscoveryError("runtime-discovery-response-refused")
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CertificationDiscoveryError("runtime-discovery-response-invalid") from error
    if not isinstance(value, dict):
        raise CertificationDiscoveryError("runtime-discovery-response-invalid")
    return value


def _tracked_versions(registry: dict[str, Any], collection: str, tag_pattern: str) -> set[str]:
    records = registry.get(collection)
    if not isinstance(records, list):
        raise CertificationDiscoveryError("invalid-runtime-compatibility-registry")
    versions = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("version"), str):
            raise CertificationDiscoveryError("invalid-runtime-compatibility-registry")
        version = record["version"]
        tag_match = re.fullmatch(tag_pattern, version)
        versions.add(tag_match.group(1) if tag_match else version)
    return versions


def _release_record(source: dict[str, Any], release: dict[str, Any], tracked: set[str], gates: list[str]) -> dict[str, Any]:
    tag = release.get("tag_name")
    match = re.fullmatch(source["tagPattern"], str(tag or ""))
    if (
        not match
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or release.get("html_url") != source["releasePagePrefix"] + str(tag)
        or not isinstance(release.get("published_at"), str)
        or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", release["published_at"])
    ):
        raise CertificationDiscoveryError(f"invalid-official-release:{source['id']}")
    version = match.group(1)
    assets = release.get("assets")
    if not isinstance(assets, list) or not assets:
        raise CertificationDiscoveryError(f"missing-official-release-assets:{source['id']}")
    by_name: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise CertificationDiscoveryError(f"invalid-official-release-asset:{source['id']}")
        name = asset.get("name")
        size = asset.get("size")
        digest = asset.get("digest")
        if (
            not isinstance(name, str)
            or not name
            or name != PurePosixPath(name).name
            or name in by_name
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size <= 0
            or not isinstance(digest, str)
            or not digest.startswith("sha256:")
            or not HEX64.fullmatch(digest.removeprefix("sha256:"))
            or asset.get("browser_download_url")
            != source["downloadPrefix"] + f"{tag}/{name}"
        ):
            raise CertificationDiscoveryError(f"invalid-official-release-asset:{source['id']}")
        by_name[name] = asset
    selected = []
    missing = []
    for profile in source["assetProfiles"]:
        matches = [asset for name, asset in by_name.items() if re.fullmatch(profile["namePattern"], name)]
        if len(matches) != 1:
            missing.append({key: profile[key] for key in ("platform", "backend", "role")})
            continue
        asset = matches[0]
        selected.append({
            "platform": profile["platform"],
            "backend": profile["backend"],
            "role": profile["role"],
            "name": asset["name"],
            "byteLength": asset["size"],
            "sha256": asset["digest"].removeprefix("sha256:"),
            "sourceUrl": asset["browser_download_url"],
        })
    status = "already-tracked-exact-version" if version in tracked else "new-official-release-candidate"
    candidate_status = (
        "blocked-required-artifact-profiles-missing"
        if missing
        else "blocked-certification-gates-open"
    )
    return {
        "runtimeId": source["id"],
        "displayName": source["displayName"],
        "repository": source["repository"],
        "version": version,
        "tag": tag,
        "releasePage": release["html_url"],
        "publishedAtUtc": release["published_at"],
        "inventoryStatus": status,
        "candidateStatus": candidate_status,
        "matchedArtifacts": sorted(selected, key=lambda item: (item["platform"], item["backend"], item["role"])),
        "missingArtifactProfiles": missing,
        "certificationPlan": [
            {"gate": gate, "status": "pending", "required": True} for gate in gates
        ],
        "downloadAuthorized": False,
        "testExecutionAuthorized": False,
        "registryWriteAuthorized": False,
        "automaticPromotionAllowed": False,
    }


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Runtime Certification Candidate Check",
        "",
        f"_Checked: {report['generatedAtUtc']}_",
        "",
        "This is an on-demand review queue. It downloaded no runtime, started no test, changed no registry or managed default, and granted no support label.",
        "",
        "| Runtime | Latest official version | Inventory | Matched profiles | Missing profiles |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for item in report["candidates"]:
        lines.append(
            f"| {item['displayName']} | `{item['tag']}` | {item['inventoryStatus'].replace('-', ' ')} | "
            f"{len(item['matchedArtifacts'])} | {len(item['missingArtifactProfiles'])} |"
        )
    missing_items = [item for item in report["candidates"] if item["missingArtifactProfiles"]]
    if missing_items:
        lines.extend(["", "## Artifact profile blockers", ""])
    for item in missing_items:
        if item["missingArtifactProfiles"]:
            missing = ", ".join(
                f"{profile['platform']}/{profile['backend']}/{profile['role']}"
                for profile in item["missingArtifactProfiles"]
            )
            lines.append(f"- **{item['displayName']} `{item['tag']}`:** required artifact profiles not present: {missing}.")
    lines.extend([
        "",
        "## Required next steps",
        "",
        "For each new candidate, review the official source and license, download only the exact listed artifacts after approval, run the generated native and model regression matrix, record failures as well as passes, and require a separate owner decision before changing an admitted runtime or default.",
        "",
    ])
    return "\n".join(lines)


def discover(contract_path: Path, registry_path: Path, fixtures: dict[str, Path], selected_ids: set[str], timeout_seconds: int) -> dict[str, Any]:
    contract = _load_json(contract_path, "runtime-certification-contract")
    _validate_contract(contract)
    registry = _load_json(registry_path, "runtime-compatibility-registry")
    source_ids = {source["id"] for source in contract["sources"]}
    if selected_ids and not selected_ids.issubset(source_ids):
        raise CertificationDiscoveryError("unknown-runtime-source")
    if not set(fixtures).issubset(source_ids):
        raise CertificationDiscoveryError("unknown-runtime-fixture")
    candidates = []
    for source in contract["sources"]:
        if selected_ids and source["id"] not in selected_ids:
            continue
        release = _load_json(fixtures[source["id"]], "runtime-release-fixture") if source["id"] in fixtures else _fetch_json(source["releaseApi"], timeout_seconds)
        candidates.append(_release_record(
            source,
            release,
            _tracked_versions(registry, source["trackedCollection"], source["tagPattern"]),
            contract["requiredCertificationGates"],
        ))
    return {
        "schemaVersion": 1,
        "kind": "haven42-runtime-certification-candidate-report",
        "generatedAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "discoveryMode": "fixture" if fixtures else "online-official-release-metadata",
        "candidates": candidates,
        "summary": {
            "candidateCount": len(candidates),
            "newReleaseCount": sum(item["inventoryStatus"] == "new-official-release-candidate" for item in candidates),
            "trackedLatestCount": sum(item["inventoryStatus"] == "already-tracked-exact-version" for item in candidates),
            "missingProfileCount": sum(len(item["missingArtifactProfiles"]) for item in candidates),
        },
        "effects": {
            "downloadsModelsOrRuntimes": False,
            "startsNativeTests": False,
            "writesCompatibilityRegistry": False,
            "changesManagedDefaults": False,
            "changesSupportLabels": False,
            "changesReleasePolicy": False,
        },
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-path", type=Path, default=root / "config" / "runtime-certification-sources.json")
    parser.add_argument("--registry-path", type=Path, default=root / "config" / "alpha-2-runtime-compatibility.json")
    parser.add_argument("--runtime", action="append", default=[])
    parser.add_argument("--fixture", action="append", default=[], metavar="RUNTIME_ID=PATH")
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--markdown-output-path", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 120:
        parser.error("--timeout-seconds must be between 1 and 120")
    fixtures: dict[str, Path] = {}
    for value in args.fixture:
        source_id, separator, path = value.partition("=")
        if not separator or not SAFE_ID.fullmatch(source_id) or source_id in fixtures or not path:
            parser.error("--fixture must be a unique RUNTIME_ID=PATH value")
        fixtures[source_id] = Path(path)
    selected = set(args.runtime)
    try:
        report = discover(args.contract_path, args.registry_path, fixtures, selected, args.timeout_seconds)
    except CertificationDiscoveryError as error:
        parser.error(str(error))
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output_path:
        args.markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output_path.write_text(_markdown(report), encoding="utf-8")
    print(
        f"Runtime discovery prepared {report['summary']['candidateCount']} candidate(s); "
        f"{report['summary']['newReleaseCount']} new release(s); no downloads or tests started."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
