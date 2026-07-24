# Security Policy

## Supported Versions

Haven 42 is pre-1.0. Only the latest tagged release and the current `main` branch receive security fixes. Contracts marked `runtimeAdmitted: false`, documentation-only candidates, and failed or partial provider profiles are not supported runtime surfaces.

The local-web readiness scan is explicit, loopback-only, CSRF-protected, bounded, shell-free, network-free, and read-only. It returns sanitized capability facts rather than identity or raw command output, stores its snapshot only in memory, and builds setup plans only from the exact current server-owned snapshot. Automatic text recommendations require an exact provider digest and capability evidence; name-only matches remain unverified. Provider token and timing values are diagnostic, memory-only, and never represented as billing or remaining context. Event envelopes are fail-closed: sequences must be contiguous and monotonic, contain exactly one result or error terminal, and stop at that terminal. An unverified manual model is visibly warned, failures do not retry automatically, and restored input remains browser-memory-only for a new request.

The Software view admits only registry-backed `uiReady`, `read-only` plans and
cannot pass arguments or start a process. The Images view is separately limited
to the promoted Linux ComfyUI/SDXL profile through an IP-literal loopback
endpoint. The model and node graph are engine-owned, response size and PNG shape
are bounded, API history is cleared, client delivery stays in browser memory,
and provider-side retention is disclosed before execution. No browser request
can authorize arbitrary download, command, client file write, repository read,
elevation, service change, driver change, or installation. The installation
broker remains simulation-only and not runtime-admitted.

Unsigned portable development builds preserve this boundary. They verify their allowlisted browser/data resources at startup, bind only to IPv4 loopback, construct only a loopback browser URL, expose no arbitrary process control, and require same-origin session authority plus verified model cleanup for HTTP shutdown. Package archives include SHA-256 checksums, dependency inventory, third-party notices, and CycloneDX SBOM evidence. They are not signed, notarized, installer-backed, published releases, or production-ready. The offline installer and updater policy foundations cannot modify a machine or activate an update. The lifecycle simulator rejects raw paths, URLs, commands, arguments, and environment input; models healthy, failed-health, interrupted, rollback, retention, and disabled paths; and always reports network, writes, download, staging, activation, rollback, cleanup, installation, elevation, service, driver, firewall, process, and user-data effects as false.

Portable build dependencies are exact-version and SHA-256 locked for the admitted hosted runner platforms. Evidence generation uses a reviewed platform allowlist rather than enumerating the caller environment. Native hostile tests reject altered, missing, unexpected, and traversal-manifest resources; shutdown authority failures; unsafe archive members; incomplete checksums/notices; malformed SBOM/provenance; and archive/file-inventory divergence. Provenance is informational and explicitly unsigned/unattested.

Public-history privacy is enforced before push and in a least-privilege GitHub Actions job. The versioned policy scans reachable commits, commit messages, author and committer identities, and unique historical blobs for private-network endpoints, machine-specific user paths and SSH command targets, key material, fingerprints, credential-bearing URLs, and likely secrets. GitHub noreply identities and narrowly enumerated hostile-test pattern sources are admitted; ignored recovery evidence and unreachable Git objects remain local and must never be tracked.

Task composition is simulation-only. It accepts only registered UI-ready read-only workflows, bounded acyclic dependencies, and exact fields. It accepts no renderer arguments or approval grants and cannot create a process, access a filesystem or network, execute a workflow, or modify a machine.

## Reporting A Vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private vulnerability reporting for `hysel/haven-42` so reports, proof-of-concept details, credentials, private endpoints, and affected artifacts remain private.

Include the affected commit or release, operating system, entry point, required privileges, impact, reproduction steps, and whether secrets or user data may have been exposed. Remove real credentials, private prompts, repository content, and machine identity from attachments.

## Response Targets

- Acknowledge a credible report within 3 business days.
- Triage severity and affected supported surfaces within 7 business days.
- Immediately block release or runtime promotion when exploitation may affect credentials, arbitrary code execution, update integrity, path-grant escape, or user-data deletion.
- Coordinate a patch and advisory before public disclosure. Timing depends on severity and the safety of available mitigations.

No bounty is currently offered. Good-faith research that avoids privacy violations, persistence, service disruption, social engineering, and access beyond the reporter's own systems is welcome.

## Release And Incident Handling

Security fixes use a new commit and release tag; published tags are not rewritten. A compromised release, signing identity, dependency, model artifact, or provider profile is blocked, documented, and superseded. Required response actions include revoking affected credentials or signing material, disabling automatic acquisition, preserving sanitized evidence, publishing an advisory, and validating a new immutable artifact through the normal promotion gates.

Never send secrets through issue comments, logs, test fixtures, or committed evidence.

Repository governance is fail-closed and recorded in
`config/github-repository-policy.json`. `main` requires the complete
cross-platform validation/package gate plus CodeQL, full-SHA GitHub-owned
Actions, read-only default workflow permissions, linear history, conversation
resolution, and administrator enforcement. See
`docs/github-repository-policy.md`.
