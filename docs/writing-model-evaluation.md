# Writing Model Evaluation

Haven 42 has validated the bounded `content.write` adapter with the recorded `qwen3.5:9b` Ollama digest, run an exact-digest constraint matrix across all four candidates, and completed two blind packets with one reviewer. Comparative writing-quality evaluation is not complete. Adapter checks, marker checks, and one reviewer's preferences do not establish the best writing model or justify changing an automatic default.

No candidate under comparative evaluation in this document is a product default or writing-quality recommendation. The local web app may select `qwen3.5:9b` automatically only when the installed name and digest match the validated writing-adapter baseline. That means the adapter passed, not that Qwen produces the best prose. Replacing it requires results for the exact model artifact, quantization, provider version, operating system, host hardware, and license, plus repeated performance measurements and blind human review.

## Initial Candidate Matrix

| Candidate | Why evaluate it | Initial hardware note | License boundary | Current Haven 42 state |
| --- | --- | --- | --- | --- |
| `qwen3.5:9b` | Existing control with passed chat, writing-adapter, summarization, and cleanup checks. | Already exercised on the current Ollama path. | Reconfirm the exact Ollama artifact and upstream license at evaluation time. | Validated adapter baseline; comparative writing quality unknown. |
| `gemma3:12b` instruction-tuned Q4 | Google identifies Gemma 3 for content creation, chat, summarization, and instruction following; the Ollama 12B package is about 8.1 GB with a 128K context window. | Plausible 16 GB-class candidate with headroom; measure the actual execution host. | Gemma Terms of Use and Prohibited Use Policy require an explicit product-license review; do not label it Apache or OSI-approved. | Candidate only. |
| `mistral-small3.2:24b-instruct-2506-q4_K_M` | Mistral reports improved precise instruction following and fewer repetition errors; the Ollama artifact is Apache 2.0 and has a 128K context window. | About 15 GB before runtime overhead, so a 16 GB GPU may spill or lose useful context headroom. | Apache 2.0 for the reviewed artifact; verify the exact digest. | Candidate only; newer Mistral generations do not transfer evidence to this artifact. |
| `granite4:7b-a1b-h` | IBM lists summarization, instruction following, question answering, and multilingual dialog as intended uses; the Ollama package is about 4.2 GB. | Efficiency baseline for lower-memory systems; verify hybrid Mamba-2 runtime behavior and output quality. | Apache 2.0 for the reviewed family/artifact; verify the exact digest. | Candidate only. |

Gemma 3 27B and Mistral Small 4 may be reconsidered for larger hardware. They are not in the first 16 GB-class matrix: the Ollama Gemma 3 27B package is about 17 GB before runtime overhead, while Mistral Small 4 has 119B total parameters despite 6.5B active parameters.

Official sources:

- Google Gemma 3 model card: <https://ai.google.dev/gemma/docs/core/model_card_3>
- Ollama Gemma 3 artifacts: <https://ollama.com/library/gemma3>
- Mistral Small 3.2 model card: <https://docs.mistral.ai/models/model-cards/mistral-small-3-2-25-06>
- Ollama Mistral Small 3.2 artifact: <https://ollama.com/library/mistral-small3.2>
- Ollama Granite 4 artifacts and IBM references: <https://ollama.com/library/granite4>

## Controlled Evaluation

The first automated run completed on 2026-07-24 with Ollama `0.32.1`. Qwen,
Gemma, and Mistral passed all three synthetic constraint-retention cases. Granite
passed two and omitted one required uncertainty phrase. Every per-case and final
unload check passed, raw output was not saved, and `/api/ps` was empty afterward.
Exact digests and sanitized metrics are in
`examples/writing-model-matrix-validation.md`. The reusable harness runs one to
five bounded repetitions per exact artifact, unloads after each sample, and keeps
only marker results, hashes, lengths, and provider metrics. Broader sampling and
human quality review remain open, so the comparative default did not change.

The first blind packet is recorded in `examples/blind-writing-quality-review.md`.
One reviewer ranked three independently randomized synthetic scenarios. Qwen led
with nine points, followed by Granite with eight, Gemma with seven, and Mistral
with six. Qwen, Granite, and Gemma each won one scenario. This result leaves the
Qwen adapter baseline in place but does not establish a writing-quality winner.
The evaluation still needs independent reviewers, broader scenarios, and
criterion-level scores.

The same reviewer completed a second randomized packet covering long-form
continuity, distractor resistance, and exact fact-preserving editing. Granite led
with nine points, followed by Mistral with eight, Gemma with seven, and Qwen with
six. Granite, Mistral, and Gemma each won one scenario. Across both packets,
Granite has 17 preference points, Qwen 15, and Gemma and Mistral 14 each. These
remain descriptive results from one reviewer. The second packet used Ollama
`0.32.4` instead of `0.32.1` and collected forced ranks without criterion-level
numeric scores. Granite's preference result does not override its repeated
automated constraint failure, so the comparative default did not change.

Use the same source material, prompts, provider settings, context limit, warm/cold policy, and output bounds for every exact candidate. Record the prompt-set revision and never use private user documents in committed fixtures.

The first suite should cover:

1. concise professional email drafting;
2. tone-preserving rewrite;
3. structured article or brief from supplied facts;
4. long-form coherence and section continuity;
5. source-grounded summarization with deliberate distractors;
6. constrained editing that must retain names, dates, numbers, and uncertainty;
7. multilingual writing only for languages represented in the claimed model support.

Blind human scoring should cover instruction compliance, factual retention, completeness, organization, tone, repetition, unsupported additions, and formatting. Automated checks should verify required facts, forbidden inventions, required headings, output bounds, and repeatability, but cannot replace human review of writing quality.

Also record time to first token, generation throughput, total latency, accelerator and system memory, context actually admitted by the provider, warm-reuse behavior, idle cleanup, and final unloaded state. Run enough repetitions to distinguish a stable result from one favorable sample.

## Promotion Rules

- Rank models independently for Chat, Writing, and Summarization.
- Never inherit writing evidence from coding, tool-use, or generic chat tests.
- Never inherit evidence across a different artifact digest, quantization, provider, operating system, or execution-host hardware profile.
- A missing recommended model may be named with explicit installation guidance; Haven 42 must not download it automatically.
- An installed unknown model remains `unverified`. It may be user-selected for bounded text generation, but it cannot become the automatic default or gain tools, filesystem access, repository writes, or external network authority.
- Promote a default only after its license review and exact tests pass. If no installed model qualifies, show `No validated model installed` instead of silently selecting the first provider result.
