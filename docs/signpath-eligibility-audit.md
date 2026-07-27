# SignPath Foundation Eligibility Audit

Audit date: 2026-07-27

This is a sanitized repository-readiness audit, not a SignPath Foundation
application, acceptance, certificate, signature, or legal conclusion. The
authoritative conditions are published by
<https://signpath.org/terms.html>.

No certificate, signing service, or signing workflow is active.

## Result

**Not currently eligible to request production signing.**

The public repository has version tags through `v0.3.0`, but the authoritative
GitHub Release API reported no published Releases and no downloadable release
assets at audit time. SignPath requires a project to be released already in
the form that should be signed. Haven 42 also remains explicitly
unsigned-development-only, and public Release publication requires a separate
owner decision.

The Windows executable also lacked product and version metadata at the start
of this audit. Deterministic metadata is now defined in
`package/haven42-version-info.txt`. A local unsigned Windows rebuild confirmed
ProductName and FileDescription `Haven 42`, ProductVersion and FileVersion
`0.3.0`, CompanyName `Haven 42 open-source project`, and OriginalFilename
`haven42.exe`; the archive/evidence verifier and native portable parity,
relocation, read-only, recovery, lifecycle, port-collision, shutdown,
hostile-environment, and integrity tests passed. Hosted native evidence for
the eventual immutable candidate remains required.

## Eligibility Matrix

| Requirement | State | Evidence or remaining work |
| --- | --- | --- |
| OSI-approved project license without commercial dual licensing | Confirmed for Haven 42 source | Root `LICENSE` is MIT. |
| No proprietary project code | Confirmed for tracked Haven 42 source; packaged dependency review pending | Tracked source is MIT. The embedded runtime and every packaged native library still require final license/notices review for the exact candidate archive. |
| No malware or potentially unwanted behavior | External review required | CodeQL, privacy scanning, strict package integrity, and hostile tests exist, but only SignPath can decide eligibility. |
| Actively maintained | Confirmed by repository history | Current `main` activity and maintained documentation exist. |
| Existing release in the form to sign | Blocked | Tags exist, but GitHub reported zero published Releases/assets. Do not publish one without explicit approval. |
| Functionality documented on download/release page | Partially satisfied | README and package documentation are detailed; no public binary download/release page exists. |
| Project team owns source and build scripts | Confirmed | Authoritative repository and build definitions are maintained by `@hysel`. |
| Sign only project-owned binaries | Policy defined; local Windows identity verified | Initial scope is only `haven42.exe`; upstream Python/PyInstaller/system libraries are excluded from signing scope. Provider artifact configuration remains external. |
| No hacking-tool runtime | Likely satisfied; external decision required | End-user runtime provides local AI and read-only evidence/setup functions. Security scanning is limited to development/build validation rather than active exploitation. |
| User privacy and security | Policy defined | `PRIVACY.md`, `SECURITY.md`, and the loopback/runtime policy document explicit user-requested network effects and no telemetry. |
| Announce system changes and provide uninstall | Confirmed for portable development form | There is no installer or automatic machine modification; removal is deletion of the extracted application directory. |
| MFA for repository and signing service | GitHub confirmed; signing service pending enrollment | The repository owner confirmed GitHub MFA is enabled on 2026-07-27. Enable signing-service MFA during any later enrollment. No authentication proof or secret is recorded. |
| Author, reviewer, and approver roles | Defined; provider review pending | `CODE-SIGNING-POLICY.md` names the current maintainer roles. SignPath decides whether the project structure is acceptable. |
| Public code-signing policy and privacy statement | Prepared | `CODE-SIGNING-POLICY.md` and `PRIVACY.md`. The SignPath provider sentence is explicitly marked planned until acceptance. |
| Product and version metadata | Local Windows gate passed; hosted candidate pending | ProductName `Haven 42`, ProductVersion/FileVersion `0.3.0`, and `haven42.exe` identity were emitted and independently parsed from the rebuilt executable. |
| Verifiable automated build | Development evidence available | Hash-locked inputs, exact source SHA, native package matrix, checksums, inventory, notices, SBOM, provenance, and prepared GitHub attestation exist. SignPath configuration remains external. |
| Manual approval for every signing request | Policy defined; service not configured | Every future request is digest- and release-bound and requires manual approval. |

## Dependency Boundary

The build allowlist currently records PyInstaller, its hooks, packaging,
setuptools, altgraph, and platform helpers under MIT, BSD, Apache, or
GPL-with-bootloader-exception expressions. The package also embeds CPython and
platform-native libraries selected by PyInstaller.

Before applying:

1. enumerate every non-system binary in the exact Windows archive;
2. map each binary to source, version, license, and notice;
3. distinguish system libraries from bundled upstream components;
4. confirm no proprietary maintainer component is present;
5. exclude every upstream executable/library from Haven 42 signing scope; and
6. have the final license inventory reviewed as eligibility evidence, not legal
   advice.

The existing SBOM and notices are development evidence and must not be
described as complete production legal clearance.

The current 70-file Windows candidate is categorized in
`docs/windows-package-component-audit.md`. Exact component evidence now binds
every file to Haven 42 or an explicit upstream/runtime group, rejects
unclassified files, expands the SBOM, and marks all upstream components
ineligible for Haven 42 signing. The audit confirmed CPython 3.14.6, OpenSSL
3.5.7, and libffi 3.4.4 identities and isolated the Microsoft
API-set/UCRT/runtime files as the highest-priority provenance and
redistribution review. CPython 3.14.6 bundled license evidence, Apache 2.0
text, and the exact libffi 3.4.4 MIT license are now hash-verified artifact
evidence. The official Python installer/SBOM, immutable CPython source commit,
and libffi/OpenSSL source and binary dependency commits are recorded in the
runtime inventory. The previous local package was then rejected because 39
UCRT/API-set files came from an unrelated JDK on the host path. The classifier
now bans those files. Both retained Visual C++ runtime DLLs match the
hash-verified official Python.org embeddable distribution, but applicable
Microsoft redistribution terms and clean hosted reproduction remain
incomplete. The replacement 31-file local build passed independent artifact
verification and the native package gate, but the promotion gate remains
blocked rather than inferred from successful local packaging.

Hosted Python input provenance is now exact for the three pinned native
runners: the official `actions/python-versions` 3.14.6 release tag, archive
name, and SHA-256 are workflow-bound and recorded in build provenance. This
reduces source ambiguity but does not replace the remaining component-level
redistribution review.

## Required Owner Actions

Before an application:

1. decide whether to approve one public unsigned development Release in the
   exact form proposed for later signing;
2. identify any additional public reviewer or signing approver if available;
3. review the public privacy and code-signing policies;
4. approve submitting the application and the information it will disclose;
   and
5. enable signing-service MFA during enrollment if the provider accepts the
   project.

Do not provide credentials, recovery codes, tokens, approval links, or private
signing material to repository files, issues, logs, or assistants.

## Required Technical Work

Before application submission:

1. repeat the successful Windows metadata, package inventory, checksums, SBOM,
   notices, provenance, and native-browser gate on the final immutable
   candidate;
2. complete the exact packaged dependency/license audit;
3. run the full cross-platform gate on the final candidate tree;
4. publish only after a separate explicit owner decision; and
5. confirm the prepared GitHub build-provenance job succeeds for the exact
   public artifact.

SignPath configuration, artifact rules, manual signing approval, and
post-signature verification remain future gates after provider acceptance.
