#!/usr/bin/env python3
"""Offline verifier for manually supplied non-synthetic PDF intake records."""

from __future__ import annotations

import argparse
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "config/pdf-hostile-corpus-intake-policy.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class IntakeRejected(ValueError):
    pass


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def safe_https_url(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) > 2048 or any(
        character in value for character in "\r\n\t\\"
    ):
        raise IntakeRejected(f"{field}-invalid")
    parsed = urlsplit(value)
    hostname = parsed.hostname.casefold() if parsed.hostname else ""
    try:
        address = ipaddress.ip_address(hostname.strip("[]"))
    except ValueError:
        address = None
    decoded_path = unquote(parsed.path)
    if (
        parsed.scheme != "https"
        or not hostname
        or not hostname.isascii()
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
        or parsed.fragment
        or parsed.query
        or hostname in {"localhost", "localhost.localdomain"}
        or hostname.endswith((".local", ".localhost"))
        or (
            address is not None
            and (
                not address.is_global
                or address.is_loopback
                or address.is_link_local
                or address.is_private
                or address.is_reserved
                or address.is_unspecified
            )
        )
        or "\\" in decoded_path
        or ".." in decoded_path.split("/")
    ):
        raise IntakeRejected(f"{field}-invalid")
    return value


def verify(record: object, policy: dict) -> dict:
    if not isinstance(record, dict) or set(record) != set(policy["requiredRecordFields"]) | {
        "sourceRevision"
    }:
        raise IntakeRejected("record-shape-invalid")
    if not isinstance(record["id"], str) or not IDENTIFIER.fullmatch(record["id"]):
        raise IntakeRejected("id-invalid")
    for field in ("sourceProject", "licenseSpdx"):
        if not isinstance(record[field], str) or not 1 <= len(record[field]) <= 128:
            raise IntakeRejected(f"{field}-invalid")
    source_page = safe_https_url(record["sourcePage"], "source-page")
    artifact_url = safe_https_url(record["artifactUrl"], "artifact-url")
    if not isinstance(record["sourceRevision"], str) or not REVISION.fullmatch(
        record["sourceRevision"]
    ):
        raise IntakeRejected("source-revision-invalid")
    source = urlsplit(source_page)
    artifact = urlsplit(artifact_url)
    if source.hostname.casefold() != artifact.hostname.casefold():
        raise IntakeRejected("artifact-host-mismatch")
    if record["sourceRevision"] not in unquote(artifact.path).split("/"):
        raise IntakeRejected("artifact-revision-unbound")
    if not isinstance(record["artifactSha256"], str) or not SHA256.fullmatch(
        record["artifactSha256"]
    ):
        raise IntakeRejected("artifact-sha256-invalid")
    if record["category"] not in policy["allowedCategories"]:
        raise IntakeRejected("category-invalid")
    for field in (
        "redistributionAllowed",
        "privacyReviewed",
        "malwareReviewed",
    ):
        if record[field] is not True:
            raise IntakeRejected(f"{field}-required")
    if record["retentionDecision"] != "manual-approved-ignored-quarantine":
        raise IntakeRejected("retention-decision-invalid")
    return {
        "schemaVersion": 1,
        "status": "metadata-record-accepted-for-manual-acquisition-review",
        "id": record["id"],
        "networkUsed": False,
        "artifactOpened": False,
        "artifactRetained": False,
        "parserExecuted": False,
        "runtimeAdmissionGranted": False,
    }


def self_test() -> int:
    policy = load_policy()
    base = {
        "id": "fixture-one",
        "sourceProject": "Example",
        "sourcePage": "https://example.invalid/project",
        "artifactUrl": "https://example.invalid/project/raw/0123456789012345678901234567890123456789/case.pdf",
        "artifactSha256": "a" * 64,
        "licenseSpdx": "CC0-1.0",
        "redistributionAllowed": True,
        "privacyReviewed": True,
        "malwareReviewed": True,
        "category": "malformed-structure",
        "retentionDecision": "manual-approved-ignored-quarantine",
        "sourceRevision": "0123456789012345678901234567890123456789",
    }
    assert verify(base, policy)["status"].startswith("metadata-record-accepted")
    cases = []
    for field, value in (
        ("id", "../case"),
        ("sourcePage", "http://example.invalid/project"),
        ("sourcePage", "https://user" + chr(58) + "pass@example.invalid/project"),
        ("sourcePage", "https://localhost/project"),
        ("sourcePage", "https://example.invalid/project#mutable"),
        ("sourcePage", "https://127.0.0.1/project"),
        ("artifactUrl", "file:///tmp/case.pdf"),
        ("artifactUrl", "https://example.invalid\\case.pdf"),
        ("artifactUrl", "https://other.invalid/project/raw/0123456789012345678901234567890123456789/case.pdf"),
        ("artifactUrl", "https://example.invalid/project/raw/main/case.pdf"),
        ("artifactUrl", "https://example.invalid/project/raw/0123456789012345678901234567890123456789/case.pdf?download=1"),
        ("artifactUrl", "https://example.invalid/project/raw/0123456789012345678901234567890123456789/%2e%2e/case.pdf"),
        ("artifactSha256", "A" * 64),
        ("artifactSha256", "a" * 63),
        ("sourceRevision", "main"),
        ("category", "live-malware"),
        ("redistributionAllowed", False),
        ("privacyReviewed", False),
        ("malwareReviewed", False),
        ("retentionDecision", "commit-to-repository"),
    ):
        changed = dict(base)
        changed[field] = value
        cases.append(changed)
    missing = dict(base)
    missing.pop("artifactSha256")
    cases.append(missing)
    extra = dict(base)
    extra["path"] = "/tmp/case.pdf"
    cases.append(extra)
    for case in cases:
        try:
            verify(case, policy)
        except IntakeRejected:
            continue
        raise AssertionError("hostile intake record unexpectedly accepted")
    print(f"PDF corpus intake verifier passed {len(cases) + 1} offline cases.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--record", type=Path)
    arguments = parser.parse_args()
    if arguments.self_test:
        return self_test()
    if arguments.record is None:
        parser.error("--record is required without --self-test")
    record = json.loads(arguments.record.read_text(encoding="utf-8"))
    print(json.dumps(verify(record, load_policy()), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
