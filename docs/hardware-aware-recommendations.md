# Hardware-Aware Recommendations

The hardware-aware recommendation flow turns an existing model profile into a local model/config recommendation without contacting external services, pulling models, or rewriting editor configuration.

Use `docs/config-generation-strategy.md` to decide whether recommendation output should become project-local config, global Continue config, shared-assets config, or future surface-specific config.

Use it after running one of the local or remote profile scripts:

Windows PowerShell:

```powershell
.\scripts\recommend-local-agent-config.ps1 `
  -ModelProfilePath .\runtime-validation-output\remote-model-profile.json `
  -VramSelectionMode MaxDedicated `
  -ContextTargetTokens 16384 `
  -MemoryReserveGb 4
```

Linux:

```bash
./scripts/recommend-local-agent-config.linux.sh \
  --model-profile-path ./runtime-validation-output/remote-model-profile.json \
  --vram-selection-mode MaxDedicated \
  --context-target-tokens 16384 \
  --memory-reserve-gb 4
```

macOS:

```bash
./scripts/recommend-local-agent-config.macos.sh \
  --model-profile-path ./runtime-validation-output/remote-model-profile.json \
  --vram-selection-mode MaxDedicated \
  --context-target-tokens 16384 \
  --memory-reserve-gb 4
```

## What It Reads

The script reads:

- A local model profile JSON from `get-local-model-profile.*` or `get-remote-model-profile.*`.
- `config/model-recommendations.tsv` for curated model priorities.
- `config/model-fit-profiles.json` for versioned memory-planning assumptions.
- `config/evidence-catalog.tsv` for validated model status.

It does not read repository source code, send hardware profiles online, call Ollama, pull models, or update `.continue/config.yaml`.

Evidence selection follows Capability Evidence Contract v2. The default target
is Continue Agent, surface version `not-recorded`, provider `Ollama`, and the
operating system from the hardware profile. PowerShell accepts `-Surface`,
`-SurfaceVersion`, and `-Provider`; Linux and macOS accept the corresponding
`--surface`, `--surface-version`, and `--provider` options.

The scripts require an exact surface, version, provider, OS, operation, and
validation-mode match. They do not inherit write readiness from another agent
surface or use read-only evidence as plan, review, or write evidence. A model
lane remains empty when its exact operation evidence is missing.

## What It Produces

The output is a sanitized JSON recommendation under `runtime-validation-output/` by default. It includes:

- Detected platform, architecture, RAM, and selected VRAM estimate.
- Candidate models with platform and VRAM fit signals, installed status, parsed model size, and lane-specific scores.
- WRITE SAFE, PLAN ONLY, and DEEP REVIEW model lanes. A lane can be empty when exact evidence is unavailable.
- A surface-neutral `ModelLanes` contract that future surfaces can read without inheriting Continue config syntax.
- Suggested Continue defaults for roles, context length, max tokens, and keep-alive.
- Privacy fields showing that paths, endpoints, hostnames, usernames, repository content, and raw hardware reports are not written.

## Selection Rules

Selection policy version 1 is evidence-gated and lane-specific:

- Every lane requires an exact Capability Evidence Contract v2 match for the requested surface, surface version, provider, operating system, operation, and validation mode.
- WRITE SAFE requires `approved-write-ready` scoped-write evidence. Eligible models receive an installed-model bonus and a VRAM-headroom score so the result remains reliability-first.
- PLAN ONLY requires `plan-validated` plan evidence. Eligible models receive a small installed-model bonus and a capacity score so a larger fitting validated planner can outrank a smaller model.
- DEEP REVIEW requires `review-validated` review evidence. Eligible models receive a small installed-model bonus and a capacity score so a larger fitting validated reviewer can outrank a smaller model.
- Missing or mismatched lane evidence makes that candidate ineligible instead of borrowing readiness from another lane or surface.
- Cloud tags are not considered local Ollama pull candidates.
- MLX-tagged models are skipped unless the model host platform is macOS.
- Oversized models are marked as not fitting the available VRAM estimate instead of being pulled.

Each candidate exposes `LaneScores` with `Eligible`, `Score`, `RequiredStatus`, `EvidenceStatus`, and `Rationale`. The report-level `SelectionPolicy` identifies the policy version and summarizes each lane's ranking rule.

