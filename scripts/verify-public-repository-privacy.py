#!/usr/bin/env python3
"""Fail closed when public Git history exposes machine-specific or secret data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "config" / "public-repository-privacy-policy.json"

RFC1918 = re.compile(
    rb"(?<![0-9])(?:"
    rb"10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|"
    rb"172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}|"
    rb"192\.168\.[0-9]{1,3}\.[0-9]{1,3}"
    rb")(?![0-9])"
)
URL_CREDENTIAL = re.compile(rb"https?://[^\s/@:]+:[^\s/@]+@", re.IGNORECASE)
PRIVATE_KEY = re.compile(
    rb"-----BEGIN (?:OPENSSH|RSA|EC|DSA|PRIVATE) PRIVATE KEY-----"
)
SSH_PUBLIC_KEY = re.compile(
    rb"(?:^|\s)(?:ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) "
    rb"[A-Za-z0-9+/]{40,}={0,3}(?:\s|$)"
)
SSH_FINGERPRINT = re.compile(rb"SHA256:[A-Za-z0-9+/]{30,}={0,3}")
LIKELY_SECRET = re.compile(
    rb"(?i)(?:api[_-]?key|access[_-]?token|personal[_-]?access[_-]?token|"
    rb"password|client[_-]?secret|authorization|bearer)"
    rb"\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-]{16,}"
)
WINDOWS_USER_PATH = re.compile(
    rb"(?i)(?:[A-Z]:|file:/+?[A-Z]:)[/\\]Users[/\\]([^/\\\s'\"`]+)"
)
POSIX_USER_PATH = re.compile(rb"/(?:home|Users)/([^/\s'\"`]+)/")
SSH_TARGET = re.compile(
    rb"(?<![A-Za-z0-9_.-])([A-Za-z_][A-Za-z0-9_.-]{0,63})@"
    rb"([A-Za-z0-9][A-Za-z0-9.-]{0,252})(?![A-Za-z0-9_.-])"
)
SSH_COMMAND_LINE = re.compile(
    rb"(?im)^[^\r\n]*(?:^|[\s;&|])(?:ssh|scp|sftp)(?:\.exe)?"
    rb"(?:\s|$)[^\r\n]{0,500}$"
)


class PrivacyFailure(RuntimeError):
    pass


def git(*arguments: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        input=input_bytes,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise PrivacyFailure(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def load_policy() -> dict:
    try:
        value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise PrivacyFailure("Privacy policy could not be loaded.") from error
    if (
        not isinstance(value, dict)
        or value.get("schemaVersion") != 1
        or value.get("policyId") != "haven42.public-repository-privacy"
    ):
        raise PrivacyFailure("Privacy policy identity is invalid.")
    patterns = value.get("identity", {}).get("allowedEmailPatterns")
    placeholders = value.get("genericPathIdentities")
    rule_allowlist = value.get("contentRulePathAllowlist")
    if (
        not isinstance(patterns, list)
        or not patterns
        or not all(isinstance(item, str) and item for item in patterns)
        or not isinstance(placeholders, list)
        or not placeholders
        or not all(isinstance(item, str) and item for item in placeholders)
        or not isinstance(rule_allowlist, dict)
        or not all(
            isinstance(label, str)
            and isinstance(paths, list)
            and all(isinstance(path, str) and path for path in paths)
            for label, paths in rule_allowlist.items()
        )
    ):
        raise PrivacyFailure("Privacy policy allowlists are invalid.")
    return value


def reachable_commits(policy: dict) -> list[str]:
    refs = policy.get("historyRefs")
    if not isinstance(refs, list) or not all(isinstance(item, str) for item in refs):
        raise PrivacyFailure("Privacy history refs are invalid.")
    commits = git("rev-list", *refs).decode("ascii").splitlines()
    if not commits or any(not re.fullmatch(r"[0-9a-f]{40}", item) for item in commits):
        raise PrivacyFailure("No valid reachable commits were found.")
    return list(dict.fromkeys(commits))


def commit_blobs(commits: list[str]) -> dict[str, bytes]:
    records = git("rev-list", "--objects", *commits).splitlines()
    object_ids: list[bytes] = []
    for record in records:
        object_id = record.split(b" ", 1)[0]
        if re.fullmatch(rb"[0-9a-f]{40}", object_id):
            object_ids.append(object_id)
    object_ids = list(dict.fromkeys(object_ids))
    request = b"".join(item + b"\n" for item in object_ids)
    output = git(
        "cat-file",
        "--batch",
        input_bytes=request,
    )
    result: dict[str, bytes] = {}
    position = 0
    for expected in object_ids:
        newline = output.find(b"\n", position)
        if newline < 0:
            raise PrivacyFailure("Git object batch response was truncated.")
        header = output[position:newline].split()
        position = newline + 1
        if len(header) != 3 or header[0] != expected:
            raise PrivacyFailure("Git object batch response was malformed.")
        size = int(header[2])
        content = output[position:position + size]
        position += size + 1
        if header[1] == b"blob":
            result[expected.decode("ascii")] = content
    return result


def object_paths(commits: list[str]) -> dict[str, str]:
    paths: dict[str, str] = {}
    for record in git("rev-list", "--objects", *commits).splitlines():
        parts = record.split(b" ", 1)
        if len(parts) == 2:
            paths.setdefault(
                parts[0].decode("ascii"),
                parts[1].decode("utf-8", "replace"),
            )
    return paths


def allowed_path_identity(value: bytes, placeholders: set[bytes]) -> bool:
    return value.lower() in placeholders or value.startswith(b"<") or value.endswith(b">")


def scan_content(
    object_id: str,
    path: str,
    content: bytes,
    placeholders: set[bytes],
    rule_allowlist: dict[str, set[str]],
) -> list[str]:
    failures: list[str] = []
    checks = (
        ("RFC1918 address", RFC1918),
        ("credential-bearing URL", URL_CREDENTIAL),
        ("private key material", PRIVATE_KEY),
        ("SSH public key material", SSH_PUBLIC_KEY),
        ("SSH fingerprint", SSH_FINGERPRINT),
        ("likely secret", LIKELY_SECRET),
    )
    for label, pattern in checks:
        if path not in rule_allowlist.get(label, set()) and pattern.search(content):
            failures.append(f"{label}: {path} ({object_id})")
    for pattern, label in (
        (WINDOWS_USER_PATH, "Windows user path"),
        (POSIX_USER_PATH, "POSIX user path"),
    ):
        if path in rule_allowlist.get(label, set()):
            continue
        for match in pattern.finditer(content):
            if not allowed_path_identity(match.group(1), placeholders):
                failures.append(f"{label}: {path} ({object_id})")
                break
    for line in SSH_COMMAND_LINE.finditer(content):
        for match in SSH_TARGET.finditer(line.group(0)):
            user = match.group(1).lower()
            host = match.group(2).lower()
            if (
                user not in placeholders
                and host not in {b"localhost", b"github.com"}
                and not host.endswith((b".example", b".test", b".invalid"))
            ):
                failures.append(f"machine-specific SSH target: {path} ({object_id})")
                return failures
    return failures


def scan_identities(policy: dict, commits: list[str]) -> list[str]:
    patterns = [
        re.compile(item)
        for item in policy["identity"]["allowedEmailPatterns"]
    ]
    failures: list[str] = []
    identity_lines = git(
        "log",
        "--format=%H%x09%ae%x09%ce",
        *commits,
    ).decode("utf-8", "replace").splitlines()
    for line in identity_lines:
        fields = line.split("\t")
        if len(fields) != 3:
            raise PrivacyFailure("Git identity record was malformed.")
        commit, author_email, committer_email = fields
        for role, email in (("author", author_email), ("committer", committer_email)):
            if not any(pattern.fullmatch(email) for pattern in patterns):
                failures.append(f"non-private {role} identity: {commit}")
    for commit in commits:
        message = git("show", "-s", "--format=%B", commit)
        encoded = message
        if RFC1918.search(encoded) or WINDOWS_USER_PATH.search(encoded):
            failures.append(f"machine-specific commit message: {commit}")
    return failures


def run() -> tuple[int, int]:
    policy = load_policy()
    commits = reachable_commits(policy)
    paths = object_paths(commits)
    blobs = commit_blobs(commits)
    placeholders = {
        item.encode("utf-8").lower()
        for item in policy["genericPathIdentities"]
    }
    rule_allowlist = {
        label: set(paths)
        for label, paths in policy["contentRulePathAllowlist"].items()
    }
    failures = scan_identities(policy, commits)
    for object_id, content in blobs.items():
        failures.extend(
            scan_content(
                object_id,
                paths.get(object_id, "<unmapped-blob>"),
                content,
                placeholders,
                rule_allowlist,
            )
        )
    if failures:
        unique = list(dict.fromkeys(failures))
        for failure in unique[:100]:
            print(f"PRIVACY FAILURE: {failure}", file=sys.stderr)
        if len(unique) > 100:
            print(
                f"PRIVACY FAILURE: {len(unique) - 100} additional failures omitted.",
                file=sys.stderr,
            )
        raise PrivacyFailure(
            f"Public repository privacy scan failed with {len(unique)} finding(s)."
        )
    return len(commits), len(blobs)


def self_test() -> None:
    placeholders = {b"name", b"user", b"your-user", b"haven42-comfyui"}
    assert RFC1918.search(b"http://192.168.4.5:11434")
    assert RFC1918.search(b"10.0.0.9")
    assert RFC1918.search(b"172.31.4.8")
    assert not RFC1918.search(b"192.0.2.42")
    assert WINDOWS_USER_PATH.search(rb"C:\Users\private-name\repo")
    assert allowed_path_identity(b"your-user", placeholders)
    assert not allowed_path_identity(b"private-name", placeholders)
    assert SSH_PUBLIC_KEY.search(b"ssh-ed25519 " + b"A" * 50)
    assert SSH_FINGERPRINT.search(b"SHA256:" + b"A" * 40)
    assert URL_CREDENTIAL.search(b"https://user:password@example.test")
    assert PRIVATE_KEY.search(b"-----BEGIN OPENSSH PRIVATE KEY-----")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print("Public repository privacy scanner self-test passed.")
            return 0
        commits, blobs = run()
    except PrivacyFailure as error:
        print(str(error), file=sys.stderr)
        return 1
    print(
        "Public repository privacy scan passed: "
        f"{commits} reachable commits and {blobs} unique blobs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
