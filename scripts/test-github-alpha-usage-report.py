#!/usr/bin/env python3
"""Offline hostile tests for the aggregate GitHub Alpha usage report."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "github_alpha_usage_report",
    ROOT / "scripts/generate-github-alpha-usage-report.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def rejected(function, expected: str) -> None:
    try:
        function()
    except MODULE.ReportError as error:
        assert str(error) == expected, (str(error), expected)
        return
    raise AssertionError(f"hostile report input accepted: {expected}")


def main() -> int:
    contract = MODULE.load_contract()
    release = {
        "tag_name": contract["releaseTag"],
        "html_url": "https://github.com/hysel/haven-42/releases/tag/v0.4.0-alpha.1",
        "published_at": "2026-08-05T12:00:00Z",
        "uploader": {"login": "must-not-appear"},
        "assets": [
            {
                "name": contract["primaryAsset"],
                "size": 123,
                "download_count": 7,
                "updated_at": "2026-08-05T12:01:00Z",
                "uploader": {"login": "must-not-appear"},
            },
            {
                "name": "SHA256SUMS",
                "size": 64,
                "download_count": 3,
                "updated_at": "2026-08-05T12:01:00Z",
            },
        ],
    }
    clones = {
        "count": 5,
        "uniques": 3,
        "clones": [
            {"timestamp": "2026-08-05T00:00:00Z", "count": 5, "uniques": 3}
        ],
    }
    views = {
        "count": 9,
        "uniques": 4,
        "views": [
            {"timestamp": "2026-08-05T00:00:00Z", "count": 9, "uniques": 4}
        ],
    }
    report = MODULE.build_report(
        contract, release, clones, views, "2026-08-06T12:00:00Z"
    )
    assert report["release"]["totals"] == {
        "primaryAlphaPackageDownloads": 7,
        "supportingAssetDownloads": 3,
        "allUploadedAssetDownloads": 10,
    }
    assert report["repositoryTraffic"]["available"] is True
    assert report["privacy"] == {
        "downloaderIdentityCollected": False,
        "ipAddressCollected": False,
        "individualEventsAvailable": False,
    }
    assert "must-not-appear" not in json.dumps(report)
    with tempfile.TemporaryDirectory(prefix="haven42-alpha-report-") as raw:
        markdown_path, json_path = MODULE.write_report(Path(raw), report)
        assert markdown_path.is_file() and json_path.is_file()
        assert "Primary Alpha ZIP: **7**" in markdown_path.read_text(encoding="utf-8")
        assert json.loads(json_path.read_text(encoding="utf-8")) == report
    checks = 7

    hostile = copy.deepcopy(release)
    hostile["tag_name"] = "v9"
    rejected(lambda: MODULE.parse_release(hostile, contract), "release-identity-mismatch")
    checks += 1
    hostile = copy.deepcopy(release)
    hostile["html_url"] = "https://example.com/redirect"
    rejected(lambda: MODULE.parse_release(hostile, contract), "release-url-mismatch")
    checks += 1
    hostile = copy.deepcopy(release)
    hostile["assets"][0]["name"] = "../alpha.zip"
    rejected(lambda: MODULE.parse_release(hostile, contract), "invalid-release-asset-name")
    checks += 1
    hostile = copy.deepcopy(release)
    hostile["assets"][1]["name"] = contract["primaryAsset"]
    rejected(lambda: MODULE.parse_release(hostile, contract), "invalid-release-asset-name")
    checks += 1
    hostile = copy.deepcopy(release)
    hostile["assets"][0]["download_count"] = -1
    rejected(
        lambda: MODULE.parse_release(hostile, contract),
        f"invalid-count:asset-downloads:{contract['primaryAsset']}",
    )
    checks += 1
    hostile = copy.deepcopy(release)
    hostile["assets"] = hostile["assets"][1:]
    rejected(lambda: MODULE.parse_release(hostile, contract), "primary-alpha-asset-missing")
    checks += 1
    hostile_traffic = copy.deepcopy(clones)
    hostile_traffic["uniques"] = 6
    rejected(
        lambda: MODULE.parse_traffic(hostile_traffic, "clones"),
        "invalid-traffic-uniques:clones",
    )
    checks += 1
    hostile = copy.deepcopy(release)
    hostile["published_at"] = "2026-99-05T12:00:00Z"
    rejected(
        lambda: MODULE.parse_release(hostile, contract),
        "invalid-timestamp:release-published",
    )
    checks += 1
    rejected(
        lambda: MODULE._api_json("/repos/hysel/haven-42/issues", ""),
        "unsafe-github-api-path",
    )
    checks += 1
    hostile_traffic = copy.deepcopy(clones)
    hostile_traffic["clones"].append(copy.deepcopy(hostile_traffic["clones"][0]))
    rejected(
        lambda: MODULE.parse_traffic(hostile_traffic, "clones"),
        "duplicate-traffic-row:clones",
    )
    checks += 1
    unavailable = MODULE.build_report(
        contract, release, None, None, "2026-08-06T12:00:00Z"
    )
    assert unavailable["repositoryTraffic"] == {
        "available": False,
        "windowDays": 14,
        "clones": None,
        "views": None,
        "unavailableReason": "github-traffic-permission-unavailable",
    }
    checks += 1
    with tempfile.TemporaryDirectory(prefix="haven42-alpha-report-hostile-") as raw:
        target = Path(raw) / "alpha-usage-report.md"
        target.mkdir()
        rejected(
            lambda: MODULE._write_atomic(target, b"unsafe"),
            "unsafe-report-output",
        )
    checks += 1
    assert MODULE.resolve_cli_output("dist/alpha-usage-report-test") == (
        ROOT / "dist/alpha-usage-report-test"
    ).resolve()
    rejected(
        lambda: MODULE.resolve_cli_output(str(ROOT.parent / "escaped-report")),
        "report-output-outside-repository-dist",
    )
    checks += 2

    class Headers(dict):
        def get_content_type(self):
            return self.get("content-type", "application/json").split(";", 1)[0]

    class Response:
        def __init__(self, content: bytes, content_type: str = "application/json"):
            self.content = content
            self.headers = Headers({
                "content-type": content_type,
                "Content-Length": str(len(content)),
            })

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, limit: int):
            return self.content[:limit]

    class Opener:
        def __init__(self, response):
            self.response = response
            self.request = None

        def open(self, request, timeout):
            assert timeout == 20
            self.request = request
            return self.response

    original_opener = MODULE.urllib.request.build_opener
    valid_opener = Opener(Response(b'{"ok":true}'))
    try:
        MODULE.urllib.request.build_opener = lambda *_handlers: valid_opener
        assert MODULE._api_json(
            "/repos/hysel/haven-42/releases/tags/v0.4.0-alpha.1", ""
        ) == {"ok": True}
        assert valid_opener.request.full_url.startswith("https://api.github.com/")
        assert valid_opener.request.get_header("Authorization") is None
    finally:
        MODULE.urllib.request.build_opener = original_opener
    checks += 3
    bad_opener = Opener(Response(b"<html>", "text/html"))
    try:
        MODULE.urllib.request.build_opener = lambda *_handlers: bad_opener
        rejected(
            lambda: MODULE._api_json(
                "/repos/hysel/haven-42/releases/tags/v0.4.0-alpha.1", "token"
            ),
            "invalid-github-api-content-type",
        )
    finally:
        MODULE.urllib.request.build_opener = original_opener
    checks += 1
    rejected(
        lambda: MODULE.NoRedirect().redirect_request(
            None, None, 302, "redirect", {}, "https://example.com/"
        ),
        "github-api-redirect-rejected",
    )
    checks += 1

    print(f"GitHub Alpha usage report tests passed: {checks} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
