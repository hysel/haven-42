# Project Information

_For users, evaluators, and contributors. Haven 42 remains active development
software and makes no production-readiness claim._

## Current position

Haven 42 has a local browser application, unsigned one-folder development
packages for Windows, Linux, and macOS, and local AI features that are enabled
only after their tests pass. The latest public test build is the unsigned Windows
`0.4.0-alpha.1` prerelease; the latest stable release line is `0.3.0`. Work
newer than those exact published versions remains unreleased.

See [[Windows Alpha Release|Eng-Windows-Alpha-Release]] for the exact Alpha files,
checksums, publication record, and boundaries.

The project separates three states:

- **Available:** present in the current app.
- **Tested only:** demonstrated on a specific recorded setup, but not available
  to every user.
- **Planned:** designed or under test, but not enabled in the app.

## Major active areas

- Unified local conversation and bounded attachment context.
- Portable development packaging and cross-platform native smoke testing.
- Hardware-aware model and inference-engine evidence.
- Local image generation and future media-provider evaluation.
- Restricted document-parser research without runtime admission.
- Optional encrypted conversation-history architecture without persistence.
- Controlled web-research transport/approval guards without an active network adapter.

For milestone detail, open the [[Roadmap]]. For exact committed outcomes and
limits, use the [[Evidence Summary|Eng-Evidence-Summary]].

## Important limitations

- Development packages are unsigned.
- No installer, system service, driver, firewall rule, or administrator access
  is required or enabled by Haven 42.
- Online updates and real machine-modifying installation remain disabled.
- Conversation history is not persisted.
- PDF, Office, and OpenDocument upload parsing is not admitted to the product.
- macOS hardware-specific evidence remains incomplete in several areas.
- A validation result applies only to its exact recorded artifact, platform,
  runtime, model, and operation.

## Governance and safety

- [[Privacy|Privacy-Policy]]
- [[Connection Security|Provider-Endpoint-Security]]
- [[Security Threat Model|Eng-Security-Threat-Model]]
- [[Code Signing Policy|Eng-Code-Signing-Policy]]
- [[GitHub Repository Policy|Eng-GitHub-Repository-Policy]]

Security issues should be reported privately using the process in the source
repository's `SECURITY.md`, without posting credentials, private prompts, or
personal files in a public issue.

## Contributing and deeper documentation

The [[Engineering and Validation Index|Engineering-Index]] organizes
contributor, architecture, validation, evidence, and research records.
Maintainers should also read [[Wiki Maintenance|Eng-Wiki-Maintenance]] before
editing synchronized pages.
