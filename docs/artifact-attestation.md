# Unsigned Development Artifact Attestation

Haven 42 prepares GitHub build-provenance attestations for the native unsigned
development archives produced by the existing Windows, Linux, and macOS
package matrix. This is supply-chain provenance, not Windows code signing,
Apple Developer ID signing, notarization, an installer, a GitHub Release, or a
production-readiness claim.

## Trigger And Authority

The attestation job runs only for a push to `main` and only after all three
native package jobs succeed. Pull-request jobs retain the workflow's read-only
permission and cannot mint or publish an attestation.

The isolated job receives only:

- `actions: read` to download artifacts from the same workflow run;
- `contents: read` to check out the exact source without persisted credentials;
- `id-token: write` for a short-lived OIDC identity;
- `attestations: write` to store the attestation; and
- `artifact-metadata: write` for GitHub's attestation metadata.

It receives no contents, packages, releases, security-events, pull-request,
deployment, or repository-administration write permission.

## Subject Boundary

The job downloads only artifact names matching
`haven42-*-unsigned-development`. It requires exactly three native artifact
sets and re-runs the existing archive, checksums, inventory, notices, SBOM, and
provenance verifier against each set before attestation.

Only archive files matching these patterns become attestation subjects:

```text
haven42-*-unsigned-development.zip
haven42-*-unsigned-development.tar.gz
```

The action does not attest arbitrary workspace files, upload a Release, push a
container, or change artifact contents. The archives remain visibly unsigned
development packages. The included CycloneDX document remains checksum-bound
evidence; this first slice does not claim a separate SBOM predicate
attestation.

## Immutable Actions

Every external action remains GitHub-owned and pinned to a reviewed full commit
SHA:

- `actions/checkout` v7.0.1;
- `actions/upload-artifact` v7.0.1;
- `actions/download-artifact` v8.0.1; and
- `actions/attest` v4.2.1.

The repository policy verifier rejects moving tags, missing pins,
pull-request-target execution, overprivileged write permissions, release or
registry publication, incomplete subject patterns, and drift from the
machine-readable policy.

## Verification

After a future approved push creates an attestation, a downloaded archive can
be checked against the authoritative public repository with:

```text
gh attestation verify PATH-TO-ARCHIVE -R hysel/haven-42
```

This verifies the GitHub/Sigstore build-provenance statement for the exact
archive digest. Users must still verify Haven 42's `SHA256SUMS` and review the
unsigned-development warning. A successful attestation does not make an
artifact production-ready and is not sufficient to activate the updater.

## Remaining Promotion Gates

Production distribution still requires:

1. Windows platform signing and publisher governance;
2. Apple Developer ID signing, hardened runtime, notarization, and physical-Mac
   validation;
3. a trusted updater verifier and root-rotation policy;
4. clean install, upgrade, rollback, retention, and uninstall evidence; and
5. explicit approval before any Release publication.
