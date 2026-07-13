# Workflow Registry

## Purpose

`config/workflows.json` is the machine-readable catalog of stable workflows that scripts, future dispatchers, and the planned starter-toolkit web UI can use.

The registry keeps workflow metadata in one place so the project can reduce script duplication without losing beginner-friendly entry points.

Use `docs/workflow-chooser.md` for a generated report that compares workflow IDs, safety levels, commands, and reference docs.

Use `docs/script-consolidation-plan.md` for the boundary between shared engines, thin wrappers, and scripts that should remain explicit.

## What It Describes

Each workflow records:

- `id`: Stable workflow identifier for scripts and UI.
- `name`: Human-readable label.
- `purpose`: Short description of what the workflow does.
- `category`: Grouping such as discovery, configuration, validation, model-selection, or release-readiness.
- `safetyLevel`: Expected safety boundary.
- `uiReady`: Whether the workflow is a reasonable candidate for the future UI.
- `inputs`: User or caller-provided values.
- `outputs`: Expected output artifacts or result types.
- `entryPoints`: Platform-specific script paths for Windows, Linux, and macOS.

## Safety Levels

| Safety level | Meaning |
| --- | --- |
| `read-only` | Reads local files or local service state only. |
| `network-read` | Reads public or configured remote metadata. |
| `network-write` | Downloads or changes remote/local model state. |
| `controlled-write` | Writes generated output, reports, samples, or test artifacts. |
| `approved-write` | Changes user-facing config or repository assets and should require explicit user approval or dry-run review. |

## UI Direction

The planned web UI should read this registry rather than hard-code every script. It should show:

- What the workflow will read or write.
- Which platform entry point will run.
- Whether the workflow is read-only, controlled-write, network-write, or approved-write.
- Which outputs are safe to inspect, copy, or commit.
- Whether the workflow has validation evidence or is still recommendation-only.

The UI should remain a wrapper over tested scripts and shared engines. It should not reimplement hardware profiling, model selection, model testing, install, or validation logic.

## Dispatcher Boundary

`scripts/invoke-workflow.ps1` is the first stable dispatcher over the registry. It is intentionally small:

- `-List` prints the available workflow IDs, names, categories, safety levels, and UI readiness.
- `-WorkflowId <id> -DryRun` resolves the platform-specific entry point without invoking it.
- `-WorkflowId <id> -- <args>` invokes the resolved script and passes remaining arguments through in an interactive shell.
- `-WorkflowArgumentsJson '["<arg>","<value>"]'` passes workflow-specific arguments through in automation that shells through `pwsh -File`.
- `-Json` emits machine-readable list or resolution output for future UI callers.

Examples:

```powershell
.\scripts\invoke-workflow.ps1 -List
.\scripts\invoke-workflow.ps1 -WorkflowId validate-pack -DryRun
.\scripts\invoke-workflow.ps1 -WorkflowId validate-pack -- -ExpectedVersion 0.2.0
pwsh -NoProfile -File .\scripts\invoke-workflow.ps1 -WorkflowId validate-pack -WorkflowArgumentsJson '["-ExpectedVersion","0.2.0"]'
```

The dispatcher does not reinterpret workflow-specific arguments. Each underlying script remains the source of behavior, validation, and safety checks.

## Autonomous Maintenance

Use `docs/autonomous-maintainer-queue.md` for safe follow-up work that can proceed without more product input. The queue keeps autonomous changes tied to existing roadmap, TODO, registry, docs, and evidence boundaries.

## Maintenance Rules

- Keep paths repository-relative.
- Do not include hostnames, IP addresses, usernames, tokens, private repository names, or local machine paths.
- Add new workflows only after the entry scripts exist or the roadmap clearly marks them as future work.
- Prefer adding shared workflow entries over adding new per-plugin script families.
- Follow `docs/script-consolidation-plan.md` before merging or removing script families.
- Update `scripts/test-pack.ps1` when the registry schema changes.
