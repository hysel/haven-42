# Local Model Reliability

## Purpose

This guide explains how to use the pack safely with local models such as Ollama-backed coding models.

Local-first operation is useful for private repositories, but smaller local models can be less consistent than hosted frontier models. Treat model output as a draft that must be checked against the pack's prompts, rules, fixtures, and templates.

## Expected Behavior

Local models should be able to:

- Summarize repository structure from supplied context.
- Produce implementation plans when the prompt asks for planning only.
- Review code or documentation against explicit criteria.
- Follow fixed templates for common workflows.
- Call out missing evidence instead of inventing details.

Local models may still:

- Ignore "do not write code" instructions.
- Invent file paths, package versions, tools, or configuration details.
- Overfit to examples from the prompt.
- Produce shallow summaries instead of risk-based reviews.
- Treat local smoke testing as enough evidence for release.
- Recommend unsafe migrations for legacy project systems.

## Reliability Tiers

Use these tiers when deciding how much trust to place in a local-model response.

### Low Risk

Examples:

- Repository discovery summaries.
- Documentation gap brainstorming.
- Drafting checklists.
- Explaining existing prompt or rule intent.

Expected review:

- Human review for accuracy.
- No direct implementation without normal engineering review.

### Medium Risk

Examples:

- Implementation planning.
- Code review.
- Architecture review.
- Security or performance triage based on limited context.

Expected review:

- Verify evidence and assumptions.
- Compare the response to relevant fixtures or examples.
- Require validation, rollback, and affected-file reasoning before acting.

### High Risk

Examples:

- Legacy dependency migration.
- Release-readiness decisions.
- Security-sensitive recommendations.
- Customer-data or authorization-related changes.
- Production deployment guidance.

Expected review:

- Require human approval before implementation.
- Prefer fixed templates where available.
- Treat missing evidence as a blocker.
- Do not accept broad rewrites, package changes, or release go decisions without independent validation.

## Validation Workflow

When testing a prompt with a local model:

1. Generate repository context with `scripts/generate-runtime-context.ps1` when tool execution is unreliable.
2. Run the prompt against the target repository or a sanitized fixture.
3. Compare the response to `docs/prompt-quality.md`.
4. Check whether the response violates any forbidden output pattern in the fixture.
5. Rerun with more explicit context if the response is shallow or generic.
6. Prefer the human-reviewed template when a high-risk prompt keeps failing.
7. Record only sanitized validation notes in committed docs.

## Using Local Ollama Endpoints

Keep committed configuration portable:

- Use the default local Ollama endpoint in committed config.
- Put private hostnames, private IP addresses, and local ports only in ignored local override files.
- Do not commit `apiBase` values that point to a private network.
- Do not commit raw runtime output that contains local paths, endpoint values, repository names, or secrets.

For machine-specific setup, copy the committed config to an ignored local file such as `.continue/config.local.yaml`, then add the local endpoint there.

## When To Retry

Retry the prompt when:

- The response asks for context that was already provided.
- The output is mostly a generic summary.
- Required sections are missing.
- The model ignored a clear "plan only" or "do not modify files" instruction.
- The response mixes confirmed facts with assumptions.

Before retrying:

- Add concise repository context.
- Include exact constraints.
- Reference the relevant fixture or template.
- Ask the model to state unknowns explicitly.

## When To Stop And Escalate

Stop relying on the local-model answer when:

- It repeatedly recommends unsafe edits after being corrected.
- It invents exact file paths, package versions, endpoints, or test results.
- It recommends production release without required evidence.
- It provides code when the workflow explicitly requires a plan only.
- It omits rollback, validation, or security risk for a high-risk workflow.

Escalation options:

- Use the fixed template output for the workflow.
- Have a human reviewer write the plan.
- Run the workflow with a stronger model if policy allows.
- Add or improve a fixture that captures the failure.

## Committable Evidence

Safe committed validation notes should include:

- Prompt name.
- Model family or size, without private endpoint details.
- Sanitized target repository type.
- Whether the response passed or failed.
- Specific failure modes.
- Prompt, fixture, or template changes made in response.

Do not commit:

- Private IP addresses.
- Personal filesystem paths.
- Raw proprietary code.
- Secrets or tokens.
- Unsanitized model transcripts from private repositories.
