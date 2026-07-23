# Security Policy

## Supported Versions

Haven 42 is pre-1.0. Only the latest tagged release and the current `main` branch receive security fixes. Contracts marked `runtimeAdmitted: false`, documentation-only candidates, and failed or partial provider profiles are not supported runtime surfaces.

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
