# Native VS Code Chat Validation Evidence

This document records sanitized evidence for the maintained native VS Code
Chat surface. It contains no private endpoint, local path, username, host
identity, credential, or raw transcript.

## 2026-08-17 Read-Only Repository Inspection

### Exact configuration

- Editor: VS Code `1.133.0`
- Chat surface: native VS Code Chat
- Local-model extension: official Ollama extension `0.0.8`
- Provider: Ollama
- Model: `qwen3.8:27b`
- Operating system: Windows
- Repository: generated disposable Python API fixture
- Mode: read-only repository inspection

### Observed result

The assistant read `app/main.py` and `tests/test_main.py`, followed the import
to `app/settings.py`, and accurately explained:

- the two exact keys returned by `build_health_response`;
- how the default `service_name` value reaches the response; and
- that the existing equality assertion rejects missing or additional keys.

The prompt prohibited command execution. The assistant therefore declined to
claim that Git was clean without running `git status`. That limitation was
correct. An external preflight had established a clean disposable fixture,
but the editor assistant did not independently verify repository state.

The response made no edits and ran no terminal commands. A brief recovery from
an initially malformed path was visible but did not change the final grounded
answer.

### Decision

- Mark this exact capability cell `read-only-tool-validated`.
- Do not infer plan, review, terminal, edit, approved-write, or broad coding
  readiness.
- Validate every later native Chat, extension, model, operating-system, and
  operation combination separately.

## 2026-08-17 Qwen 3.5 4B Read-Only Comparison

### Exact configuration

- Editor: VS Code `1.133.0`
- Chat surface: native VS Code Chat
- Local-model extension: official Ollama extension `0.0.8`
- Provider: Ollama
- Model: `qwen3.5:4b`
- Operating system: Windows
- Repository: generated disposable Python API fixture
- Mode: read-only repository inspection

### Observed result

The assistant read the three explicitly permitted files, accurately described
the two-key response, traced the default service name through `Settings`, and
explained the exact dictionary equality asserted by the test. It made no edits
and ran no commands. It correctly declined to confirm Git cleanliness and
listed the repository states that cannot be excluded without `git status`.

### Decision

- Mark this exact capability cell `read-only-tool-validated`.
- This comparison does not establish plan, review, terminal, edit,
  approved-write, or broad coding readiness.