Fit policy version 1 uses `config/model-fit-profiles.json` for exact curated tags. Each profile discloses its quantization assumption, estimated weight memory, cache memory at a baseline context, runtime overhead, dense or mixture-of-experts architecture, total and active parameter counts, and reserve policy. `-ContextTargetTokens` / `--context-target-tokens` scales the cache estimate. `-MemoryReserveGb` / `--memory-reserve-gb` replaces the profile reserve for the current run.

Unknown tags use a `low`-confidence model-name heuristic and expose that source in `ModelFit.Source`; they are not silently treated as measured profiles. Catalog values are planning assumptions, not guarantees. Verify the exact installed artifact, quantization, runner, drivers, concurrent load, and observed memory use before relying on a borderline fit.

`ModelLanes` is the reusable recommendation contract for surface adapters. `ContinueProfiles` is the Continue-specific projection used by the Continue apply script. The Aider adapter consumes a selected `ModelLanes` lane and emits Aider-native config; do not generate Cline, Roo Code, Kilo Code, OpenCode, or other surface config directly from `ContinueProfiles`.

## VRAM Mode

Use `MaxDedicated` for the safest default because most local model servers run a model on one GPU. Use `TotalDedicated` only when your model server and model runner can actually use multiple GPUs effectively.

## Apply The Recommendation To Local Config

After reviewing the recommendation JSON, generate a local-only Continue config:

Windows PowerShell:

```powershell
.\scripts\apply-recommended-agent-config.ps1 `
  -TargetRepo C:\path\to\your-project `
  -RecommendationPath .\runtime-validation-output\model-config-recommendation.json `
  -OllamaBaseUrl http://your-local-ollama-host:11434
```

Linux:

```bash
./scripts/apply-recommended-agent-config.linux.sh \
  --target-repo /path/to/your-project \
  --recommendation-path ./runtime-validation-output/model-config-recommendation.json \
  --ollama-base-url http://your-local-ollama-host:11434
```

macOS:

```bash
./scripts/apply-recommended-agent-config.macos.sh \
  --target-repo /path/to/your-project \
  --recommendation-path ./runtime-validation-output/model-config-recommendation.json \
  --ollama-base-url http://your-local-ollama-host:11434
```

The generated file is:

```text
.continue/config.local.yaml
```

Do not commit this file. It may contain private model choices or a private Ollama endpoint.

Run with `-DryRun` or `--dry-run` first if you want to inspect what would happen without writing the local config.

## Apply The Recommendation To Global Continue Config

Some editor installations, especially Windows VS Code or VSCodium setups, load the global Continue config instead of the project-local `.continue/config.local.yaml`. Do not copy `config.local.yaml` into the global Continue config by hand. The local config uses project-relative `file://./...` references, and a global copy can make Continue look for prompts under the editor install folder.

Instead, let the apply script generate the global config with absolute references to the target repository:

Windows PowerShell:

```powershell
.\scripts\apply-recommended-agent-config.ps1 `
  -TargetRepo C:\path\to\your-project `
  -RecommendationPath .\runtime-validation-output\model-config-recommendation.json `
  -OllamaBaseUrl http://your-local-ollama-host:11434 `
  -GlobalConfig
```

Linux:

```bash
./scripts/apply-recommended-agent-config.linux.sh \
  --target-repo /path/to/your-project \
  --recommendation-path ./runtime-validation-output/model-config-recommendation.json \
  --ollama-base-url http://your-local-ollama-host:11434 \
  --global-config
```

macOS:

```bash
./scripts/apply-recommended-agent-config.macos.sh \
  --target-repo /path/to/your-project \
  --recommendation-path ./runtime-validation-output/model-config-recommendation.json \
  --ollama-base-url http://your-local-ollama-host:11434 \
  --global-config
```

The generated global config backs up the previous global config and omits `rules:` by default. That avoids duplicate rule warnings when the opened repository also contains `.continue/rules`. Use `-GlobalConfigIncludeRules` or `--global-config-include-rules` only when the editor will not load the project-local `.continue` folder.

## Next Stage

The recommendation JSON can generate local-only Continue config or feed the supported Aider adapter. Continue to run surface-specific read-only and approved-write smoke tests before trusting a model for project changes.

## Shared Asset Planning

Hardware-aware config generation currently writes project-local or global Continue config references for the selected target repository. For users who manage many repositories from one machine, see `docs/shared-asset-installation.md` for centralized shared-assets mode. The installer can now copy reusable assets into one local folder and generate global Continue config references to that folder with `-SharedAssets` or `--shared-assets`.
