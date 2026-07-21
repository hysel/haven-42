# Kilo Code Validation Evidence

## 2026-07-21 Windows Generated-Sample Validation

### Boundary

- Surface: Kilo Code CLI 7.4.11 on Windows.
- Provider: Ollama through a local-only project configuration.
- Target: disposable generated Python sample.
- Configuration: documented `.kilo/kilo.jsonc`, explicit `code` agent, isolated user profile, and one-model-at-a-time preload/unload policy.
- Private endpoint, local paths, raw output, and user-profile data are omitted.

The locally installed version matched the current npm package version, so no
Kilo upgrade was available before testing.

### Results

| Model | Read-only | README write smoke | Source/test scoped edit | Process behavior | Decision |
| --- | --- | --- | --- | --- | --- |
| `devstral-small-2:24b` | Passed | Failed | Failed | Each failed write phase exited `0` without producing an externally valid edit | Retain read-only evidence only; writes blocked |
| `qwen3.5:35b` | Failed | Failed | Failed | Every phase exited `0` without satisfying its external gate | Candidate rejected for Kilo tasks |

Devstral reproduced the previously observed Kilo behavior rather than resolving
it. Qwen 35B was selected as the single alternative because it has stronger
write evidence on another CLI surface, but it performed worse through Kilo.
No additional models should be cycled through Kilo 7.4.11 without a concrete
tool-protocol or task-execution change.

### External Verification And Cleanup

- Write and scoped-edit status came from Git/file-content verification, not the CLI exit code.
- The generated repository was restored after each phase.
- Both models were unloaded after their runs.
- A Kilo cleanup warning reported that an isolated `.continue/` directory could not be removed; no tracked target-repository change remained.
- The shared harness was updated to return a nonzero process status whenever any requested validation gate reports `failed`, preventing exit-0 model failures from appearing successful in automation.

### Promotion Decision

Kilo remains read-only validated only for the exact Devstral generated-sample
scenario. Write-smoke, scoped-edit, and real-project approved-write support stay
blocked. The next useful gate requires a Kilo task-execution/tool-protocol fix
or version change, followed by the same externally verified test sequence.
