# Blind Writing Quality Review

## Scope

One human reviewer ranked four anonymized exact Ollama artifacts across three
synthetic writing scenarios on 2026-07-25. Candidate labels were randomized
independently for each scenario. The reviewer completed every rank before the
local answer key was opened. The endpoint, raw model output, local paths, and
answer key are intentionally excluded from committed evidence.

This is bounded preference evidence, not a statistically stable comparative
promotion. It does not replace automated constraint checks, broader reviewers,
accessibility review, license decisions, or exact-platform evidence.

## Exact artifacts

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

## Rankings

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

## Decision

No comparative writing-quality promotion is justified. Qwen retains the
existing bounded adapter baseline and narrowly leads this one-reviewer sample,
but Qwen, Granite, and Gemma each won one scenario. Granite also failed the
separate repeated automated structured-brief constraint in all three samples,
so its first-place human preference does not override deterministic fidelity
evidence.

Before changing a default, repeat the blind packet with additional independent
reviewers and broader scenarios, collect criterion-level scores, reconcile
preference with automated constraint failures, and repeat exact artifact and
platform validation. The reusable local-only harness is
`scripts/run-blind-writing-review.py`.
