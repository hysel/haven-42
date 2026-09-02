# Code Signing Policy

## Status

Haven 42 does not currently publish or distribute code-signed binaries.
Current public portable packages are unsigned development artifacts. A
Microsoft Artifact Signing account, Public Trust certificate profile, and
keyless GitHub OIDC identity are configured for Windows candidate validation.
That configuration does not authorize a signature, distribution, or Release.

The repository's manual signing workflow may sign one exact `haven42.exe` from
an immutable commit on `main` only after the owner reviews its unsigned SHA-256
and approves the protected `windows-signing` environment. The environment must
also define the exact reviewed certificate subject; any different signer fails
closed after signing and cannot become a retained candidate. Its short-lived
output is a native-validation candidate, not a public release. Publication
remains a separate owner decision after every promotion gate passes.

## Project And Repository

- Project: Haven 42
- Authoritative source: <https://github.com/hysel/haven-42>
- License: MIT
- Maintainer, committer, and reviewer for external contributions:
  [@hysel](https://github.com/hysel)
- Signing approver after a signing service is admitted:
  [@hysel](https://github.com/hysel)

Every team member with source or signing authority must use multi-factor
authentication for both GitHub and the signing service. No maintainer may share
credentials, approval links, tokens, recovery codes, or private signing
material.

## Eligible Artifact Scope

The initial Windows signing scope is only the Haven 42-owned
`haven42.exe` launcher built from the authoritative repository at one immutable
commit. Product name, product version, file version, original filename, and
description metadata must match the release manifest and be enforced by the
signing artifact configuration.

The following are not eligible under this policy:

- pull-request artifacts;
- dirty, local-only, branch-tip, or moving-reference builds;
- Python, PyInstaller, system, or other upstream executables and libraries;
- models, model runtimes, GPU drivers, services, or third-party providers;
- arbitrary paths or files supplied by a workflow caller;
- debug, test, recovery, or privately modified binaries;
- installers, updaters, Tauri/Rust packages, or additional executables until
  separately admitted; and
- any artifact lacking exact checksums, dependency inventory, notices, SBOM,
  provenance, and successful required checks.

Unsigned upstream open-source libraries may be packaged only when their
license and notices are reviewed. They must not be signed with Haven 42's
project authorization.

## Build And Approval Requirements

Every future signing request must:

1. originate from an immutable protected release source revision;
2. use the repository-owned build scripts and exact hash-locked dependencies;
3. pass privacy, CodeQL, Windows, Linux, macOS, package-integrity, and native
   smoke gates for that exact source revision;
4. produce strict package inventory, SHA-256 checksums, dependency inventory,
   third-party notices, CycloneDX SBOM, and build provenance;
5. match the approved Haven 42 product name and one release version across
   executable metadata, archive names, manifests, and evidence;
6. be requested through the admitted signing service without exporting a
   private signing key;
7. receive a fresh manual approval for that exact artifact digest and release;
8. be verified after signing, including expected publisher, digest, timestamp,
   metadata, and signature-chain checks; and
9. remain unpublished until the separately approved release gate passes.

Approval is single-release and digest-bound. It cannot be remembered, replayed,
transferred to another artifact, or inferred from a prior successful build.
Source authorship, CI success, build provenance, and an artifact attestation do
not by themselves approve code signing.

## Pull Requests And Untrusted Contributions

Pull requests receive no signing, OIDC signing-service, certificate, Release,
package-write, or repository-content-write authority. Changes proposed by
non-committers require maintainer review before merge. Security-sensitive
changes to workflows, package specifications, metadata, signing policy,
privacy policy, release automation, updater policy, or verification logic
require focused review even when authored by a committer.

Signing is never triggered by `pull_request_target`, issue text, comments,
labels, forks, model output, renderer data, arbitrary workflow input, or a
moving branch reference.

## Privacy And System Effects

Haven 42's runtime privacy behavior is documented in the repository
[privacy policy](https://github.com/hysel/haven-42/blob/main/PRIVACY.md).
The program does not transfer information to another networked system unless
the user specifically requests or configures that operation. It contains no
telemetry or advertising.

The portable development package has no installer and requires no
administrator access, system service, startup entry, firewall change, driver,
or global Python installation. Removal consists of closing Haven 42 and
deleting the extracted application directory. User-owned providers, models,
generated files, and exported content remain separate and are not silently
removed.

No signed artifact may add a machine effect, data transfer, installation,
update, persistence, or privilege that was absent from its reviewed source and
disclosed release scope.

## Key And Service Security

Haven 42 will not store a code-signing private key in the repository, GitHub
Actions secrets, workflow artifacts, maintainer workstations, or release
archives when using a managed signing service. Signing-service access must use
the provider's protected key custody, least-privilege identities, MFA, and
manual approval controls.

Signing logs and attestations must exclude credentials, private endpoints,
machine paths, user files, prompts, model output, and local identities.

## Incident Response And Revocation

Immediately stop signing and block publication when:

- a signing identity, maintainer account, workflow, dependency, build runner,
  release artifact, or verification result may be compromised;
- an unauthorized artifact is signed or requested;
- signed bytes do not match the approved digest or source revision;
- malware, unwanted behavior, privacy violations, or undisclosed system
  effects are credibly reported; or
- a required promotion gate is bypassed or becomes invalid.

Preserve sanitized evidence, notify the signing provider, revoke or suspend the
affected authorization when appropriate, rotate compromised credentials,
publish a security advisory when safe, and supersede affected artifacts with a
new immutable version. Published tags and signed artifacts are never silently
rewritten.

Security reports follow the repository
[security policy](https://github.com/hysel/haven-42/security/policy) and must not
be filed with secrets or private user data in a public issue.

## Policy Changes

Every material policy change requires repository review and the complete
required CI gate. A policy change cannot retroactively authorize an existing
artifact. The admitted managed signing provider's current conditions and
technical constraints take precedence for any artifact signed through its
certificate.
