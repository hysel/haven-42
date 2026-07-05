# Runtime Output Verification

## Purpose

Runtime output verification adds a deterministic safety check after model output is generated.

Prompt wording is still useful, but local models can ignore instructions. The verifier checks output against the generated runtime context and marks guardrail failures without exposing private repository content.

## What It Checks

The verifier currently checks:

- File names mentioned in model output must appear in the supplied runtime context.
- Mixed filename synthesis is rejected, such as combining an add-in file basename with a project-file extension.
- Legacy dependency migration output must not include unsafe mechanical migration patterns.
- Compatibility, maintenance, lifecycle, or support claims must include source evidence or a current-source verification qualifier.

## Scripts

Windows:

```powershell
.\scripts\verify-runtime-output.ps1 `
  -OutputPath runtime-validation-output\<run>\repository-discovery.md `
  -ContextPath runtime-validation-output\<run>\runtime-context.md `
  -WorkflowName repository-discovery
```

Linux:

```bash
./scripts/verify-runtime-output.linux.sh \
  --output-path runtime-validation-output/<run>/repository-discovery.md \
  --context-path runtime-validation-output/<run>/runtime-context.md \
  --workflow-name repository-discovery
```

macOS:

```bash
./scripts/verify-runtime-output.macos.sh \
  --output-path runtime-validation-output/<run>/repository-discovery.md \
  --context-path runtime-validation-output/<run>/runtime-context.md \
  --workflow-name repository-discovery
```

## Runtime Validation Integration

`run-runtime-validation` writes a verification file next to each workflow output:

```text
repository-discovery.verification.txt
legacy-dotnet-dependency-migration.verification.txt
```

The summary marks workflows as:

- `Completed; verification passed`
- `Failed guardrail verification`
- `Tool call only output`
- `Failed with exit code ...`

Raw workflow outputs and verification files remain local in `runtime-validation-output/` until reviewed and sanitized.

## Limitations

The verifier is intentionally conservative. A failed verification does not always mean the model output is useless, but it means the output should not be treated as safe guidance without human review.

The verifier does not replace testing, source review, security review, or release validation.
