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

A bounded three-repetition run on the same date then produced nine samples per
candidate. Gemma and Mistral passed all 9/9 constraint and unload checks.
Granite passed 6/9; each structured-brief repetition omitted the same required
uncertainty phrase. The first Qwen cell was invalidated because a concurrent
diagnostic temporarily made two per-sample residency checks non-empty, although
its content constraints passed. That cell was discarded and rerun alone: Qwen
passed all 9/9 constraint and unload checks. Average generation rates in the
valid cells were 76.26, 53.98, 41.18, and 127.12 tokens per second for Qwen,
Gemma, Mistral, and Granite respectively. Final independent `/api/ps` audits
were empty. This additional automation still does not replace blind human
quality review.

## Limits and promotion boundary

- Automated marker checks measure constraint retention, not prose quality.
- Three deterministic samples per case are still insufficient for a stable
  comparative writing-quality ranking.
- Provider timing includes model-load effects and does not transfer to another
  host, provider version, digest, quantization, context, or concurrency.
- Human reviewers have not scored instruction compliance, organization, tone,
  repetition, unsupported additions, or overall writing quality.
- Qwen remains the bounded adapter baseline. This result does not promote
  Gemma, Mistral, or Granite as an automatic default.

The reusable harness is `scripts/run-writing-model-matrix.py`.

## Expanded installed-model screen

An additional bounded run on 2026-07-31 screened eight models that were already
installed on the same private NVIDIA provider. The host reported Ollama
`0.32.5` and approximately 250 GB free before the run. No model was downloaded,
and neither prompts nor response text were retained.

| Candidate | Ollama digest | Automated cases | Average generation rate | Final state |
| --- | --- | ---: | ---: | --- |
| `qwen3.5:0.8b` | `f3817196d142eaf72ce79dfebe53dcb20bd21da87ce13e138a8f8e10a866b3a4` | 2/3 passed | 143.44 tokens/s | unloaded |
| `qwen3.5:2b` | `324d162be6ca5629ae4517c8710434d0bd2d665bc94dbad46e9af8fbf8a2f0df` | 0/3 passed | 122.61 tokens/s | unloaded |
| `qwen3.5:4b` | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` | 3/3 passed | 93.94 tokens/s | unloaded |
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 3/3 passed | 75.57 tokens/s | unloaded |
| `gemma3:12b` | `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | 3/3 passed | 53.09 tokens/s | unloaded |
| `granite4:7b-a1b-h` | `566b725534ea0e9824f844abe6a78e1ab6f7357f1efb549be94908cb681513bb` | 2/3 passed | 129.75 tokens/s | unloaded |
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | `5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b` | 3/3 passed | 41.20 tokens/s | unloaded |
| `devstral-small-2:24b` | `24277f07f62db8f9cb68e9dfc679ea1818a7fbac47a50eff0a701d3f645b63c8` | 3/3 passed | 39.64 tokens/s | unloaded |

These exact-output constraint checks are diagnostic, not a quality ranking.
The two smaller Qwen variants and Granite remain valid user-selectable models,
but their misses grant no recommendation or promotion authority. Every case
used bounded generation and immediate unload; a final independent residency
check reported no loaded models.
