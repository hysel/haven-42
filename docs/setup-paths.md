# Setup Paths

This pack supports two setup styles without splitting the project into separate beginner and enterprise editions.

## Beginner Path

Use this path when you want a local coding assistant working quickly on one machine or one project.

Start here:

- `docs/agent-pack-menu.md`
- `docs/beginner-setup-mode.md`
- `docs/workflow-chooser.md`

Default posture:

- Prefer local Ollama.
- Use conservative model defaults.
- Generate recommendations before writing config.
- Use dry-run install and config preview first.
- Keep private endpoints and machine-specific settings in local-only files.
- Validate model/tool behavior before trusting approved writes.

## Team Or Enterprise Path

Use this path when setup needs reviewability, repeatability, or audit evidence across more than one project.

Start here:

- `docs/shared-asset-installation.md`
- `docs/workflow-registry.md`
- `docs/evidence-dashboard.md`
- `docs/release.md`

Default posture:

- Keep shared assets centralized and versioned.
- Keep generated local config out of commits.
- Run validation and release readiness gates before publishing changes.
- Record sanitized evidence for model, surface, OS, and write-readiness claims.
- Require explicit approval before approved-write mode.
- Use external Git or shell verification after any write validation.

## Same Safety Boundary

Both paths use the same safety model:

| Need | Beginner path | Team or enterprise path |
| --- | --- | --- |
| Choose a workflow | Guided menu or beginner setup plan. | Workflow registry, chooser, and release gate. |
| Pick a model | Hardware-aware recommendation and local model docs. | Recommendation plus evidence dashboard and scorecard. |
| Install assets | Dry-run project-local install first. | Shared-assets mode plus backup and validation. |
| Trust writes | Tool-use validation before approved writes. | Tool-use validation plus audit evidence and external verification. |
| Troubleshoot | Troubleshooting docs and local health check. | Health check, runtime validation, evidence dashboard, release readiness. |

Beginner-friendly does not mean weaker safety. Enterprise-safe does not mean harder first-run setup. The difference is how much evidence, review, and repeatability the user needs before applying changes.
