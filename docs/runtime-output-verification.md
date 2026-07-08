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
- `Failed guardrail verification; filename-fidelity fallback written`
- `Tool call only output`
- `Failed with exit code ...`

When verification fails with `FILENAME_NOT_IN_CONTEXT`, the runtime runner also writes a deterministic remediation artifact next to the original output:

```text
repository-discovery.filename-fidelity-fallback.md
legacy-dotnet-dependency-migration.filename-fidelity-fallback.md
```

Treat the original model output as untrusted until the filename failures are reviewed. The fallback file lists the failed filename checks and gives a safe remediation template: re-read the supplied runtime context, keep only context-backed findings, label absent useful files as `recommended new file: <path>`, use `unconfirmed filename` when evidence is missing, then rerun verification.

Raw workflow outputs, verification files, and fallback artifacts remain local in `runtime-validation-output/` until reviewed and sanitized.

## Limitations

The verifier is intentionally conservative. A failed verification does not always mean the model output is useless, but it means the output should not be treated as safe guidance without human review.

The verifier does not replace testing, source review, security review, or release validation.

## Recommended New Files

Runtime verification allows filenames that are absent from supplied context only when the output line clearly labels them as `recommended new file`, `missing file recommendation`, or an equivalent new-file recommendation. Unlabeled absent filenames still fail with `FILENAME_NOT_IN_CONTEXT`.
