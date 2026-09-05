#!/usr/bin/env python3
"""Fail-closed static checks for the manual Windows Artifact Signing workflow."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "windows-artifact-signing.yml"


def main() -> int:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    trigger = workflow.split("permissions:", 1)[0]
    require("workflow_dispatch:" in trigger, "Signing must require manual dispatch.")
    require(
        not re.search(r"(?m)^\s{2}(push|pull_request|pull_request_target|release|schedule):", trigger),
        "No automatic or pull-request signing trigger is allowed.",
    )
    require(
        "source_commit:" in trigger
        and "Exact 40-character commit SHA from main" in trigger,
        "The workflow must require an explicit immutable source commit.",
    )
    require(
        re.search(r"(?m)^permissions:\n  contents: read$", workflow) is not None,
        "Global workflow authority must remain read-only.",
    )
    require(
        "group: windows-artifact-signing" in workflow
        and "cancel-in-progress: false" in workflow,
        "Signing requests must be serialized and must not cancel one another.",
    )
    require(
        "git merge-base --is-ancestor $actual origin/main" in workflow,
        "The selected source must be verified as reachable from main.",
    )
    require(
        workflow.count("persist-credentials: false") == 2,
        "Both jobs must check out source without retaining Git credentials.",
    )
    require(
        "--require-hashes -r package/requirements-build.txt" in workflow,
        "Build dependencies must remain hash locked.",
    )
    for command in (
        "scripts/test-portable-build-provenance.py",
        "scripts/test-portable-package.py",
        "scripts/test-haven42-web-browser.mjs",
        "scripts/verify-portable-development-artifacts.py",
    ):
        require(command in workflow, f"Missing pre-sign validation: {command}")
    require(
        "unsignedSha256 = $digest" in workflow
        and "publicationAuthorized = $false" in workflow,
        "The approval packet must bind the unsigned digest and deny publication.",
    )
    require(
        "environment: windows-signing" in workflow,
        "The signing job must use the protected manual-approval environment.",
    )
    sign_job = workflow.split("  sign-approved-candidate:", 1)[1]
    require(
        "needs: prepare-unsigned-candidate" in sign_job,
        "Signing must wait for the approval packet.",
    )
    require(
        re.search(r"(?m)^    permissions:\n      contents: read\n      id-token: write$", sign_job)
        is not None,
        "Only the signing job may request an OIDC token.",
    )
    require(
        workflow.count("id-token: write") == 1,
        "OIDC authority must exist only in the protected signing job.",
    )
    require(
        "azure/login@7ddb5af1ef8758cf1353cf3b42f940aee27ba21c" in sign_job,
        "Azure login must be pinned to the reviewed v3 commit.",
    )
    require(
        "azure/artifact-signing-action@c7ab2a863ab5f9a846ddb8265964877ef296ee82"
        in sign_job,
        "Artifact Signing must be pinned to the reviewed v2 commit.",
    )
    require(
        all(
            f"secrets.{name}" in sign_job
            for name in ("AZURE_CLIENT_ID", "AZURE_TENANT_ID", "AZURE_SUBSCRIPTION_ID")
        )
        and "AZURE_CLIENT_SECRET" not in workflow
        and "azure-client-secret" not in workflow,
        "Authentication must use OIDC without a reusable client secret.",
    )
    require(
        "HAVEN42_EXPECTED_SIGNER_SUBJECT: ${{ vars.WINDOWS_EXPECTED_SIGNER_SUBJECT }}"
        in sign_job
        and "Require the approved publisher identity before signing" in sign_job
        and sign_job.index("Require the approved publisher identity before signing")
        < sign_job.index("Sign only the Haven 42-owned launcher"),
        "An exact approved publisher identity must be configured before paid signing.",
    )
    require(
        "endpoint: https://eus.codesigning.azure.net/" in sign_job
        and "signing-account-name: haven42-artifact-signing" in sign_job
        and "certificate-profile-name: haven42-public-release" in sign_job,
        "The action must target the admitted East US account and profile.",
    )
    require(
        "files: ${{ github.workspace }}\\dist\\approved-input\\bundle\\haven42\\haven42.exe"
        in sign_job,
        "The signing action must receive exactly the project-owned launcher path.",
    )
    require(
        "files-folder:" not in sign_job
        and "files-folder-filter:" not in sign_job
        and "files-folder-recurse:" not in sign_job,
        "Directory-wide or recursive signing is prohibited.",
    )
    require(
        "file-digest: SHA256" in sign_job
        and "timestamp-rfc3161: http://timestamp.acs.microsoft.com" in sign_job
        and "timestamp-digest: SHA256" in sign_job,
        "The signature must use SHA-256 and the Artifact Signing timestamp service.",
    )
    require(
        "$signature.Status -ne 'Valid'" in sign_job
        and "$null -eq $signature.TimeStamperCertificate" in sign_job,
        "Post-sign verification must require a valid timestamped Authenticode signature.",
    )
    require(
        "[System.StringComparison]::Ordinal" in sign_job
        and "SignerCertificate.Subject, $expectedSubject" in sign_job
        and "expectedSignerSubjectMatched = $true" in sign_job,
        "Post-sign verification must match the exact approved publisher identity.",
    )
    require(
        "Haven 42 signed native-validation candidate." in sign_job
        and "Only the project-owned haven42.exe launcher is signed" in sign_job
        and "candidateArchiveSha256 = $candidateArchiveDigest" in sign_job,
        "The signed ZIP must carry accurate candidate metadata and an external digest record.",
    )
    require(
        "releasePublished = $false" in sign_job
        and "distributionAuthorized = $false" in sign_job
        and "productionReady = $false" in sign_job,
        "Signing evidence must not grant publication, distribution, or production authority.",
    )
    require(
        "retention-days: 3" in workflow,
        "Candidate artifacts must have short retention.",
    )
    require(
        not re.search(r"(?i)gh\s+release|create-release|upload-release-asset|contents:\s*write", workflow),
        "The signing workflow must not create or modify a GitHub Release.",
    )
    require(
        checks == 31,
        f"Expected 31 signing-workflow checks, executed {checks}.",
    )
    print("Windows Artifact Signing workflow self-test passed: 31 fail-closed checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
