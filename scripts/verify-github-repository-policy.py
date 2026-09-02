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


def workflow_jobs(text: str, name: str) -> list[tuple[str, str]]:
    marker = "\njobs:\n"
    if marker not in text:
        raise PolicyError(f"workflow-jobs-missing:{name}")
    section = text.split(marker, 1)[1]
    matches = list(re.finditer(r"(?m)^  ([a-z0-9][a-z0-9-]*):\s*$", section))
    if not matches:
        raise PolicyError(f"workflow-jobs-missing:{name}")
    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        result.append((match.group(1), section[match.start():end]))
    return result


def verify_workflow_safety(workflows: dict[str, str]) -> None:
    if set(workflows) != {
        "alpha-usage-report.yml", "alpha2-candidate.yml", "codeql.yml",
        "validate-pack.yml", "windows-artifact-signing.yml",
    }:
        raise PolicyError("unexpected-workflow-inventory")
    combined = "\n".join(workflows[name] for name in sorted(workflows))
    for name, text in workflows.items():
        header = text.split("\njobs:\n", 1)[0]
        expected_cancel = "false" if name == "windows-artifact-signing.yml" else "true"
        if not re.search(
            rf"(?ms)^concurrency:\s*\n\s+group:\s*\S.+\n\s+cancel-in-progress:\s*{expected_cancel}\s*$",
            header,
        ):
            raise PolicyError(f"workflow-concurrency-unbounded:{name}")
        if not re.search(r"(?ms)^permissions:\s*\n(?:  [a-z-]+:\s*(?:read|write)\s*\n?)+", header):
            raise PolicyError(f"workflow-permissions-missing:{name}")
        for job_id, block in workflow_jobs(text, name):
            if not re.search(r"(?m)^    runs-on:\s*.+\s*$", block):
                raise PolicyError(f"workflow-runner-missing:{name}:{job_id}")
            timeout = re.search(r"(?m)^    timeout-minutes:\s*([0-9]+)\s*$", block)
            if not timeout or not 1 <= int(timeout.group(1)) <= 30:
                raise PolicyError(f"workflow-timeout-invalid:{name}:{job_id}")
    checkout_blocks = [
        block
        for text in workflows.values()
        for block in re.findall(
            r"(?ms)^\s+- name:.*?\n\s+uses:\s+actions/checkout@[0-9a-f]{40}.*?(?=^\s+- name:|\Z)",
            text,
        )
    ]
    if not checkout_blocks or any(
        not re.search(r"(?m)^\s+persist-credentials:\s*false\s*$", block)
        for block in checkout_blocks
    ):
        raise PolicyError("checkout-credentials-persisted")
    forbidden_permissions = (
        "actions", "administration", "contents", "deployments", "packages",
        "pull-requests", "releases",
    )
    if any(re.search(rf"(?m)^\s+{field}:\s*write\s*$", combined) for field in forbidden_permissions):
        raise PolicyError("workflow-write-permission-forbidden")
    if any(marker in combined.lower() for marker in (
        "gh release create", "softprops/action-gh-release", "ncipollo/release-action",
    )):
        raise PolicyError("release-publication-enabled")
    upload_blocks = [
        block
        for text in workflows.values()
        for block in re.findall(
            r"(?ms)^\s+- name:.*?\n\s+uses:\s+actions/upload-artifact@[0-9a-f]{40}.*?(?=^\s+- name:|\Z)",
            text,
        )
    ]
    if len(upload_blocks) != 6:
        raise PolicyError("unexpected-artifact-upload-count")
    package_uploads = [block for block in upload_blocks if "unsigned-development" in block]
    report_uploads = [block for block in upload_blocks if "alpha-usage-report" in block]
    candidate_uploads = [block for block in upload_blocks if "alpha2-" in block]
    signing_uploads = [block for block in upload_blocks if "signing-request" in block or "signed-native-validation-candidate" in block]
    if (
        len(package_uploads) != 1
        or len(report_uploads) != 1
        or len(candidate_uploads) != 2
        or len(signing_uploads) != 2
        or not re.search(r"(?m)^\s+retention-days:\s*7\s*$", package_uploads[0])
        or not re.search(r"(?m)^\s+if-no-files-found:\s*error\s*$", package_uploads[0])
        or not re.search(r"(?m)^\s+retention-days:\s*30\s*$", report_uploads[0])
        or not re.search(r"(?m)^\s+if-no-files-found:\s*error\s*$", report_uploads[0])
        or any(not re.search(r"(?m)^\s+retention-days:\s*7\s*$", block) for block in candidate_uploads)
        or any(not re.search(r"(?m)^\s+if-no-files-found:\s*error\s*$", block) for block in candidate_uploads)
        or any(not re.search(r"(?m)^\s+retention-days:\s*3\s*$", block) for block in signing_uploads)
        or any(not re.search(r"(?m)^\s+if-no-files-found:\s*error\s*$", block) for block in signing_uploads)
    ):
        raise PolicyError("unsafe-artifact-upload-policy")
    report_workflow = workflows["alpha-usage-report.yml"]
    required_report_markers = {
        "name: Alpha Usage Report",
        "workflow_dispatch:",
        'cron: "41 7 * * 1"',
        "group: alpha-usage-report-${{ github.workflow }}",
        "contents: read",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 5",
        "persist-credentials: false",
        "HAVEN42_GITHUB_REPORT_TOKEN: ${{ github.token }}",
        "python scripts/generate-github-alpha-usage-report.py",
        'cat dist/alpha-usage-report/alpha-usage-report.md >> "$GITHUB_STEP_SUMMARY"',
        "name: haven42-alpha-usage-report-${{ github.run_id }}",
        "path: dist/alpha-usage-report/",
        "if-no-files-found: error",
        "retention-days: 30",
    }
    if any(marker not in report_workflow for marker in required_report_markers):
        raise PolicyError("alpha-usage-report-workflow-incomplete")
    candidate_workflow = workflows["alpha2-candidate.yml"]
    required_candidate_markers = {
        "name: Alpha 2 Candidate",
        "workflow_dispatch:",
        "group: alpha2-candidate-${{ github.workflow }}-${{ github.ref }}",
        "contents: read",
        "runs-on: ${{ matrix.os }}",
        "runs-on: ubuntu-24.04",
        "timeout-minutes: 25",
        "timeout-minutes: 10",
        "persist-credentials: false",
        'python-version: "3.14.6"',
        "--release-line alpha2",
        "--expected-version 0.4.0-alpha.2",
        "--verify-only",
        "--expected-commit ${{ github.event.pull_request.head.sha || github.sha }}",
        "name: haven42-alpha2-${{ matrix.platform }}-candidate",
        "name: haven42-alpha2-candidate-pair-verification",
        "retention-days: 7",
    }
    if any(marker not in candidate_workflow for marker in required_candidate_markers):
        raise PolicyError("alpha2-candidate-workflow-incomplete")
    candidate_header = candidate_workflow.split("\njobs:\n", 1)[0]
    if (
        "pull_request_target:" in candidate_header
        or re.search(r"(?m)^\s+push:\s*$", candidate_header)
        or "contents: write" in candidate_workflow
        or "id-token: write" in candidate_workflow
        or "secrets." in candidate_workflow
        or any(marker in candidate_workflow.lower() for marker in (
            "gh release create", "softprops/action-gh-release", "ncipollo/release-action",
        ))
    ):
        raise PolicyError("alpha2-candidate-workflow-overprivileged")
    report_header = report_workflow.split("\njobs:\n", 1)[0]
    if (
        "pull_request:" in report_header
        or "pull_request_target:" in report_header
        or re.search(r"(?m)^\s+push:\s*$", report_header)
        or "contents: write" in report_workflow
        or "issues: write" in report_workflow
        or "actions: write" in report_workflow
        or "secrets." in report_workflow
    ):
        raise PolicyError("alpha-usage-report-workflow-overprivileged")


