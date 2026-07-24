# Writing Model Matrix Validation

## Scope

This sanitized record covers an initial automated writing-constraint screen on
Ollama `0.32.1` using a user-controlled Linux NVIDIA host. The exact endpoint,
host identity, raw prompts, response text, and machine paths are intentionally
omitted. The committed harness uses only embedded synthetic material and
persists neither prompts nor raw output.

This evidence is not a comparative writing-quality promotion. Blind human review,
broader repeated sampling, long-form coherence, multilingual coverage, license review,
and exact hardware utilization evidence remain open.

## Exact artifacts

| Candidate | Ollama digest | Automated cases | Average generation rate | Final state |
| --- | --- | ---: | ---: | --- |
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 3/3 passed | 76.15 tokens/s | unloaded |
| `gemma3:12b` | `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | 3/3 passed | 53.99 tokens/s | unloaded |
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | `5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b` | 3/3 passed | 41.13 tokens/s | unloaded |
| `granite4:7b-a1b-h` | `566b725534ea0e9824f844abe6a78e1ab6f7357f1efb549be94908cb681513bb` | 2/3 passed | 127.02 tokens/s | unloaded |

The cases covered a concise professional email, a fact- and
uncertainty-preserving rewrite, and a structured source-grounded brief. Qwen,
Gemma, and Mistral retained every required marker and avoided every forbidden
marker. Granite omitted one required uncertainty phrase in the structured
brief; it remains a candidate and gains no recommendation authority.

Each request used `think:false`, temperature zero, a 512-token generation
bound, and `keep_alive: 0`. The harness called the unload API and checked
`/api/ps` after every case. All twelve per-case checks and the final independent
residency check reported no loaded evaluation model.

## Repeatability check

A second complete run on 2026-07-24 used the same provider version, exact model
digests, synthetic prompts, and bounds. Qwen, Gemma, and Mistral again passed
all three cases. Granite again passed the email and fact-preserving rewrite but
omitted the required `no safety conclusion` uncertainty phrase in the
structured brief. Average generation rates were 75.86, 54.25, 41.20, and
127.64 tokens per second respectively; these host-specific measurements are
diagnostic only.

Every per-case unload and every final model unload passed. A separate final
`/api/ps` request confirmed that the provider had no loaded models. No model
was downloaded, no response text was retained, and the local endpoint remains
excluded from this evidence.

## Limits and promotion boundary

- Automated marker checks measure constraint retention, not prose quality.
- Two samples per case are still insufficient for a stable comparative ranking.
- Provider timing includes model-load effects and does not transfer to another
  host, provider version, digest, quantization, context, or concurrency.
- Human reviewers have not scored instruction compliance, organization, tone,
  repetition, unsupported additions, or overall writing quality.
- Qwen remains the bounded adapter baseline. This result does not promote
  Gemma, Mistral, or Granite as an automatic default.

The reusable harness is `scripts/run-writing-model-matrix.py`.
