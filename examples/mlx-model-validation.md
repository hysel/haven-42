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
| Qwen 3.5 4B 4-bit endpoint tool call | Passed | The endpoint returned a required function call with valid JSON arguments. | Small-model endpoint evidence only; editor behavior remains unproven. |
| Qwen 3.5 4B 4-bit Continue CLI read and scoped write smoke | Passed | The focused read returned the inspected fixture project name; only `README.md` changed in the write smoke, the exact marker was present once, and `git diff --check` passed before cleanup. | Do not infer plan, review, editor Agent, or full language-matrix readiness. |
| Qwen 3.5 4B 4-bit VSCodium Continue Agent strict write smoke | Partial pass | The agent edited the correct existing disposable file, but appended rather than replaced the baseline content and introduced a trailing blank line in two attempts; `git diff --check` failed. | Do not use this model for VSCodium approved writes. |
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

The smaller Qwen 3.5 4B 4-bit quantization passed the endpoint structured-tool
call plus focused Continue CLI read and disposable scoped-write checks. A
strict VSCodium replacement test then failed content-fidelity and whitespace
verification in two attempts. It is a low-resource candidate for targeted
read-only and Continue CLI workflows, not a substitute for the 9B OptiQ
model's plan, review, or editor-write evidence.

On 2026-07-17, the OptiQ model also ran through the native language workflow
matrix runner after the host's non-interactive Homebrew `npx` path was resolved.
It completed direct tool-backed Continue CLI reads and writes, but returned an
empty final response for the matrix's evidence-heavy discovery prompt, even
with a larger response allowance. The endpoint and runner were healthy. Keep
the model eligible for its bounded smoke workflows, but do not promote it as a
full cross-language default until all required matrix cells emit evidence-
bearing output and scoped writes pass external diff verification.

## 2026-07-17 VSCodium Continue Agent Scoped Edit

This later interactive editor validation used the same OptiQ MLX model through
the loopback-only OpenAI-compatible endpoint. The Continue and VSCodium
versions were not recorded, so this is deliberately narrow evidence.

| Capability | Result | External verification | Boundary |
| --- | --- | --- | --- |
| VSCodium Continue Agent repository read | Passed | The agent listed the generated Python fixture's actual top-level files and folders. | One generated fixture and one interactive editor session. |
| VSCodium Continue Agent Python scoped edit | Passed | The agent changed only `app/settings.py`, `app/main.py`, and `tests/test_main.py` to add a default version value and expose it through the health response. `python -m app.main`, `python -m pytest`, and `git diff --check` passed. | Manual Apply/save was required in the editor. This is generated-sample evidence only, not real-project or broad-write approval. |

The successful edit was performed after the Python fixture's disposable virtual
environment was prepared. The fixture ignores `.venv`, `__pycache__`, and
`.pytest_cache`, so test artifacts did not affect the changed-file check.

Do not infer support for another editor, Continue version, MLX server version,
model quantization, language, or repository from this result. Repeat the
read, edit, direct-run, test, and external-diff checks for each intended setup.

## 2026-07-18 VSCodium Continue Agent 4B Strict Write Result

On a constrained Apple Silicon host, the 4B model completed an interactive
VSCodium Continue Agent write against an existing disposable file. In two
strict replacement attempts, it targeted the correct file but appended the
required marker instead of replacing the baseline content and added trailing
blank lines. External `git diff --check` reported the whitespace error, while
the fixture's Python test still passed. This is a content-fidelity failure, so
the model is not approved for VSCodium writes on this evidence.
