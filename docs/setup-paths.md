# Setup Paths

The same pack supports a quick individual setup and a reviewable team setup.

## Beginner Path

Choose this path to get a local coding assistant working on one computer or project.

Start here:

- `docs/haven-42-menu.md`
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

Choose this path when setup must be reviewable, repeatable, or auditable across
multiple projects.

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

Beginner-friendly does not mean weaker safety. Enterprise-safe does not need to
make first-run setup harder. The difference is how much evidence, review, and
repeatability you need before applying changes.
