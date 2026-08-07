#!/usr/bin/env python3
"""Generate a bounded aggregate GitHub Alpha usage report."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.request
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/github-alpha-usage-report-contract.json"
API_VERSION = "2026-03-10"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
SAFE_ASSET_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}")
UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


class ReportError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        raise ReportError("github-api-redirect-rejected")


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReportError("invalid-report-contract") from error
    expected = {
        "apiOrigin", "artifactRetentionDays", "collectDownloaderIdentity",
        "collectIpAddress", "commitReportsToRepository",
        "countGeneratedSourceArchives", "primaryAsset", "releaseTag",
        "repository", "schedule", "schemaVersion", "trafficWindowDays",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ReportError("invalid-report-contract")
    if (
        value["schemaVersion"] != 1
        or value["repository"] != "hysel/haven-42"
        or value["releaseTag"] != "v0.4.0-alpha.1"
        or value["primaryAsset"]
        != "haven42-0.4.0-alpha.1-windows-x64-unsigned.zip"
        or value["apiOrigin"] != "https://api.github.com"
        or value["schedule"] != "41 7 * * 1"
        or value["trafficWindowDays"] != 14
        or value["artifactRetentionDays"] != 30
        or value["collectDownloaderIdentity"] is not False
        or value["collectIpAddress"] is not False
        or value["countGeneratedSourceArchives"] is not False
        or value["commitReportsToRepository"] is not False
    ):
        raise ReportError("unsafe-report-contract")
    return value


def _bounded_int(value: object, field: str) -> int:
    if type(value) is not int or value < 0 or value > 10**12:
        raise ReportError(f"invalid-count:{field}")
    return value


def _timestamp(value: object, field: str) -> str:
    if not isinstance(value, str) or not UTC_TIMESTAMP.fullmatch(value):
        raise ReportError(f"invalid-timestamp:{field}")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise ReportError(f"invalid-timestamp:{field}") from error
    return value


def parse_release(value: object, contract: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("tag_name") != contract["releaseTag"]:
        raise ReportError("release-identity-mismatch")
    expected_url = (
        f"https://github.com/{contract['repository']}/releases/tag/"
        f"{contract['releaseTag']}"
    )
    if value.get("html_url") != expected_url:
        raise ReportError("release-url-mismatch")
    assets = value.get("assets")
    if not isinstance(assets, list) or not 1 <= len(assets) <= 1000:
        raise ReportError("invalid-release-assets")
    records: list[dict[str, Any]] = []
    names: set[str] = set()
    for item in assets:
        if not isinstance(item, dict):
            raise ReportError("invalid-release-asset")
        name = item.get("name")
        if not isinstance(name, str) or not SAFE_ASSET_NAME.fullmatch(name) or name in names:
            raise ReportError("invalid-release-asset-name")
        names.add(name)
        records.append({
            "name": name,
            "sizeBytes": _bounded_int(item.get("size"), f"asset-size:{name}"),
            "downloadCount": _bounded_int(
                item.get("download_count"), f"asset-downloads:{name}"
            ),
            "updatedAt": _timestamp(item.get("updated_at"), f"asset-updated:{name}"),
            "primaryAlphaPackage": name == contract["primaryAsset"],
        })
    if contract["primaryAsset"] not in names:
        raise ReportError("primary-alpha-asset-missing")
    records.sort(key=lambda item: (not item["primaryAlphaPackage"], item["name"]))
    primary = next(item for item in records if item["primaryAlphaPackage"])
    total = sum(item["downloadCount"] for item in records)
    return {
        "tag": contract["releaseTag"],
        "url": expected_url,
        "publishedAt": _timestamp(value.get("published_at"), "release-published"),
        "assets": records,
        "totals": {
            "primaryAlphaPackageDownloads": primary["downloadCount"],
            "supportingAssetDownloads": total - primary["downloadCount"],
            "allUploadedAssetDownloads": total,
        },
    }


def parse_traffic(value: object, series_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ReportError(f"invalid-traffic:{series_name}")
    total = _bounded_int(value.get("count"), f"{series_name}-count")
    uniques = _bounded_int(value.get("uniques"), f"{series_name}-uniques")
    if uniques > total:
        raise ReportError(f"invalid-traffic-uniques:{series_name}")
    rows = value.get(series_name)
    if not isinstance(rows, list) or len(rows) > 14:
        raise ReportError(f"invalid-traffic-series:{series_name}")
    daily = []
    seen: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            raise ReportError(f"invalid-traffic-row:{series_name}")
        timestamp = _timestamp(item.get("timestamp"), f"{series_name}-timestamp")
        if timestamp in seen:
            raise ReportError(f"duplicate-traffic-row:{series_name}")
        seen.add(timestamp)
        count = _bounded_int(item.get("count"), f"{series_name}-daily-count")
        unique = _bounded_int(item.get("uniques"), f"{series_name}-daily-uniques")
        if unique > count:
            raise ReportError(f"invalid-traffic-uniques:{series_name}")
        daily.append({"timestamp": timestamp, "count": count, "uniques": unique})
    daily.sort(key=lambda item: item["timestamp"])
    return {"count": total, "uniques": uniques, "daily": daily}


def _api_json(path: str, token: str, allow_forbidden: bool = False) -> object | None:
    allowed_paths = {
        "/repos/hysel/haven-42/releases/tags/v0.4.0-alpha.1",
        "/repos/hysel/haven-42/traffic/clones?per=day",
        "/repos/hysel/haven-42/traffic/views?per=day",
    }
    if path not in allowed_paths:
        raise ReportError("unsafe-github-api-path")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "haven-42-alpha-usage-report",
        "X-GitHub-Api-Version": API_VERSION,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            if response.headers.get_content_type() != "application/json":
                raise ReportError("invalid-github-api-content-type")
            length = response.headers.get("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_RESPONSE_BYTES):
                raise ReportError("github-api-response-too-large")
            content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise ReportError("github-api-response-too-large")
    except urllib.error.HTTPError as error:
        if allow_forbidden and error.code in {403, 404}:
            return None
        raise ReportError(f"github-api-http-error:{error.code}") from error
    except urllib.error.URLError as error:
        raise ReportError("github-api-unavailable") from error
    try:
        return json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReportError("invalid-github-api-json") from error


def build_report(
    contract: dict[str, Any],
    release_json: object,
    clones_json: object | None,
    views_json: object | None,
    generated_at: str,
) -> dict[str, Any]:
    release = parse_release(release_json, contract)
    traffic_available = clones_json is not None and views_json is not None
    traffic = {
        "available": traffic_available,
        "windowDays": contract["trafficWindowDays"],
        "clones": parse_traffic(clones_json, "clones") if traffic_available else None,
        "views": parse_traffic(views_json, "views") if traffic_available else None,
        "unavailableReason": None if traffic_available else "github-traffic-permission-unavailable",
    }
    return {
        "schemaVersion": 1,
        "kind": "haven42-alpha-usage-report",
        "generatedAt": _timestamp(generated_at, "generated-at"),
        "repository": contract["repository"],
        "release": release,
        "repositoryTraffic": traffic,
        "privacy": {
            "downloaderIdentityCollected": False,
            "ipAddressCollected": False,
            "individualEventsAvailable": False,
        },
        "limitations": [
            "Uploaded release-asset counts are cumulative and may include repeat downloads.",
            "GitHub-generated source ZIP and TAR downloads are not counted as release assets.",
            "Repository traffic is aggregate, covers only the latest 14 days, and identifies no visitor.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    release = report["release"]
    totals = release["totals"]
    lines = [
        "# Haven 42 Alpha Usage Report",
        "",
        f"Generated: {report['generatedAt']}",
        "",
        "This report contains aggregate GitHub measurements only. It does not identify downloaders or visitors.",
        "",
        "## Alpha Downloads",
        "",
        f"- Primary Alpha ZIP: **{totals['primaryAlphaPackageDownloads']}**",
        f"- Supporting release assets: **{totals['supportingAssetDownloads']}**",
        f"- All uploaded release assets: **{totals['allUploadedAssetDownloads']}**",
        "",
        "| Release asset | Size (bytes) | Downloads |",
        "|---|---:|---:|",
    ]
    lines.extend(
        f"| `{item['name']}` | {item['sizeBytes']} | {item['downloadCount']} |"
        for item in release["assets"]
    )
    lines.extend(["", "## Repository Traffic", ""])
    traffic = report["repositoryTraffic"]
    if traffic["available"]:
        lines.extend([
            f"- Full clones during GitHub's 14-day window: **{traffic['clones']['count']}** "
            f"(**{traffic['clones']['uniques']}** unique cloners)",
            f"- Repository views during GitHub's 14-day window: **{traffic['views']['count']}** "
            f"(**{traffic['views']['uniques']}** unique visitors)",
        ])
    else:
        lines.append(
            "Repository clone/view traffic is unavailable because the workflow's "
            "least-privilege token has no repository Administration permission. "
            "No broader credential was requested."
        )
    lines.extend(["", "## Important Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def _write_atomic(path: Path, content: bytes) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ReportError("unsafe-report-output")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".haven42-report-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_report(output_directory: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output = output_directory.resolve()
    if output.exists() and (not output.is_dir() or output.is_symlink()):
        raise ReportError("unsafe-report-output-directory")
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "alpha-usage-report.json"
    markdown_path = output / "alpha-usage-report.md"
    _write_atomic(
        json_path,
        (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    _write_atomic(markdown_path, markdown(report).encode("utf-8"))
    return markdown_path, json_path


def resolve_cli_output(value: str) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        requested = ROOT / requested
    output = requested.resolve()
    allowed = (ROOT / "dist").resolve()
    try:
        relative = output.relative_to(allowed)
    except ValueError as error:
        raise ReportError("report-output-outside-repository-dist") from error
    if not relative.parts:
        raise ReportError("unsafe-report-output-directory")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-directory", default="dist/alpha-usage-report")
    args = parser.parse_args()
    contract = load_contract()
    token = os.environ.get("HAVEN42_GITHUB_REPORT_TOKEN", "")
    if len(token) > 4096 or "\n" in token or "\r" in token:
        raise SystemExit("The GitHub report token is invalid.")
    repository = contract["repository"]
    tag = contract["releaseTag"]
    release = _api_json(f"/repos/{repository}/releases/tags/{tag}", token)
    clones = (
        _api_json(f"/repos/{repository}/traffic/clones?per=day", token, True)
        if token else None
    )
    views = (
        _api_json(f"/repos/{repository}/traffic/views?per=day", token, True)
        if token else None
    )
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    report = build_report(contract, release, clones, views, now)
    markdown_path, json_path = write_report(resolve_cli_output(args.output_directory), report)
    print(markdown_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
