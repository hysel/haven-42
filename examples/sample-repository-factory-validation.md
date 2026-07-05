# Sample Repository Factory Validation Evidence

This file records sanitized validation evidence for generated sample repositories.

Do not include private repository names, private paths, private endpoints, usernames, hostnames, tokens, raw private source code, or raw transcripts.

## 2026-07-05 Initial Factory Validation

### Summary

- Validation type: Generated sample repository factory smoke test
- Repository categories: Python API sample, TypeScript frontend sample
- Operating system: Windows
- Editor surface: Not used for this evidence entry
- Continue version: Not used for this evidence entry
- Model: Not used for this evidence entry
- Provider: Not used for this evidence entry
- MCP state: Not used
- Pack version or commit: `0.2.0` plus sample factory implementation

### Setup

- Generated samples with the PowerShell sample repository factory using overwrite mode.
- Installed the pack into the generated Python API sample after dry-run preview.
- Installed the pack into the generated TypeScript frontend sample after dry-run preview.
- Generated runtime context files for both samples.
- Kept generated sample repositories and runtime context files under ignored runtime output.

### Results

| Sample | Factory generation | Pack install dry run | Pack install | Runtime context generation | Notes |
| --- | --- | --- | --- | --- | --- |
| `python-api` | Passed | Passed | Passed | Passed | Validates Python API repository shape and installed pack references. |
| `typescript-frontend` | Passed | Passed | Passed | Passed | Validates TypeScript frontend repository shape and installed pack references. |

### Tool Validation

- File listing worked: Not applicable; this entry validates scripts, not editor Agent tools.
- File content reading worked: Runtime context generation completed for both samples.
- Current-folder path resolution worked: Not applicable; no editor Agent write was performed.
- Apply target matched intended file: Not applicable; no approved write was performed.
- External shell or git verification passed: Yes, script exit codes were successful.
- Failure signals: None observed during script validation.

### Findings

1. The factory can create deterministic disposable validation repositories without needing additional real repositories.
2. The installer can copy the pack into generated samples after dry-run preview.
3. Runtime context generation can inspect generated Python and TypeScript sample repositories.
4. This evidence does not prove model or editor Agent behavior; those still require editor-based read-only and approved-write validation.

### Pack Follow-Up

- Prompt updates needed: None from this script-only validation pass.
- Rule updates needed: None from this script-only validation pass.
- Documentation updates needed: Keep sample factory docs linked from README, wiki, and roadmap.
- Script or test updates needed: None; validation and tests already cover factory shape and script behavior.
- No-change rationale: This evidence only records the first generated-sample smoke test. Model/editor validation should be recorded separately.

### Sanitization Checklist

- [x] No private repository names.
- [x] No private local paths.
- [x] No private endpoints, IP addresses, or hostnames.
- [x] No usernames.
- [x] No tokens or secrets.
- [x] No raw private source code.
- [x] No raw transcripts.
- [x] No customer, employer, or internal project identifiers.
