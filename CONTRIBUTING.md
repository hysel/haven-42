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

Run the Fast tier while editing. For the final local gate, stage the complete
change first and ensure there are no unstaged or untracked files. Review the
entire staged diff for security. If any finding of any severity exists, stop,
notify the repository owner, fix every finding, and repeat the review. When the
review has zero findings, record its exact-tree receipt, then run Full without
`-NoReceipt`:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
python scripts/security-review-gate.py --record-clean
.\scripts\test-pack.ps1 -Tier Full
```

Use `docs/test-tiers.md` for Integration-only runs, timing output, and the
schema-v3 staged-tree receipt used to avoid duplicate pre-push work. Before the
final stage, review every roadmap milestone for status, evidence, and boundary
drift rather than checking only the milestone being changed. Commit without
editing after Full; the pre-commit hook rejects an untested staged tree and the
pre-commit hook also rejects a qualifying staged tree without its clean
security-review receipt. The pre-push hook then reuses the exact tested tree.
GitHub Actions always runs Full independently.

When mapped documentation changes, synchronize and push the separate GitHub
wiki before opening or pushing the main-repository PR. Follow
`docs/wiki-maintenance.md`; hosted CI performs bounded retry for propagation
delay but rejects persistent drift.

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
- [ ] The complete staged diff has a zero-finding security review when required.
- [ ] All roadmap milestones were reviewed for status, evidence, and boundary drift.

## Security changes

Report vulnerabilities privately as described in `SECURITY.md`. Changes to
provider boundaries, workflow dispatch, installers, updates, releases,
permissions, or CI must complete the pull-request security checklist. Obtain
CODEOWNERS review when another eligible maintainer is available. Solo-maintainer
changes rely on the enforced eight-check branch gate because GitHub does not
count self-approval. Do not weaken a fail-closed gate to make a test pass.