def load_policy() -> dict:
    try:
        value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PolicyError("invalid-policy-json") from error
    required = {
        "schemaVersion", "repository", "defaultBranch", "mergePolicy",
        "branchProtection", "actions", "artifactAttestations", "artifactSigning",
        "usageReports",
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
        "patternsAllowed": [
            "Azure/artifact-signing-action@*",
            "Azure/login@*",
        ],
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
        "actionCommit": "1e69f48acb82d1966a394da916b4c1698aa569d6",
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
    if policy["artifactSigning"] != {
        "enabled": True,
        "provider": "microsoft-artifact-signing",
        "workflow": "windows-artifact-signing.yml",
        "trigger": "manual",
        "environment": "windows-signing",
        "allowedSourceBranch": "main",
        "signingScope": "haven42.exe-only",
        "authentication": "github-oidc",
        "expectedSignerSubjectSource": "windows-signing-environment-variable",
        "expectedSignerSubjectMatch": "exact-ordinal",
        "candidateRetentionDays": 3,
        "releasePublicationAllowed": False,
    }:
        raise PolicyError("unsafe-artifact-signing-policy")
    if policy["usageReports"] != {
        "enabled": True,
        "workflow": "alpha-usage-report.yml",
        "triggers": ["weekly", "manual"],
        "permissions": ["contents:read"],
        "repositoryData": "aggregate-only",
        "downloaderIdentityCollected": False,
        "reportRetentionDays": 30,
        "commitsReportsToRepository": False,
    }:
        raise PolicyError("unsafe-usage-report-policy")

    workflows = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    }
    verify_workflow_safety(workflows)
    workflow_text = "\n".join(workflows[name] for name in sorted(workflows))
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
    if workflow_text.count(upload_artifact) != 6:
        raise PolicyError("reviewed-node24-upload-artifact-not-pinned")
    setup_python = (
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97"
    )
    if workflow_text.count(setup_python) != 4:
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
    if workflow_text.count(download_artifact) != 3:
        raise PolicyError("reviewed-node24-download-artifact-not-pinned")
    codeql_sha = "cdf488f595d80d6e07e03d4674febd5ab45fa938"
    if (
        workflow_text.count(f"github/codeql-action/init@{codeql_sha}") != 1
        or workflow_text.count(f"github/codeql-action/analyze@{codeql_sha}") != 1
    ):
        raise PolicyError("reviewed-codeql-action-pair-not-pinned")
    attest = "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6"
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


