# Validation Checklists

## Purpose

Use these checklists before merging changes to this pack. They keep prompts, rules, agents, templates, configuration, and examples consistent as the repository grows.

## Prompt Changes

- [ ] Frontmatter starts on the first line.
- [ ] `name` is lower-case kebab-case.
- [ ] `description` explains the workflow in one sentence.
- [ ] `invokable: true` is present when the prompt should be user-invokable.
- [ ] Purpose, required context, process, output format, and quality checks are clear.
- [ ] The prompt does not duplicate full rule content.
- [ ] The prompt tells the assistant when not to modify files.
- [ ] Output sections match the intended workflow.
- [ ] The prompt can be run with the configured Continue model.
- [ ] README, examples, TODO, and ROADMAP are updated if the workflow surface changes.

## Rule Changes

- [ ] Frontmatter starts on the first line.
- [ ] `name` is human-readable and stable.
- [ ] Scope is clear.
- [ ] Required practices are reusable across workflows.
- [ ] Avoid section identifies common failure modes.
- [ ] Review checklist is actionable.
- [ ] The rule does not depend on a prompt or agent.
- [ ] The rule does not encode one-off task instructions.
- [ ] Related prompts reference the rule conceptually instead of copying it.

## Agent Changes

- [ ] Frontmatter starts on the first line.
- [ ] Role is durable and not tied to one task.
- [ ] Responsibilities describe behavior, not a full workflow.
- [ ] Boundaries are explicit.
- [ ] Expected outputs are concise and role-appropriate.
- [ ] Agent behavior does not duplicate detailed prompt steps.
- [ ] README and architecture docs are updated if the role model changes.

## Template Changes

- [ ] Template has a clear artifact purpose.
- [ ] Sections are easy to scan.
- [ ] Findings, recommendations, risks, and next steps are separated when relevant.
- [ ] Template can be pasted into issues, pull requests, or review records.
- [ ] Template does not require repository-specific private context.
- [ ] Related examples are updated if output shape changes.

## Config Changes

- [ ] `name`, `version`, and `schema` remain present.
- [ ] Model entries have provider, model, and intended roles.
- [ ] Remote endpoints are documented when committed.
- [ ] Local `file://` references resolve from `.continue/config.yaml`.
- [ ] New prompts or rules are included only when ready for users.
- [ ] MCP servers remain empty unless setup and security guidance exist.
- [ ] Continue CLI can load the config.
- [ ] Model-backed execution works, or the reason it cannot be validated is documented.

## Example Changes

- [ ] Examples reflect current repository state.
- [ ] Examples are labeled as representative, not exhaustive.
- [ ] Examples do not include secrets, real customer data, or private URLs.
- [ ] Examples match current prompt output expectations.
- [ ] README links to new examples.
- [ ] TODO and ROADMAP are updated when examples complete a milestone item.

## Documentation Changes

- [ ] README remains user-facing.
- [ ] ROADMAP describes staged delivery, not tactical details.
- [ ] TODO tracks concrete implementation work.
- [ ] DECISIONS records meaningful architecture, compatibility, or governance choices.
- [ ] CHANGELOG records user-visible changes.
- [ ] STYLEGUIDE remains the source for writing and formatting conventions.
- [ ] Claims match implemented behavior.

## Release Validation

- [ ] `git status --short --branch` is reviewed before commit.
- [ ] `git diff --check` passes.
- [ ] Windows validation scripts pass.
- [ ] Linux and macOS Bash wrapper scripts pass when those environments are available.
- [ ] Config local references are checked.
- [ ] Version is updated in `.continue/config.yaml`.
- [ ] CHANGELOG has an entry for the release.
- [ ] README reflects the current runtime status.
- [ ] Tags use the `vMAJOR.MINOR.PATCH` format.
- [ ] Branch and tag are pushed.
