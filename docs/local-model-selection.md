# Local Model Selection

## Purpose

This guide helps users choose a local Ollama model for Continue based on machine capacity and workflow risk.

The goal is not to chase the largest model. The goal is to choose the smallest reliable model that can complete the task safely.

## Default Recommendation

Use the committed default first when your machine can run it:

```text
qwen3-coder:30b
```

This is the current validated default for chat, edit, apply, and Agent tool workflows in this pack.

Also install the embedding model:

```text
nomic-embed-text
```

## Selection Inputs

Before choosing a model, check:

- System RAM
- GPU VRAM
- Whether Ollama is using CPU only or GPU acceleration
- Target repository size
- Required context length
- Whether the workflow needs tools
- Whether the workflow can modify files
- Risk level of the task

Larger models usually need more memory and respond more slowly, but they may follow tool and planning instructions better.

## Workflow Risk Levels

### Low Risk

Examples:

- Repository discovery
- Documentation summaries
- Explaining files
- Drafting checklists

Model guidance:

- Smaller coding models may be acceptable.
- Runtime-context workflows are acceptable if tools are unreliable.
- Human review is still required.

### Medium Risk

Examples:

- Implementation planning
- Code review
- Architecture review
- Performance triage

Model guidance:

- Prefer a stronger coding model.
- Require evidence, affected files, validation steps, and rollback steps.
- Retry with more context if the answer is generic.

### High Risk

Examples:

- Approved write mode
- Tool-backed edits
- Legacy dependency migration
- Security-sensitive recommendations
- Release-readiness decisions
- Authentication, authorization, CI, deployment, or production-data changes

Model guidance:

- Use only a model that has been validated with the exact Continue workflow.
- For tool-backed edits, verify that the model executes tools instead of printing raw JSON tool calls.
- Prefer plan-only first, then one scoped edit at a time.
- Stop if the model ignores boundaries or invents details.

## Hardware Tiers

These tiers are starting points. Exact performance depends on quantization, drivers, available memory, repository size, and what else is running.

### Low Resource

Typical machine:

- CPU-only or limited GPU
- Less than 16 GB system RAM
- Less than 8 GB VRAM

Recommended usage:

- Review-only workflows
- Documentation help
- Runtime-context workflows
- Small files and short prompts

Avoid:

- Approved write mode
- Large repository-wide context
- High-risk migrations
- Tool-heavy Agent workflows unless validated

### Medium Resource

Typical machine:

- 16-32 GB system RAM
- 8-16 GB VRAM, or strong CPU fallback

Recommended usage:

- Repository discovery
- Implementation planning
- Code review
- Documentation review
- Small approved edits after validation

Use caution with:

- Long context windows
- Large generated diffs
- Security-sensitive or release decisions

### High Resource

Typical machine:

- 32 GB or more system RAM
- 16 GB or more VRAM
- Enough headroom for editor, Ollama, build tools, and tests

Recommended usage:

- `qwen3-coder:30b` as the default coding and tool-capable model
- Agent mode after read-only tool validation
- Scoped approved edits
- Larger context windows when needed

Still required:

- Human review
- Validation
- Rollback plan
- Git diff review before commit

## Model Capability Checklist

Before using a model for tool-backed work, test it with a safe prompt:

```text
Use tools to list the repository files. Do not modify files.
```

Good result:

- Continue runs the tool.
- The assistant returns a normal text summary.

Bad result:

```json
{"name":"ls","arguments":{"dirPath":".","recursive":true}}
```

If the model prints raw JSON instead of executing the tool, do not use that model for approved write mode.

## Choosing By Task

Use this matrix as a default:

| Task | Suggested model posture |
| --- | --- |
| Discovery or summary | Any locally reliable coding model with enough context |
| Documentation drafting | Small or medium model is acceptable with review |
| Implementation planning | Prefer stronger coding model and require validation/rollback sections |
| Code review | Prefer stronger coding model and require file-specific findings |
| Architecture/security/performance review | Prefer stronger model; require evidence and assumptions |
| Tool-backed edits | Use validated tool-capable model only |
| Dependency migration or release readiness | Use strongest available model plus human review and fixed templates |

## Context Length Guidance

Use only the context needed for the task.

For small tasks:

- Current file
- Related files
- Existing tests
- Relevant docs

For larger reviews:

- Generate `runtime-context.md`
- Attach selected files
- Ask the model to state unknowns

Avoid sending an entire large repository when a focused slice is enough. More context can make local models slower and less precise.

## Local Override Safety

Keep the committed config portable.

Do not commit:

- Private IP addresses
- Private hostnames
- VPN endpoints
- Machine-specific ports
- Experimental model names that only exist on one machine
- Hardware notes that identify a private workstation

Use ignored local config files for machine-specific changes:

```text
.continue/config.local.yaml
```

If you test a new model, record only sanitized results in committed docs:

- Model family and size
- Workflow tested
- Pass or fail
- Failure mode
- No private endpoint details

## Recommended Starting Flow

1. Start with the committed default model.
2. Run a read-only repository discovery prompt.
3. Test tool execution with a safe list-files request.
4. If tools work, try plan-only workflows.
5. If planning is reliable, approve one scoped edit.
6. Validate the edit.
7. Record sanitized findings if they change the pack guidance.

## When To Use A Smaller Model

Use a smaller model when:

- The machine cannot run the default model comfortably.
- The workflow is read-only.
- The task is summarization or documentation drafting.
- The user can provide a focused context file.
- The result will be reviewed before action.

Do not use a smaller unvalidated model for high-risk tool-backed changes.

## When To Upgrade The Model

Use a stronger model when:

- The response is generic or shallow.
- The model ignores "plan only" or "do not modify files."
- The model invents package versions, file paths, test results, or endpoints.
- The model prints raw JSON tool calls.
- The task touches security, dependency management, release readiness, or production behavior.

## Related Docs

- `docs/local-model-reliability.md`
- `docs/tool-use-modes.md`
- `docs/approved-tool-backed-changes.md`
- `docs/scoped-edits.md`
- `docs/troubleshooting.md`
