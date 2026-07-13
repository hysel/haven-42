# Script Reference Appendix

This appendix is the long-form home for individual script documentation.

The main user experience should stay workflow- and intent-based. Start with `docs/agent-pack-menu.md` or `docs/beginner-setup-mode.md` before choosing individual scripts.

Individual script docs remain available here for advanced users, maintainers, automation authors, and troubleshooting. They should not be the primary navigation path for beginners.

Use `docs/workflow-chooser.md` for a generated complete workflow list before dropping down to individual script arguments.

## Navigation Rules

- User-facing docs should start from intent, not script name.
- Script docs should explain exact parameters, safety level, outputs, and examples.
- Workflow docs should point to this appendix only when users need detailed command options.
- Appendix docs should preserve script-level references rather than hiding or deleting them.
- `config/workflows.json` is the source of truth for workflow IDs, entry points, safety levels, inputs, and outputs.

## Workflow Reference

| Workflow | Intent | Safety | UI | Windows entry point | Reference |
| --- | --- | --- | --- | --- | --- |
| `apply-agent-config` | Write local-only agent configuration from a recommendation result with dry-run support. | `approved-write` | yes | `scripts/apply-recommended-agent-config.ps1` | `docs/hardware-aware-recommendations.md` |
| `build-release-package` | Create release archives, checksums, and release artifacts after validation passes. | `controlled-write` | no | `scripts/build-release-package.ps1` | `docs/release.md` |
| `cleanup-local-agent-artifacts` | Safely remove ignored local validation output, generated samples, backup folders, and failed diagnostic artifacts after dry-run review. | `controlled-write` | yes | `scripts/cleanup-local-agent-artifacts.ps1` | `docs/workflow-registry.md` |
| `discover-online-models` | Suggest candidate local models from public model metadata while keeping recommendations evidence-gated. | `network-read` | yes | `scripts/discover-online-model-candidates.ps1` | `docs/online-model-discovery.md` |
| `generate-evidence-dashboard` | Summarize evidence status, agent surface readiness, and tested model coverage from committed sanitized catalogs. | `read-only` | yes | `scripts/generate-evidence-dashboard.ps1` | `docs/evidence-dashboard.md` |
| `generate-model-scorecard` | Summarize model readiness by model, surface, status, and evidence from the committed evidence catalog. | `read-only` | yes | `scripts/generate-model-scorecard.ps1` | `docs/model-scorecard.md` |
| `generate-runtime-context` | Create sanitized repository context for model-backed validation and review workflows. | `read-only` | yes | `scripts/generate-runtime-context.ps1` | `docs/runtime-validation.md` |
| `generate-sample-repositories` | Create deterministic disposable sample repositories for validation without private source code. | `controlled-write` | yes | `scripts/generate-sample-repositories.ps1` | `docs/sample-repository-factory.md` |
| `get-beginner-setup-plan` | Create an ordered first-run setup plan that links beginner commands to stable workflow registry entries. | `read-only` | yes | `scripts/get-beginner-setup-plan.ps1` | `docs/beginner-setup-mode.md` |
| `install-pack-assets` | Install or update project-local or centralized agent assets with backups, dry-run, and global config support. | `approved-write` | yes | `scripts/install-continue-pack.ps1` | `docs/shared-asset-installation.md` |
| `profile-local-hardware` | Collect sanitized CPU, RAM, GPU, VRAM, platform, and local model information for model recommendation. | `read-only` | yes | `scripts/get-local-model-profile.windows.ps1` | `docs/hardware-aware-recommendations.md` |
| `profile-remote-hardware` | Collect sanitized hardware and model profile information from a remote model host over SSH. | `read-only` | yes | `scripts/get-remote-model-profile.ps1` | `docs/remote-hardware-profile.md` |
| `pull-local-agent-models` | Download selected local model candidates after hardware and validation review. | `network-write` | yes | `scripts/pull-local-agent-models.ps1` | `docs/local-agent-model-testing.md` |
| `recommend-agent-config` | Create hardware-aware model lanes and local configuration recommendations from sanitized profile and evidence data. | `read-only` | yes | `scripts/recommend-local-agent-config.ps1` | `docs/hardware-aware-recommendations.md` |
| `run-runtime-validation` | Execute configured validation prompts, collect raw local outputs, and optionally append sanitized summaries. | `controlled-write` | yes | `scripts/run-runtime-validation.ps1` | `docs/runtime-validation.md` |
| `show-agent-pack-menu` | Generate a short intent-based menu over stable workflows so users do not need to choose from individual scripts. | `read-only` | yes | `scripts/show-agent-pack-menu.ps1` | `docs/agent-pack-menu.md` |
| `show-workflow-chooser` | Generate a complete registry-backed workflow chooser with safety levels, commands, and reference docs. | `read-only` | yes | `scripts/show-workflow-chooser.ps1` | `docs/workflow-chooser.md` |
| `test-agent-cli-surface` | Screen CLI-capable agent surfaces with read-only and disposable write-smoke checks through the shared harness. | `controlled-write` | yes | `scripts/test-agent-cli-surface-models.ps1` | `docs/agent-cli-surface-model-testing.md` |
| `test-local-agent-health` | Check local setup health for repository config, runtime output, and optional Ollama reachability without mutating user files. | `read-only` | yes | `scripts/test-local-agent-health.ps1` | `docs/workflow-registry.md` |
| `test-local-agent-models` | Run API-level model preflight checks, optional pulls, cleanup, and unload behavior against a local model server. | `controlled-write` | yes | `scripts/test-local-agent-models.ps1` | `docs/local-agent-model-testing.md` |
| `test-pack` | Run the repository test suite used before commits, pushes, and releases. | `controlled-write` | yes | `scripts/test-pack.ps1` | `docs/release.md` |
| `test-release-readiness` | Run the release gate for validation, tests, release package dry-run, git state, workflow registry, and agent-surface parity. | `controlled-write` | yes | `scripts/test-release-readiness.ps1` | `docs/release.md` |
| `validate-pack` | Run static pack validation for config, docs, scripts, references, and safety invariants. | `read-only` | yes | `scripts/validate-pack.ps1` | `docs/release.md` |
| `verify-runtime-output` | Check runtime validation output for invented filenames, unsupported claims, and other deterministic failure signals. | `read-only` | yes | `scripts/verify-runtime-output.ps1` | `docs/runtime-output-verification.md` |

## Direct Invocation

Use the dispatcher when you want a stable workflow ID instead of a script path:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/invoke-workflow.ps1 -List
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/invoke-workflow.ps1 -WorkflowId show-agent-pack-menu -DryRun
```

Use the platform-specific entry points when you need exact script behavior or script-specific arguments. The registry lists Windows, Linux, and macOS entry points for every workflow.

## Safety Levels

| Safety level | Meaning |
| --- | --- |
| `read-only` | Reads local files or generated evidence without changing user assets. |
| `network-read` | Reads public network metadata without installing or changing local assets. |
| `network-write` | Downloads or pulls selected assets after review. |
| `controlled-write` | Writes only to explicit output folders, disposable samples, generated reports, or dry-run-reviewed cleanup targets. |
| `approved-write` | Can change target repository config or installed assets and should use dry-run/review before apply. |

## Maintenance Rule

When a workflow is added to `config/workflows.json`, add it to this appendix, link an appropriate reference doc, and keep beginner-facing docs pointed at `docs/agent-pack-menu.md` first.
