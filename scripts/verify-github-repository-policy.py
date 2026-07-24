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
        "branchProtection", "actions",
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
    if not isinstance(checks, list) or len(checks) != len(set(checks)) or len(checks) != 8:
        raise PolicyError("invalid-required-checks")
    expected_checks = {
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

    workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    )
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