def run_self_tests() -> int:
    workflows = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted((ROOT / ".github/workflows").glob("*.yml"))
    }
    cases = (
        ("cancel-in-progress: true", "cancel-in-progress: false", "workflow-concurrency-unbounded"),
        ("timeout-minutes: 10", "timeout-minutes: 0", "workflow-timeout-invalid"),
        ("persist-credentials: false", "persist-credentials: true", "checkout-credentials-persisted"),
        ("contents: read", "contents: write", "workflow-write-permission-forbidden"),
        ("retention-days: 7", "retention-days: 90", "unsafe-artifact-upload-policy"),
        ("if-no-files-found: error", "if-no-files-found: warn", "unsafe-artifact-upload-policy"),
        ('cron: "41 7 * * 1"', 'cron: "* * * * *"', "alpha-usage-report-workflow-incomplete"),
        (
            "HAVEN42_GITHUB_REPORT_TOKEN: ${{ github.token }}",
            "HAVEN42_GITHUB_REPORT_TOKEN: ${{ secrets.REPORT_TOKEN }}",
            "alpha-usage-report-workflow-incomplete",
        ),
        ("retention-days: 30", "retention-days: 365", "unsafe-artifact-upload-policy"),
    )
    checks = 0
    for old, new, expected in cases:
        hostile = dict(workflows)
        target = next((name for name, text in hostile.items() if old in text), None)
        if target is None:
            raise AssertionError(f"self-test marker missing: {old}")
        hostile[target] = hostile[target].replace(old, new, 1)
        try:
            verify_workflow_safety(hostile)
        except PolicyError as error:
            if expected not in str(error):
                raise AssertionError(f"expected {expected}, received {error}") from error
            checks += 1
        else:
            raise AssertionError(f"unsafe workflow accepted: {expected}")
    release_hostile = dict(workflows)
    release_hostile["validate-pack.yml"] += "\n# gh release create forbidden\n"
    try:
        verify_workflow_safety(release_hostile)
    except PolicyError as error:
        if str(error) != "release-publication-enabled":
            raise AssertionError(f"unexpected release rejection: {error}") from error
        checks += 1
    else:
        raise AssertionError("release publication marker was accepted")
    return checks


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
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        policy = load_policy()
        verify_static(policy)
        checks = run_self_tests() if args.self_test else 0
        if args.live:
            verify_live(policy)
    except PolicyError as error:
        print(f"GitHub repository policy verification failed: {error}", file=sys.stderr)
        return 2
    scope = "live" if args.live else "static"
    suffix = f" with {checks} hostile checks" if args.self_test else ""
    print(f"GitHub repository policy verification passed ({scope}{suffix}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
