#!/usr/bin/env python3
"""Fail-closed, effect-free checks for Haven 42 code-signing readiness."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_VERSION = "0.4.0-alpha.1"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    checks = 0

    def require(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(message)

    policy = read("CODE-SIGNING-POLICY.md")
    privacy = read("PRIVACY.md")
    audit = read("docs/signpath-eligibility-audit.md")
    component_audit = read("docs/windows-package-component-audit.md")
    version_info = read("package/haven42-version-info.txt")
    spec = read("package/haven42.spec")
    workflow = read(".github/workflows/validate-pack.yml")
    signing_workflow = read(".github/workflows/windows-artifact-signing.yml")
    codeowners = read(".github/CODEOWNERS")
    wiki_map = read("config/wiki-sync.tsv")
    readme = read("README.md")
    release = read("docs/release.md")
    builder = read("scripts/build-portable-development-package.py")
    verifier = read("scripts/verify-portable-development-artifacts.py")

    require(
        "does not currently publish or distribute code-signed binaries" in policy,
        "Policy must not claim that signed binaries are published.",
    )
    require(
        "Microsoft Artifact Signing account" in policy
        and "does not authorize a signature, distribution, or Release" in policy
        and "native-validation candidate, not a public release" in policy,
        "Configured signing infrastructure must not grant signing or release authority.",
    )
    require(
        "initial Windows signing scope is only" in policy
        and "`haven42.exe`" in policy,
        "Signing scope must be restricted to the project-owned launcher.",
    )
    require(
        "fresh manual approval" in policy and "digest-bound" in policy,
        "Every future signature must require digest-bound manual approval.",
    )
    require(
        "no telemetry, analytics" in privacy
        and "will not transfer information" in privacy,
        "Privacy policy must preserve the local-first transfer boundary.",
    )
    require(
        "Historical record:" in audit
        and "does not describe Haven 42's current" in audit
        and "signing integration" in audit
        and "No provider correspondence or application outcome" in audit,
        "The earlier provider audit must remain sanitized and clearly historical.",
    )
    require(
        "exact unsigned Windows" in audit
        and "`0.4.0-alpha.1` prerelease" in audit
        and "does not establish provider eligibility" in audit
        and "Provider review required" in audit,
        "Audit must record the public unsigned Alpha without treating it as provider eligibility.",
    )
    require(
        "MFA for repository and signing service | GitHub confirmed; signing service pending enrollment"
        in audit
        and "No authentication proof or secret is recorded" in audit,
        "Audit must record only the owner MFA confirmation and keep provider MFA pending.",
    )
    require(
        "earlier 70-file local build is no longer an admitted candidate"
        in component_audit
        and "replacement clean local build contained 31 files" in component_audit
        and "disposable 41-file Windows package" in component_audit
        and "host-derived contamination" in component_audit
        and "exact packaged dependency/license gate remains" in component_audit,
        "The contaminated Windows build must be rejected while hosted and legal review remain gated.",
    )
    for field, value in (
        ("ProductName", "Haven 42"),
        ("ProductVersion", EXPECTED_VERSION),
        ("FileVersion", EXPECTED_VERSION),
        ("OriginalFilename", "haven42.exe"),
    ):
        require(
            f'StringStruct("{field}", "{value}")' in version_info,
            f"Windows metadata must pin {field}.",
        )
    require(
        'sys.platform == "win32"' in spec and "version=version_info" in spec,
        "PyInstaller must apply version metadata only to the Windows executable.",
    )
    require(
        "validate_windows_executable_metadata(package_dir)" in builder
        and '"runtime-component-inventory.json"' in builder
        and '"CPYTHON-3.14.6-LICENSE.txt"' in builder
        and '"APACHE-2.0.txt"' in builder
        and '"LIBFFI-3.4.4-LICENSE.txt"' in builder
        and '"OLLAMA-MIT-LICENSE.txt"' in builder
        and "runtime-component-inventory-mismatch" in verifier,
        "The package build must verify Windows metadata, runtime coverage, and license evidence.",
    )
    require(
        not re.search(r"(?i)signpath|codesign|signtool|notarytool", workflow),
        "The development workflow must not activate a signing service or platform signer.",
    )
    require(
        "workflow_dispatch:" in signing_workflow
        and "environment: windows-signing" in signing_workflow
        and "id-token: write" in signing_workflow
        and "AZURE_CLIENT_SECRET" not in signing_workflow,
        "The signing workflow must be manual, approval protected, and OIDC only.",
    )
    require(
        "\\bundle\\haven42\\haven42.exe" in signing_workflow
        and "files-folder:" not in signing_workflow
        and "releasePublished = $false" in signing_workflow,
        "The signing workflow must sign only the launcher and deny release publication.",
    )
    require(
        "/CODE-SIGNING-POLICY.md @hysel" in codeowners
        and "/package/haven42-version-info.txt @hysel" in codeowners,
        "Signing policy and executable identity must remain code-owner protected.",
    )
    require(
        "CODE-SIGNING-POLICY.md\tEng-Code-Signing-Policy.md" in wiki_map
        and "PRIVACY.md\tPrivacy-Policy.md" in wiki_map
        and "docs/signpath-eligibility-audit.md\tEng-SignPath-Eligibility-Audit.md"
        in wiki_map,
        "Signing and privacy pages must be mapped to the public wiki.",
    )
    require(
        "[code signing policy](code-signing-policy.md)" in readme.lower()
        and "[privacy policy](privacy.md)" in readme.lower(),
        "Repository home must link the public signing and privacy policies.",
    )
    require(
        "[Code signing policy](https://github.com/hysel/haven-42/blob/main/CODE-SIGNING-POLICY.md)" in release
        and "public downloads remain unsigned development artifacts" in release
        and "candidate is not a Release" in release,
        "Release guidance must distinguish native signing validation from publication.",
    )
    if checks != 22:
        raise AssertionError(f"Expected 22 checks, executed {checks}.")
    print("Code-signing readiness self-test passed: 22 effect-free checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
