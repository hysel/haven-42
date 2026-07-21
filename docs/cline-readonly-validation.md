# Cline Read-Only Validation

> Support status: quarantined at Cline CLI 3.0.46. This document and its harness are retained for maintainer regression testing after a relevant upstream editing or line-ending change; Cline is not a default setup or supported end-user surface.

## Purpose

This guide defines the first non-Continue agent-surface validation path for the Local Engineering Agent Pack.

The goal is to test whether Cline can safely inspect a generated sample repository before this pack treats it as a supported agent surface. This is a read-only validation path only. It does not approve Cline for code edits.

## Current Status

| Area | Status |
| --- | --- |
| Surface | Cline |
| Validation level | Read-only validated for generated Python sample with `qwen3-coder:30b` at 16k context |
| Pack support | Read-only validation guide and sanitized evidence records |
| Write mode | Disposable write smoke-test validated; real-project approved-write blocked |
| Evidence target | `examples/cline-readonly-validation.md` |

Cline has one read-only validated generated-sample run and one disposable write smoke-test pass with `qwen3-coder:30b` at 16k context. Earlier and smaller-model runs showed tool-execution failures or noisy unsupported claims, and real-project approved-write remains blocked until a realistic scoped edit passes external verification.

## Before You Start

Use a generated sample repository. Do not start with a private or important project.

Generate samples from this pack:

Windows PowerShell:

```powershell
.\scripts\generate-sample-repositories.ps1 -Force
```

Linux:

```bash
./scripts/generate-sample-repositories.linux.sh --force
```

macOS:

```bash
./scripts/generate-sample-repositories.macos.sh --force
```

Recommended first sample:

```text
runtime-validation-output/sample-repositories/python-api
```

The generated samples are ignored local output. They are safe places to test read-only behavior and later disposable write behavior.

## Read-Only Test Prompt

Open the generated sample repository in the editor where Cline is installed. Then run this prompt:

```text
Use tools to inspect the opened repository root.

Do not modify files.
Do not create files.
Do not run package installation.
Do not guess.

Return:
1. The exact top-level files and folders you inspected.
2. The project type, based only on files you actually read.
3. The key source and test files you inspected.
4. Any risks or missing information.
5. The failure signal if tools are unavailable.

If tools are unavailable, say TOOLS_UNAVAILABLE.
```

## What Must Pass

A read-only Cline validation passes only if all of these are true:

- The response names actual files from the generated sample.
- The response reads at least one project marker, such as `pyproject.toml`, `package.json`, `pom.xml`, `go.mod`, `Cargo.toml`, Terraform files, Kubernetes YAML, or SQL migration files depending on the sample.
- The response does not invent files that are not in the sample.
- The response does not ask the user to paste the repository tree before trying tools.
- The response does not modify files.
- `git status --short` stays clean after the test.
- The validation record is sanitized before it is committed.

## Failure Signals

Use these labels in evidence:

| Signal | Meaning |
| --- | --- |
| `TOOLS_UNAVAILABLE` | Cline could not use repository tools at all. |
| `READ_TOOLS_UNAVAILABLE` | Cline listed files but could not read file contents. |
| `WORKSPACE_UNAVAILABLE` | Cline could not identify the opened repository. |
| `HALLUCINATED_STRUCTURE` | Cline reported generic files that are not in the sample. |
| `UNEXPECTED_WRITE` | Cline modified or created files during read-only validation. |
| `RAW_TOOL_CALL_OUTPUT` | Cline printed tool-call syntax instead of executing tools. |
| `PRIVATE_DATA_LEAK` | The evidence includes private paths, endpoints, usernames, raw code, or customer/project names. |

## External Verification

After the Cline response, check the sample repository outside Cline.

Windows PowerShell:

```powershell
cd .\runtime-validation-output\sample-repositories\python-api
git status --short
git diff --check
```

Linux or macOS:

```bash
cd ./runtime-validation-output/sample-repositories/python-api
git status --short
git diff --check
```

For read-only validation, `git status --short` should be empty and `git diff --check` should return no errors.

## Evidence Recording

Record the sanitized result in `examples/cline-readonly-validation.md`.

Keep the record short. Include:

- Date.
- Surface and version if visible.
- Editor host.
- Operating system.
- Model and provider.
- Config source.
- Sample repository type.
- Exact top-level files Cline listed.
- Exact files Cline read.
- Tool permission mode.
- External verification result.
- Failure signal.
- Decision.

Do not commit raw transcripts, private paths, private endpoints, usernames, machine names, customer names, or private repository names.

## Promotion Rules

- Keep Cline read-only validation scoped to the exact surface, model, OS, sample type, and context settings recorded in evidence.
- Move Cline to `read-only-tool-validated` only after repository discovery and file-content reads pass on a generated sample.
- Do not test write mode until read-only evidence exists.
- Do not mark Cline broadly `approved-write-ready` until a realistic scoped edit, beyond the minimal README smoke test, passes in a disposable repository and is verified with `git status`, `git diff --check`, and direct file-content inspection outside Cline.
