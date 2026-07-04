# Local Model Reliability

## Purpose

This guide explains how to use the pack safely with local models such as Ollama-backed coding models.

Local-first operation is useful for private repositories, but smaller local models can be less consistent than hosted frontier models. Treat model output as a draft that must be checked against the pack's prompts, rules, fixtures, and templates.

Use `docs/local-model-selection.md` to choose a model based on hardware capacity, context needs, workflow risk, and tool-use requirements.

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

## Tool-Capable Model Guidance

Agent mode tool execution needs a model that produces tool calls in the format Continue can execute.

Validated behavior:

- `qwen3-coder:30b` successfully enabled tool execution in the tested VSCodium, Continue, and Ollama setup.
- `qwen2.5-coder:7b` produced raw JSON tool-call text instead of executable tool calls in the same setup.

Recommended use:

- Use `qwen3-coder:30b` or another validated tool-capable model for Agent mode and approved tool-backed changes.
- Use smaller models only for review, planning, summarization, or context-file workflows unless tool execution is proven.
- Keep model experiments in local config until they are validated.
- Keep local defaults responsive first. The committed starter config uses `contextLength: 16384` and `maxTokens: 2048`; raise those values only when the workflow needs deeper context and latency remains acceptable.

## Tool-Use Validation Checklist

Treat a model as tool-validated only after it passes a read-only tool test in the intended editor, provider, and operating system.

Record:

- Model name and tag.
- Provider or server, such as Ollama or an OpenAI-compatible local endpoint.
- Editor surface, such as VS Code, VSCodium, or Continue CLI.
- Continue extension or CLI version when available.
- Operating system.
- Whether MCP was enabled.

A model passes the basic read-only tool check when:

- It executes a read-only file or repository inspection tool instead of printing JSON.
- It produces a normal final answer after tool execution.
- It separates observed evidence from assumptions.
- It does not ask to modify files during a read-only prompt.
- It does not suggest clicking Apply on raw JSON.

Before approved write mode, also confirm:

- The model asks before write actions.
- The requested edit scope is narrow and names affected files.
- The model can explain the planned change before editing.
- The model can summarize the diff after editing.
- The model can name validation and rollback steps.

Do not treat hardware-tier recommendations or installed-model detection as tool validation. The recommendation catalog helps choose a candidate model; it does not prove tool behavior.

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

1. Generate repository context when tool execution is unreliable. Use `scripts/generate-runtime-context.ps1` on Windows, `scripts/generate-runtime-context.linux.sh` on Linux, or `scripts/generate-runtime-context.macos.sh` on macOS.
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
