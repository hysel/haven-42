# Core update cryptographic verifier review

Reviewed on 2026-08-04. This is a dependency and security recommendation for a
future updater verifier. It does not add a dependency, trusted identity, trust
root, signing key, online check, download path, staging path, or activation
authority.

## Candidate mechanisms

| Candidate | Platform | Benefit | Security and packaging cost | Decision |
| --- | --- | --- | --- | --- |
| Windows `WinVerifyTrust` with the Authenticode policy provider | Windows | Native publisher and file-integrity verification with no bundled crypto library | Requires exact noninteractive flags, zero-only success handling, chain-policy and revocation decisions, signed fixture coverage, and protection against verification/use races | Preferred platform-signature candidate after native code and signed fixtures exist |
| Apple Security framework static-code validation with an explicit designated requirement | macOS | Native signature, sealed-resource, and signer-requirement validation | Must check all architectures, bind the designated requirement, avoid mutable/network filesystems, and still satisfy notarization and physical-Mac gates | Preferred platform-signature candidate after signing and physical-Mac evidence exist |
| Sigstore bundle verification through a pinned Cosign verifier | Windows, Linux, macOS | Offline bundle verification can bind artifact digest, certificate identity and issuer, signed timestamps, and transparency evidence | Adds a separately distributed Go binary and trust-root lifecycle; its own binary, license, SBOM, provenance, bundle format, identity, issuer, and root must be pinned and verified | Preferred cross-platform research candidate, not admitted |
| `sigstore-python` | Windows, Linux, macOS | Python-native Sigstore client from the official project | Adds a substantial runtime dependency graph to the currently standard-library application and would require complete lock, license, vulnerability, bundle, and package evidence | Do not admit automatically; reconsider only if a native helper proves worse |
| `sigstore-rs` or Tauri/Rust integration | Windows, Linux, macOS | Potential future native integration | The official Sigstore organization still describes the Rust client as beta, and Haven 42 keeps Tauri/Rust unadmitted | Rejected for the current architecture |

The native references are Microsoft's
[`WinVerifyTrust`](https://learn.microsoft.com/en-us/windows/win32/api/wintrust/nf-wintrust-winverifytrust)
documentation and Apple's
[`SecStaticCodeCheckValidity`](https://developer.apple.com/documentation/security/secstaticcodecheckvalidity%28_%3A_%3A_%3A%29)
and [code-signing requirement](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements)
guidance. Sigstore documents identity-and-issuer-bound blob verification and
offline-capable bundles in its
[verification guide](https://docs.sigstore.dev/cosign/verifying/verify/).
The official [Cosign repository](https://github.com/sigstore/cosign) identifies
the project as Apache-2.0 and documents offline verification; a future exact
version still needs a new immutable-source, license, vulnerability, and
bootstrap review.

## Recommendation

Keep the current structural contracts dependency-free and inactive. A future
native verifier should expose one bounded receipt format to Haven 42 while
using platform verification for the signed application package and an offline
Sigstore bundle for cross-platform release provenance. Linux requires the
cross-platform verifier because it has no single native application-signature
policy equivalent to Windows Authenticode or macOS code signing.

Do not shell out to an unpinned verifier found on `PATH`, download a verifier at
update time, trust a moving tag, accept a verification boolean from the
renderer, or treat a GitHub attestation badge as local verification. The
verifier binary and complete trust material must themselves be immutable and
bootstrap-verifiable.

## Remaining cryptographic gates

The existing contracts deliberately stop short of these gates:

- exact trusted signer identity and OIDC issuer registry;
- exact offline bundle schema, size limits, certificate chain, signed-time,
  transparency inclusion and checkpoint requirements;
- pinned trust-root material, expiry, revocation, compromise response and
  threshold rotation authorization;
- deterministic valid, corrupted-signature, corrupted-payload, wrong-identity,
  wrong-issuer, expired, future, revoked, unknown-root, threshold and root-
  transition vectors produced by the selected verifier implementation;
- Windows signed-PE and macOS signed/universal-bundle fixtures;
- exact native verifier binary dependency, license, SBOM, provenance,
  source-versus-package parity and lifecycle evidence.

Until those exist, `core-update-trust-handoff` remains structural only. Its
claims are non-authoritative and cannot promote evidence, stage a package, or
activate an update.
