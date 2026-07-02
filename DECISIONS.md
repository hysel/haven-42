# Decisions

This file records important project decisions. Use it for choices that affect architecture, compatibility, governance, or long-term maintenance.

## Format

Each decision should use this structure:

```text
## YYYY-MM-DD: Decision Title

Status: Proposed | Accepted | Superseded

Context:
Why the decision is needed.

Decision:
What was chosen.

Consequences:
Expected benefits, tradeoffs, and follow-up work.
```

## 2026-07-01: Use Continue YAML Configuration

Status: Accepted

Context:
Continue supports YAML configuration for agents, models, rules, prompts, context providers, documentation, and MCP servers. The deprecated JSON configuration format should not be the primary target for this pack.

Decision:
Use `.continue/config.yaml` with `schema: v1` as the composition root for the pack.

Consequences:
The pack should be validated against the Continue YAML schema. Documentation and examples should prefer YAML configuration.

## 2026-07-01: Local-First Model Posture

Status: Accepted

Context:
The project targets enterprise teams that may work with private repositories and regulated codebases.

Decision:
Use Ollama and local models as the default documented path.

Consequences:
Cloud-hosted model configuration may be documented later, but must not become the default assumption.

## 2026-07-01: Separate Agents, Prompts, Rules, And Templates

Status: Accepted

Context:
The repository needs to scale across many workflows without duplicating instructions or creating unclear ownership.

Decision:
Agents define role behavior, prompts define workflow steps, rules define reusable standards, and templates define output shape.

Consequences:
Contributors should move duplicated guidance to the lowest appropriate reusable layer, usually rules or templates.

## 2026-07-01: Keep Rule Dependencies Acyclic

Status: Accepted

Context:
Rules, prompts, agents, and templates can easily become coupled if each layer copies or depends on the others.

Decision:
Rules and templates are lower-level reusable assets. Prompts may reference rules and templates conceptually. Agents may reference prompts and rules conceptually. Rules should not depend on prompts or agents.

Consequences:
The pack should remain easier to extend because policy, workflow, role behavior, and output shape can evolve independently.

## 2026-07-01: Include Supplemental Review Prompts

Status: Accepted

Context:
Additional prompt files existed for AI framework self-review, refactoring planning, product-management review, and release-readiness review. They were useful enterprise workflows but were not wired into the pack configuration.

Decision:
Normalize those prompt files with standard frontmatter, use lower-case kebab-case filenames, and include them in `.continue/config.yaml`.

Consequences:
The pack now exposes broader review and planning workflows. Runtime validation must confirm each prompt is invokable in Continue.

## 2026-07-01: Use MIT License

Status: Accepted

Context:
The repository is a reusable Continue engineering pack made of configuration, prompts, rules, agents, templates, and documentation. Adoption should be simple for teams that want to copy, adapt, or redistribute the pack.

Decision:
Use the MIT License.

Consequences:
The pack is permissively licensed with low adoption friction. The license does not include the explicit patent grant provided by Apache-2.0.

## 2026-07-01: Keep Ollama Endpoint Portable

Status: Accepted

Context:
The pack should be reusable across machines and networks. A local-network Ollama server was used for validation, but committing a concrete private IP address would make the default configuration environment-specific.

Decision:
Do not commit a concrete `apiBase` value for Ollama. Use remote Ollama endpoints only as local test-time overrides.

Consequences:
The committed config remains portable and defaults to Continue's standard Ollama behavior. Users who run Ollama on another host must add their own local `apiBase` override.

## 2026-07-01: Start SonarQube Support With Manual Triage

Status: Accepted

Context:
SonarQube support is part of the enterprise review scope, but direct API, CLI, or MCP integration requires additional design and environment assumptions.

Decision:
Provide a manual workflow first. Users paste relevant SonarQube findings into Continue, and the pack guides classification, prioritization, remediation, and validation.

Consequences:
Teams can use SonarQube findings immediately without integration setup. Automated SonarQube ingestion requires separate integration guidance before it should become a default workflow.

## 2026-07-01: Use Documentation Checklists For Pack Validation

Status: Accepted

Context:
The pack is primarily composed of markdown and YAML assets. Traditional unit tests do not cover most quality risks in prompts, rules, agents, templates, and examples.

Decision:
Maintain validation checklists in `docs/validation-checklists.md` for prompt, rule, agent, template, config, example, documentation, and release changes.

Consequences:
Contributors have a repeatable review path before automated validation exists. Future scripts can be added later for checks that are easy to automate.

## 2026-07-02: Keep MCP Optional And Local-First

Status: Accepted

Context:
MCP can connect Continue to external tools such as GitHub, filesystems, databases, and quality systems. These integrations are useful, but they expand trust boundaries, may require secrets, and can create network dependencies. The pack must continue to work with local Ollama systems and without cloud services.

Decision:
Keep `mcpServers: []` in the default config. Document MCP as optional. Prefer read-only, local-first MCP integrations first, with GitHub MCP as the first candidate for repository, issue, and pull request context.

Consequences:
The default pack remains portable and local-model compatible. Users can adopt MCP intentionally through documented setup. SonarQube and other external integrations require separate security and setup guidance before they are recommended.

## 2026-07-02: Use SonarQube Web API As First Automation Path

Status: Accepted

Context:
SonarQube findings are valuable review inputs, but direct integration can require tokens, internal endpoints, project identifiers, organization keys, and network access. The pack must remain usable with local Ollama and without granting agent tools live access to quality systems.

Decision:
Keep manual SonarQube triage as the default workflow. Use the SonarQube Web API as the first documented automation path for sanitized, read-only review input. Treat the SonarQube MCP server as optional until it is validated with Continue, local Ollama, and enterprise credential-handling expectations.

Consequences:
Teams can automate retrieval of quality gate status, measures, and findings without changing the default Continue config. MCP remains a future opt-in setup rather than a default dependency.

## 2026-07-02: Document GitHub MCP As Optional First MCP Setup

Status: Accepted

Context:
MCP can provide useful external context, but enabling MCP by default would add credentials, network dependencies, tool execution, and possible data exposure. The pack needs a concrete setup path while keeping local Ollama workflows unaffected.

Decision:
Document GitHub MCP as the first optional MCP setup path. Keep the default config unchanged with `mcpServers: []`. Prefer a separate local `.continue/mcpServers/` file for users who opt in.

Consequences:
Teams have a reproducible MCP starting point without changing the portable default configuration. GitHub MCP can be validated independently from local model behavior, and SonarQube MCP can remain separate until API-based workflows are proven.

## 2026-07-02: Add Scripted Release Validation

Status: Accepted

Context:
The pack is mostly markdown and YAML, so traditional unit tests do not cover the main failure modes. Release risk is concentrated around broken local file references, accidental endpoint or secret commits, stale version values, and accidental changes to the local-first default posture.

Decision:
Add a PowerShell validation script that checks the pack version, required files, local `.continue` references, default MCP posture, and obvious private endpoints or secrets.

Consequences:
Release checks are repeatable on the current Windows-first maintenance environment. Future CI can run the same script or add cross-platform equivalents.
