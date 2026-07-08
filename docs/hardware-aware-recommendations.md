# Hardware-Aware Recommendations

The hardware-aware recommendation flow turns an existing model profile into a local model/config recommendation without contacting external services, pulling models, or rewriting editor configuration.

Use it after running one of the local or remote profile scripts:

Windows PowerShell:

```powershell
.\scripts\recommend-local-agent-config.ps1 `
  -ModelProfilePath .\runtime-validation-output\remote-model-profile.json `
  -VramSelectionMode MaxDedicated
```

Linux:

```bash
./scripts/recommend-local-agent-config.linux.sh \
  --model-profile-path ./runtime-validation-output/remote-model-profile.json \
  --vram-selection-mode MaxDedicated
```

macOS:

```bash
./scripts/recommend-local-agent-config.macos.sh \
  --model-profile-path ./runtime-validation-output/remote-model-profile.json \
  --vram-selection-mode MaxDedicated
```

## What It Reads

The script reads:

- A local model profile JSON from `get-local-model-profile.*` or `get-remote-model-profile.*`.
- `config/model-recommendations.tsv` for curated model priorities.
- `config/evidence-catalog.tsv` for validated model status.

It does not read repository source code, send hardware profiles online, call Ollama, pull models, or update `.continue/config.yaml`.

## What It Produces

The output is a sanitized JSON recommendation under `runtime-validation-output/` by default. It includes:

- Detected platform, architecture, RAM, and selected VRAM estimate.
- Candidate models with platform and VRAM fit signals.
- WRITE SAFE, PLAN ONLY, and DEEP REVIEW model lanes.
- Suggested Continue defaults for roles, context length, max tokens, and keep-alive.
- Privacy fields showing that paths, endpoints, hostnames, usernames, repository content, and raw hardware reports are not written.

## Selection Rules

The first implementation is deliberately conservative:

- WRITE SAFE requires `approved-write-ready` evidence.
- PLAN ONLY can use approved-write, read-only tool validated, or plan-review candidate models.
- DEEP REVIEW can use validated non-candidate models when they fit the hardware estimate.
- Cloud tags are not considered local Ollama pull candidates.
- MLX-tagged models are skipped unless the model host platform is macOS.
- Oversized models are marked as not fitting the available VRAM estimate instead of being pulled.

## VRAM Mode

Use `MaxDedicated` for the safest default because most local model servers run a model on one GPU. Use `TotalDedicated` only when your model server and model runner can actually use multiple GPUs effectively.

## Next Stage

This recommendation JSON is the input contract for future local config generation. Until that wiring is complete, treat the output as guidance and continue to run editor read-only and approved-write smoke tests before trusting a model for project changes.
