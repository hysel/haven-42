# MLX Model Validation Evidence

This record captures a bounded native Apple Silicon validation of a local MLX
server. It is sanitized and intentionally does not include machine paths,
addresses, credentials, or raw model transcripts.

## Environment

- Platform: native macOS on Apple Silicon.
- Runtime: `mlx-lm` 0.31.3 installed in a Python 3.12 virtual environment.
- Model: `mlx-community/Qwen3.5-9B-OptiQ-4bit`.
- Server: local OpenAI-compatible MLX endpoint bound to loopback only.
- Agent surface: Continue CLI 1.5.47.

## Results

| Capability | Result | External verification | Boundary |
| --- | --- | --- | --- |
| Qwen 3.5 9B OptiQ 4-bit endpoint tool call | Passed | The endpoint returned a required function call with valid JSON arguments. | Endpoint-level evidence only. |
| Qwen 3.5 9B OptiQ 4-bit Continue CLI read, plan, review, and scoped write smoke | Passed | Read-only responses cited fixture files; only `README.md` changed in the write smoke, the exact final marker was present once, and `git diff --check` passed before cleanup. | One-file disposable write only; not broad approved-write or editor evidence. |
| Qwen 3.5 9B 4-bit endpoint tool call | Passed | The endpoint returned a required function call with valid JSON arguments. | Separate quantization evidence; editor behavior remains unproven. |
| Qwen 3.5 9B 4-bit Continue CLI read and scoped write smoke | Passed | The focused read response cited the approved fixture files; only `README.md` changed in the write smoke and external Git checks passed before cleanup. | The plan was useful but did not cite every requested file, so it is not promoted as strict plan evidence. |
| Devstral Small 2 24B 4-bit endpoint tool call | Failed | The MLX endpoint returned a normal response but not the required structured tool call. | The server logged a Mistral tokenizer regex warning; the installed server did not expose the documented fix as a command-line option. Do not use this MLX candidate for tool-backed workflows. |

## Outcome

The tested model is a validated MLX candidate for bounded Continue CLI read,
planning, review, and disposable scoped-write smoke workflows on an Apple
Silicon host. It must be revalidated for a different MLX quantization, server
version, Continue version, editor surface, repository type, or write scope.

The baseline Qwen 3.5 9B 4-bit quantization passed endpoint, focused Continue
CLI read, and disposable scoped-write checks. It does not yet have the same
strict plan and review evidence as the OptiQ quantization. Devstral Small 2
24B 4-bit is intentionally excluded from MLX tool-backed recommendations until
the tokenizer/runtime issue is resolved and independently retested.

On 2026-07-17, the OptiQ model also ran through the native language workflow
matrix runner after the host's non-interactive Homebrew `npx` path was resolved.
It completed direct tool-backed Continue CLI reads and writes, but returned an
empty final response for the matrix's evidence-heavy discovery prompt, even
with a larger response allowance. The endpoint and runner were healthy. Keep
the model eligible for its bounded smoke workflows, but do not promote it as a
full cross-language default until all required matrix cells emit evidence-
bearing output and scoped writes pass external diff verification.
