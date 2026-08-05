# Private alpha feedback template

Use this sanitized structure for a future invited-alpha report. Do not include
provider addresses, API keys, prompts, attachments, model responses, local
paths, usernames, machine identifiers, SSH details, or private repository data.

```text
Alpha version:
Artifact SHA-256:
Operating system and architecture:
Haven launch mode: source or packaged
Provider kind: same-device or private-network
Authentication mode: none, Bearer, or X-API-Key (never include the key)
Model name and immutable digest, if relevant:

Area: setup, chat, writing, summarization, models, attachments, system, evidence, or shutdown
Expected behavior:
Observed behavior:
Minimal synthetic reproduction steps:
Frequency: once, intermittent, or every time
Impact: blocked, degraded, cosmetic, or suggestion
Workaround, if any:

Confirmation:
- No secrets or private content included
- No local address or machine-specific path included
- Candidate archive and application were not modified
```

Suspected vulnerabilities, credential exposure, arbitrary execution, listener
scope errors, update/install effects, or data loss must be reported privately
and treated as release-blocking until reviewed.

For an ordinary Alpha problem or experience suggestion, use the structured
[Alpha report chooser](https://github.com/hysel/haven-42/issues/new/choose).
The forms repeat these privacy limits and disable blank public issues. Review a
saved sanitized support report before sharing any part of it. Security concerns
must use
[private vulnerability reporting](https://github.com/hysel/haven-42/security/advisories/new).
