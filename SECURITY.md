# Security Policy

## Supported Versions

Haven 42 is pre-1.0. Only the latest tagged release and the current `main` branch receive security fixes. Contracts marked `runtimeAdmitted: false`, documentation-only candidates, and failed or partial provider profiles are not supported runtime surfaces.

The local-web readiness scan is explicit, loopback-only, CSRF-protected, bounded, shell-free, network-free, and read-only. It returns sanitized capability facts rather than identity or raw command output, stores its snapshot only in memory, and builds setup plans only from the exact current server-owned snapshot. The installation broker is simulation-only and not runtime-admitted; no browser request can authorize a download, command, write, elevation, service change, driver change, or installation.

Unsigned portable development builds preserve this boundary. They verify their allowlisted browser/data resources at startup, bind only to IPv4 loopback, construct only a loopback browser URL, expose no arbitrary process control, and require same-origin session authority plus verified model cleanup for HTTP shutdown. Package archives include SHA-256 checksums, dependency inventory, third-party notices, and CycloneDX SBOM evidence. They are not signed, notarized, installer-backed, published releases, or production-ready. The offline installer and updater policy foundations cannot modify a machine or activate an update.

Portable build dependencies are exact-version and SHA-256 locked for the admitted hosted runner platforms. Evidence generation uses a reviewed platform allowlist rather than enumerating the caller environment. Native hostile tests reject altered, missing, unexpected, and traversal-manifest resources; shutdown authority failures; unsafe archive members; incomplete checksums/notices; malformed SBOM/provenance; and archive/file-inventory divergence. Provenance is informational and explicitly unsigned/unattested.

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
