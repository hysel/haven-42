# Contributing

Thank you for improving Haven 42.

This repository is primarily documentation, Continue configuration, rules, prompts, agents, templates, examples, and validation guidance. Changes should make the pack more reusable, safer for enterprise repositories, and easier to validate.

## Contribution Principles

- Keep the default pack local-first.
- Do not commit private endpoints, tokens, organization names, project keys, or machine-specific paths.
- Prefer reusable rules and templates over duplicated prompt text.
- Keep examples realistic but sanitized.
- Update documentation when behavior, setup, or workflow expectations change.
- Treat AI output as review assistance, not as an authority.
- Evaluate new agent software outside the tracked repository and admit agent-specific assets only after every promotion gate passes.

## Before Changing Files

Read the relevant project documents:

- `PROJECT.md`
- `ARCHITECTURE.md`
- `STYLEGUIDE.md`
- `ROADMAP.md`
- `TODO.md`
- `AI.md`
- `DECISIONS.md`

For Continue-specific changes, also inspect:

- `.continue/config.yaml`
- `.continue/rules/`
- `.continue/prompts/`
- `.continue/agents/`
- `.continue/templates/`

## Change Guidelines

### Configuration

- Keep `.continue/config.yaml` portable.
- Keep `mcpServers: []` unless the project intentionally changes the default integration posture.
- Use local Ollama defaults unless a future decision record changes the model strategy.
- Do not commit `apiBase` values for private or local-network model endpoints.

### Prompts

- Prompts should define workflow steps and expected output.
- Prompts should reference rules conceptually instead of duplicating long standards.
- Prompts should tell the assistant to call out missing information instead of guessing.

### Rules

- Rules should capture reusable engineering standards.
- Rules should be specific enough to guide output but should not remove engineering judgment.
- Avoid circular dependencies between rules, prompts, and agents.

### Examples

- Examples should demonstrate expected structure and depth.
- Use sanitized file paths, service names, project keys, and findings.
- Do not include real customer data, credentials, hostnames, or internal URLs.

### Documentation

- Keep README focused on setup, usage, and repository orientation.
- Keep ROADMAP focused on staged delivery.
- Keep TODO focused on trackable work.
- Keep DECISIONS focused on durable decisions and tradeoffs.
- Keep CHANGELOG updated for user-visible changes.

### Agent Integrations

- Follow `docs/agent-integration-admission-policy.md` before testing or proposing another agent surface.
- Keep candidate harnesses, wrappers, configuration, logs, fixtures, and transcripts untracked and disposable.
- If any required gate fails, commit only a concise sanitized decision record; do not commit or retain partial integration artifacts.
- Add scripts, workflows, active catalog entries, examples, or package assets only after the exact agent version passes the full pass-to-ship gate.

## Validation

Run the Fast tier while editing and Full before pushing:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
.\scripts\test-pack.ps1 -Tier Full
```

Use `docs/test-tiers.md` for Integration-only runs, timing output, and the
exact-tree receipt used to avoid duplicate pre-push work. GitHub Actions always
runs Full independently.

When mapped documentation changes, synchronize and commit the separate GitHub wiki before pushing the main repository. Follow `docs/wiki-maintenance.md`; hosted CI rejects stale mapped wiki pages.

Also review:

- `docs/validation-checklists.md`
- `docs/compatibility.md`
- `docs/release.md`

## Release Process

Follow `docs/release.md` for version updates, validation, commit, tag, and push guidance.

After every push, use the platform-specific `verify-hosted-ci` script with the
full commit SHA. A push is not verified until the exact-SHA workflow and all
required hosted jobs report success. See `docs/hosted-ci-verification.md`.

## Pull Request Checklist

- [ ] The change follows `STYLEGUIDE.md`.
- [ ] The relevant docs are updated.
- [ ] New examples are sanitized.
- [ ] No secrets, private endpoints, or machine-specific paths are committed.
- [ ] `.continue/config.yaml` remains portable.
- [ ] New agent-specific assets have complete pass-to-ship evidence, or the change contains documentation only for a failed evaluation.
- [ ] `CHANGELOG.md` records user-visible changes.
- [ ] Validation has been run or skipped with a clear reason.
