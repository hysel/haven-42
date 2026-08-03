#!/usr/bin/env python3
"""Verify the committed and optional live GitHub repository policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = ROOT / "config/github-repository-policy.json"


class PolicyError(ValueError):
    pass


def load_policy() -> dict:
    try:
        value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PolicyError("invalid-policy-json") from error
    required = {
        "schemaVersion", "repository", "defaultBranch", "mergePolicy",
        "branchProtection", "actions", "artifactAttestations",
    }
    if not isinstance(value, dict) or set(value) != required or value["schemaVersion"] != 1:
        raise PolicyError("invalid-policy-shape")
    return value


def verify_static(policy: dict) -> None:
    if policy["repository"] != "hysel/haven-42" or policy["defaultBranch"] != "main":
        raise PolicyError("unexpected-repository-identity")
    merge = policy["mergePolicy"]
    if merge != {
        "allowMergeCommit": False,
        "allowSquashMerge": True,
        "allowRebaseMerge": True,
        "deleteBranchOnMerge": True,
        "requiredLinearHistory": True,
    }:
        raise PolicyError("unsafe-merge-policy")
    protection = policy["branchProtection"]
    checks = protection.get("requiredChecks")
    if not isinstance(checks, list) or len(checks) != len(set(checks)) or len(checks) != 9:
        raise PolicyError("invalid-required-checks")
    expected_checks = {
        "Public repository privacy",
        "Wiki synchronization",
        "Windows PowerShell validation",
        "Linux script smoke tests",
        "macOS script smoke tests",
        "Windows portable package",
        "Linux portable package",
        "macOS portable package",
        "CodeQL Python analysis",
    }
    if set(checks) != expected_checks:
        raise PolicyError("required-check-drift")
    if any(protection.get(field) != expected for field, expected in {
        "strictStatusChecks": True,
        "dismissStaleReviews": True,
        "requiredApprovingReviewCount": 0,
        "requireCodeOwnerReviews": False,
        "enforceAdmins": True,
        "requireConversationResolution": True,
        "allowForcePushes": False,
        "allowDeletions": False,
    }.items()):
        raise PolicyError("unsafe-branch-protection")
    if policy["actions"] != {
        "enabled": True,
        "allowedActions": "selected",
        "githubOwnedAllowed": True,
        "verifiedAllowed": False,
        "patternsAllowed": [],
        "shaPinningRequired": True,
        "defaultWorkflowPermissions": "read",
        "canApprovePullRequestReviews": False,
    }:
        raise PolicyError("unsafe-actions-policy")
    if policy["artifactAttestations"] != {
        "enabled": True,
        "trigger": "push-main-after-native-package-success",
        "subjects": "unsigned-development-archives-only",
        "action": "actions/attest",
        "actionCommit": "508db95dd578ae2727ebd6217d5ba78e4fbda05d",
        "actionRelease": "v4.2.1",
        "requiredJobPermissions": [
            "actions:read",
            "artifact-metadata:write",
            "attestations:write",
            "contents:read",
            "id-token:write",
        ],
        "pullRequestWriteAuthorityAllowed": False,
        "releasePublicationAllowed": False,
        "platformCodeSigningClaimAllowed": False,
        "notarizationClaimAllowed": False,
        "productionReadinessClaimAllowed": False,
    }:
        raise PolicyError("unsafe-artifact-attestation-policy")

    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    )
    validate_workflow = (ROOT / ".github/workflows/validate-pack.yml").read_text(encoding="utf-8")
    for check in expected_checks - {
        "Windows portable package", "Linux portable package", "macOS portable package"
    }:
        if f"name: {check}" not in workflow_text:
            raise PolicyError(f"required-check-not-defined:{check}")
    if "name: ${{ matrix.label }} portable package" not in workflow_text:
        raise PolicyError("portable-package-matrix-not-defined")
    for match in re.finditer(r"^\s*uses:\s*([^#\s]+)", workflow_text, re.MULTILINE):
        reference = match.group(1)
        if reference.startswith("./"):
            continue
        if not re.fullmatch(r"[^@\s]+@[0-9a-f]{40}", reference):
            raise PolicyError(f"action-not-sha-pinned:{reference}")
    upload_artifact = (
        "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    )
    if workflow_text.count(upload_artifact) != 1:
        raise PolicyError("reviewed-node24-upload-artifact-not-pinned")
    setup_python = (
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
    )
    if workflow_text.count(setup_python) != 1:
        raise PolicyError("reviewed-node24-setup-python-not-pinned")
    package_section = workflow_text.split("  package:", 1)[1].split(
        "  attest-development:", 1
    )[0]
    if (
        setup_python not in package_section
        or 'python-version: "3.14.6"' not in package_section
        or package_section.index(setup_python)
        > package_section.index("python -m pip install")
    ):
        raise PolicyError("portable-package-python-not-exact-or-ordered")
    package_identity_markers = {
        "windows-2025": (
            "python-3.14.6-win32-x64.zip",
            "dc722964ab28f81f6a0c753ee960871f045d363568f4fb7626cc02c1e0caa1e9",
        ),
        "ubuntu-24.04": (
            "python-3.14.6-linux-24.04-x64.tar.gz",
            "29dc7f3887a430fe7a0005fee4732b00be1bbed5bf21aa1e43f8d947eb1b9f61",
        ),
        "macos-15": (
            "python-3.14.6-darwin-arm64.tar.gz",
            "7ed5b5c399a38b9b5b1bbb70a454c2ac8b0548cd0610871ea443c4747468e97c",
        ),
    }
    for runner, (asset, digest) in package_identity_markers.items():
        if (
            package_section.count(f"- os: {runner}") != 1
            or package_section.count(f"python_asset: {asset}") != 1
            or package_section.count(f"python_sha256: {digest}") != 1
        ):
            raise PolicyError(f"portable-python-distribution-drift:{runner}")
    if any(
        marker in package_section
        for marker in ("windows-latest", "ubuntu-latest", "macos-latest")
    ):
        raise PolicyError("portable-runner-label-must-be-versioned")
    if (
        "HAVEN42_PYTHON_SOURCE_ASSET: ${{ matrix.python_asset }}"
        not in package_section
        or "HAVEN42_PYTHON_SOURCE_SHA256: ${{ matrix.python_sha256 }}"
        not in package_section
    ):
        raise PolicyError("portable-python-provenance-not-bound")
    download_artifact = (
        "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
    )
    if workflow_text.count(download_artifact) != 1:
        raise PolicyError("reviewed-node24-download-artifact-not-pinned")
    codeql_sha = "f205ea1c3313d32999d8d6a48b4f6530d4437b38"
    if (
        workflow_text.count(f"github/codeql-action/init@{codeql_sha}") != 1
        or workflow_text.count(f"github/codeql-action/analyze@{codeql_sha}") != 1
    ):
        raise PolicyError("reviewed-codeql-action-pair-not-pinned")
    attest = "actions/attest@508db95dd578ae2727ebd6217d5ba78e4fbda05d"
    if workflow_text.count(attest) != 1:
        raise PolicyError("reviewed-attestation-action-not-pinned")
    attestation_markers = {
        "attest-development:",
        "name: Attest unsigned development artifacts",
        "if: github.event_name == 'push' && github.ref == 'refs/heads/main'",
        "needs: package",
        "actions: read",
        "artifact-metadata: write",
        "attestations: write",
        "contents: read",
        "id-token: write",
        "pattern: haven42-*-unsigned-development",
        "Expected exactly three native artifact sets.",
        "subject-path:",
        "haven42-*-unsigned-development.zip",
        "haven42-*-unsigned-development.tar.gz",
    }
    if any(marker not in validate_workflow for marker in attestation_markers):
        raise PolicyError("artifact-attestation-job-incomplete")
    if any(marker in validate_workflow for marker in (
        "pull_request_target:",
        "push-to-registry:",
        "contents: write",
        "packages: write",
        "releases: write",
    )):
        raise PolicyError("artifact-attestation-job-overprivileged")
    if (ROOT / ".github/workflows/package-development.yml").exists():
        raise PolicyError("duplicate-package-workflow")


def gh_json(endpoint: str) -> object:
    result = subprocess.run(
        ["gh", "api", endpoint],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise PolicyError(f"github-api-failed:{endpoint}") from None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise PolicyError(f"github-api-invalid-json:{endpoint}") from error


def verify_live(policy: dict) -> None:
    repository = policy["repository"]
    repo = gh_json(f"repos/{repository}")
    protection = gh_json(f"repos/{repository}/branches/main/protection")
    actions = gh_json(f"repos/{repository}/actions/permissions")
    selected = gh_json(f"repos/{repository}/actions/permissions/selected-actions")
    workflow = gh_json(f"repos/{repository}/actions/permissions/workflow")
    desired_merge = policy["mergePolicy"]
    if (
        repo["default_branch"] != policy["defaultBranch"]
        or repo["allow_merge_commit"] != desired_merge["allowMergeCommit"]
        or repo["allow_squash_merge"] != desired_merge["allowSquashMerge"]
        or repo["allow_rebase_merge"] != desired_merge["allowRebaseMerge"]
        or repo["delete_branch_on_merge"] != desired_merge["deleteBranchOnMerge"]
    ):
        raise PolicyError("live-merge-policy-drift")
    desired = policy["branchProtection"]
    live_checks = {item["context"] for item in protection["required_status_checks"]["checks"]}
    if (
        live_checks != set(desired["requiredChecks"])
        or protection["required_status_checks"]["strict"] != desired["strictStatusChecks"]
        or protection["enforce_admins"]["enabled"] != desired["enforceAdmins"]
        or protection["required_linear_history"]["enabled"] != desired_merge["requiredLinearHistory"]
        or protection["required_conversation_resolution"]["enabled"] != desired["requireConversationResolution"]
        or protection["allow_force_pushes"]["enabled"] != desired["allowForcePushes"]
        or protection["allow_deletions"]["enabled"] != desired["allowDeletions"]
        or protection["required_pull_request_reviews"]["dismiss_stale_reviews"] != desired["dismissStaleReviews"]
        or protection["required_pull_request_reviews"]["require_code_owner_reviews"] != desired["requireCodeOwnerReviews"]
        or protection["required_pull_request_reviews"]["required_approving_review_count"] != desired["requiredApprovingReviewCount"]
    ):
        raise PolicyError("live-branch-protection-drift")
    desired_actions = policy["actions"]
    if (
        actions.get("enabled") != desired_actions["enabled"]
        or actions.get("allowed_actions") != desired_actions["allowedActions"]
        or actions.get("sha_pinning_required") != desired_actions["shaPinningRequired"]
        or selected != {
            "github_owned_allowed": desired_actions["githubOwnedAllowed"],
            "verified_allowed": desired_actions["verifiedAllowed"],
            "patterns_allowed": desired_actions["patternsAllowed"],
        }
        or workflow != {
            "default_workflow_permissions": desired_actions["defaultWorkflowPermissions"],
            "can_approve_pull_request_reviews": desired_actions["canApprovePullRequestReviews"],
        }
    ):
        raise PolicyError("live-actions-policy-drift")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        policy = load_policy()
        verify_static(policy)
        if args.live:
            verify_live(policy)
    except PolicyError as error:
        print(f"GitHub repository policy verification failed: {error}", file=sys.stderr)
        return 2
    print(f"GitHub repository policy verification passed ({'live' if args.live else 'static'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
