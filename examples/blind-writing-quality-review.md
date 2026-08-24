# Blind Writing Quality Reviews

## First packet

### Scope

One human reviewer ranked four anonymized exact Ollama artifacts across three
synthetic writing scenarios on 2026-07-25. Candidate labels were randomized
independently for each scenario. The reviewer completed every rank before the
local answer key was opened. The endpoint, raw model output, local paths, and
answer key are intentionally excluded from committed evidence.

This is one reviewer's bounded preference result, not a statistically stable
comparison. It does not replace automated constraint checks, additional
reviewers, accessibility review, license decisions, or exact-platform results.

### Exact artifacts

| Candidate | Ollama digest |
| --- | --- |
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` |
| `gemma3:12b` | `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` |
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | `5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b` |
| `granite4:7b-a1b-h` | `566b725534ea0e9824f844abe6a78e1ab6f7357f1efb549be94908cb681513bb` |

The provider was Ollama `0.32.1` on a user-controlled trusted-LAN host.
Generation used `think:false`, temperature `0.2`, seed `42`, and a 700-token
bound. Every per-sample unload passed, and the final independent `/api/ps`
audit reported zero loaded models.

### Rankings

Four points were assigned to first place, three to second, two to third, and
one to fourth.

| Scenario | First | Second | Third | Fourth |
| --- | --- | --- | --- | --- |
| Professional scheduling email | Qwen | Granite | Gemma | Mistral |
| Fact-preserving executive rewrite | Gemma | Qwen | Mistral | Granite |
| Source-grounded public brief | Granite | Mistral | Qwen | Gemma |

| Candidate | Points | Average rank | First-place results |
| --- | ---: | ---: | ---: |
| Qwen | 9 | 2.00 | 1 |
| Granite | 8 | 2.33 | 1 |
| Gemma | 7 | 2.67 | 1 |
| Mistral | 6 | 3.00 | 0 |

### Decision

No comparative writing-quality promotion is justified. Qwen keeps the existing
bounded adapter baseline and narrowly leads this one-reviewer sample, but Qwen,
Granite, and Gemma each won one scenario. Granite also failed the separate
automated structured-brief constraint in all three repeated samples, so its
first-place human preference does not override that fidelity failure.

Before changing a default, repeat the blind packet with independent reviewers
and broader scenarios, collect criterion-level scores, reconcile preferences
with automated constraint failures, and validate the exact artifact and
platform again. The reusable local-only harness is
`scripts/run-blind-writing-review.py`.

## Second packet

### Scope

The same reviewer completed a second independently randomized packet on
2026-07-27. It added long-form continuity, distractor-resistant summarization,
and constrained fact-preserving editing. The reviewer supplied a forced
best-to-worst rank for every scenario before opening the local answer key and
did not assign criterion-level numeric scores.

The packet used the same four exact model artifacts and generation settings as
the first review, with Ollama `0.32.4`. Every per-sample unload passed, and the
final independent provider audit reported zero loaded models. The endpoint,
raw responses, local paths, and randomized answer key remain intentionally
excluded from committed evidence.

### Rankings

| Scenario | First | Second | Third | Fourth |
| --- | --- | --- | --- | --- |
| Long-form continuity and section coherence | Mistral | Granite | Qwen | Gemma |
| Distractor-resistant source summary | Granite | Qwen | Gemma | Mistral |
| Constrained fact-preserving edit | Gemma | Mistral | Granite | Qwen |

| Candidate | Points | Average rank | First-place results |
| --- | ---: | ---: | ---: |
| Granite | 9 | 2.00 | 1 |
| Mistral | 8 | 2.33 | 1 |
| Gemma | 7 | 2.67 | 1 |
| Qwen | 6 | 3.00 | 0 |

### Combined interpretation

Across the six scenarios, Granite received 17 preference points, Qwen 15, and
Gemma and Mistral 14 each. Granite and Gemma each won two scenarios; Qwen and
Mistral each won one. These totals are descriptive only: both packets used the
same reviewer, the provider versions differed, and the second packet did not
collect criterion-level scores.

No comparative writing-quality promotion is justified. Granite's preference
lead does not override its repeatable failure in the separate automated
constraint matrix. Qwen remains the exact bounded adapter baseline, not a
best-writer claim. A default change still requires independent reviewers,
criterion-level scoring, repeated exact-platform evidence, license review, and
agreement between subjective quality and deterministic instruction fidelity.
