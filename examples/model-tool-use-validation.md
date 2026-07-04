# Model Tool-Use Validation Evidence

Use this template to record sanitized model validation results. Keep private endpoints, local paths, repository names, customer names, usernames, secrets, and raw transcripts out of committed evidence.

## Summary

- Date:
- Validation status: Candidate | Read-only tool validated | Plan validated | Approved-write ready | Failed
- Model:
- Provider: Ollama | OpenAI-compatible local endpoint | Other
- Editor surface: VS Code | VSCodium | Continue CLI | Other
- Continue version:
- Operating system:
- CPU architecture:
- MCP state: Disabled | Enabled | Partial | Unknown
- Config source: Project-local `.continue/config.yaml` | Local `.continue/config.local.yaml` | Other

## Environment Notes

- Hardware tier:
- Memory type: Dedicated VRAM | Unified memory | Shared/integrated memory | Unknown
- Hardware profile script used: Windows | Linux | macOS | Not used
- Duplicate-rule warnings: Yes | No
- Private details removed: Yes

## Tests

| Test | Result | Notes |
| --- | --- | --- |
| Config loading | Pass | Expected model and prompts were visible. |
| Read-only repository discovery | Pass | Response referenced real files without modifying the repository. |
| Read-only tool execution | Pass | Tool execution produced a normal text summary. |
| Read-content tool execution | Not run | Confirm the model can read a harmless file such as `README.md` before approving code changes. |
| Plan-only behavior | Pass | Plan included affected files, risks, validation, rollback, and definition of done. |
| Platform-aware command use | Not run | Confirm Windows uses PowerShell commands and Linux/macOS use shell commands. |
| Approved-write smoke test | Not run | Leave as not run unless tested in a safe disposable branch or repository. |

## Failure Mode

Use this section only when something failed.

- Failed step:
- Observed behavior:
- Expected behavior:
- Safe fallback used:
- Follow-up needed:

## Decision

Choose one:

- Keep as candidate only.
- Mark as read-only tool validated.
- Mark as plan validated.
- Mark as approved-write ready for one scoped edit at a time.
- Do not recommend for tool-backed workflows.

## Sanitization Checklist

- [ ] No private endpoints.
- [ ] No private IP addresses.
- [ ] No local filesystem paths.
- [ ] No usernames.
- [ ] No private repository names.
- [ ] No customer names.
- [ ] No tokens or secrets.
- [ ] No raw private-code transcript.
