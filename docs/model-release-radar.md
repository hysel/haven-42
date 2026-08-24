# Model release radar

_Reviewed: 2026-08-21_

This page tracks newly released or previously missed local models worth
evaluating next. It is not a supported-model list. Nothing here changes Haven
42's automatic choice. Certification still requires the exact artifact,
runtime, hardware profile, task behavior, cleanup, and repeatability to pass.

The machine-readable record is `config/model-release-watch.json`. Unfiltered
discovery output stays in ignored local review storage because it contains many
official publisher updates unrelated to a local assistant.

The test design is in `config/model-release-evaluation-plan.json`. It assigns
each runnable candidate below to a task-specific lane and records the required
checks, fixtures, and failure outcomes. The file does not permit downloads,
execution, hardware changes, support-label changes, or promotion. A fresh owner
prompt is still required before a newly prepared soak starts.

## What the improved sweep found

| Candidate | Why it matters | Realistic first tier | Current gate |
| --- | --- | --- | --- |
| Qwen 3.8 27B | One model for chat, coding, reasoning, vision, and tools | 32 GiB accelerator or a future reviewed 24 GiB Q4/offload profile | No exact Ollama tag or reviewed GGUF yet |
| Gemma 4 E2B / E4B / 12B / 26B-A4B / 31B | A five-size Apache-2.0 family spanning chat, coding, reasoning, tools, vision, and selected audio variants | Official Q4 estimates range from 2.9 to 17.5 GB before Haven context/modality headroom | Pin one official QAT GGUF or full Ollama manifest and exact runtime per size |
| North Micro Vision 2.4B | Very compact general vision model | 8 GiB and above | Transformers 5.16.0 path needs native validation |
| LFM2.5-VL 3B | Official GGUF, compact multimodal/edge candidate | 4–12 GiB depending on exact quant | Select one file and finish LFM license review |
| Mage-VL 5B | Image/video understanding and bounded streaming-event research | 12 GiB and above | Custom code/codec review and a separately admitted video boundary |
| Nemotron Parse 2.0 | Compact document parsing, OCR, and layout extraction | 8 GiB and above | NVIDIA license and exact Transformers route review |
| Granite Vision 4.1 4B | Document, chart, and table extraction rather than generic chat | 12 GiB and above | Validate Transformers 5.8+ and vLLM 0.21+ routes |
| Shieldstral 1.0 3B | Policy-driven text and image safety classification | 16 GiB BF16; lower with a reviewed quant | Safety policy quality and exact llama.cpp artifact remain untested |
| Nemotron 3 Embed 1B / 8B | Retrieval and semantic search for future local history/library work | CPU/4 GiB for 1B; 16 GiB for 8B | OpenMDW license review and embedding quality suite |
| Qwen3-ASR 0.6B / 1.7B | Local speech recognition and language identification | CPU/low-memory through 8 GiB | Future audio boundary; Transformers 5.13+ |
| Nemotron 3.5 ASR Streaming 0.6B / VibeVoice ASR BitNet | Streaming and CPU-oriented long-form transcription alternatives | CPU and low-memory accelerators | Audio boundary, license/runtime pinning, and no implicit microphone access |
| Fara 1.5 4B / 9B / 27B | Scalable visual computer-use family | 12 GiB through workstation tiers | Needs a new sandboxed computer-use safety contract |
| GLM 4.1V 9B Thinking | Strong compact vision reasoning candidate | 24 GiB BF16; possibly lower with a reviewed quant | Consumer runtime artifact unresolved |
| Tiny Aya Global 3.35B | Compact chat coverage for 70+ languages | CPU/8 GiB and above | Gated non-commercial terms and multilingual quality review |
| Riva Translate 4B v2 | Sentence/document translation over 36 non-English languages | 12 GiB BF16 | Machine-readable license metadata and consumer quant unresolved |
| Llama Nemotron Embed VL 1B v2 | Image-text and document retrieval rather than text-only embeddings | CPU/4–8 GiB | NVIDIA license, preprocessing, and vector-contract review |
| Ornith 1.0 9B | Small coding/tool-use option already exposed by Ollama | 8 GiB and above | Full immutable Ollama manifest unresolved |
| North Mini Code 1.0 | 30B-A3B agentic coding model with a 19 GB Q4 | 24/32 GiB | Full manifest, minimum Ollama version, and tool suite |
| LFM2.5 8B-A1B | Small on-device chat and tool-calling model | 8 GiB and above | Full manifest and LFM license review |
| LFM2.5 1.2B Instruct and 2.6B GGUF | Compact assistant comparisons | CPU/4–8 GiB | Exact Q4_K_M files ran with full Metal offload on the M4, but both failed bounded core and OpenCode coding gates; LFM license review also remains open |

## Important releases that do not fit the current lab

- **Qwen 3.8 2.4T-A95B** has official public local weights, but its 2.4T
  total/95B active scale is outside the current memory envelope.
- **Kimi K3** is open-weight and multimodal, but its official repository is
  approximately 1.45 TiB. Ollama currently presents the model as cloud-only.
- **Laguna S 2.1** is an interesting 118B-A8B coding/reasoning model, but the
  smallest published route needs roughly 75–96 GB before context overhead.
  The current Ollama page also conflicts about the Q4 tag's size and
  quantization, so exact identity must be resolved before any plan advances.
- **DeepSeek V4 Flash 0731** is about 155 GiB upstream (and roughly 164 GiB in
  NVIDIA's NVFP4 DSpark conversion); **DeepSeek V4 Pro 0813** is about 831 GiB;
  **GLM-5** is about 1.40 TiB; and **Kimi K2.7 Code NVFP4** is about 554 GiB.
  Their local weights are real, but not realistic for the current single-node
  test tiers.
- **MiniMax Music3** is about 53 GiB, has no machine-readable license in the
  official repository metadata, and targets text-to-music, which Haven 42 does
  not currently support as an assistant capability.
- **Granite SWASH 3B-a600M** is a useful Apache-2.0 architecture preview, but it
  is a base model rather than an instruction-tuned novice-facing assistant.

These entries make an important distinction: “local weights exist” does not
mean “practical on the hardware we have.”

## Why Qwen 3.8 and Gemma 4 were initially missed

The old updater asked general and trending searches for known family names.
That is useful for community artifacts, but it had four blind spots:

1. A new official repository may not rank yet.
2. Search indexing can lag the publisher by hours or days.
3. A new family name is unknowable to a fixed seed-query list.
4. A manual `since` timestamp could accidentally narrow the configured rolling
   window. Gemma 4's official repository metadata predates the date on which it
   became relevant to this sweep, so that narrowing hid it.

The updater now polls reviewed publisher namespaces directly, sorts by
`lastModified`, and compares immutable revisions with prior output. Its 45-day
window is a minimum lookback: a manual timestamp may widen it but cannot narrow
it. A second source reads Ollama's newest-first registry index and resolves each
visible family detail page, so unfamiliar family names no longer depend on seed
queries. Seeded Ollama and general Hub search remain secondary discovery
signals. Official publisher weights establish release status, runtime
registries establish possible execution routes, and only Haven 42's local tests
establish support.

## Prepared evaluation order

1. Resolve one official Gemma 4 QAT GGUF per meaningful hardware tier, then
   resolve exact runtime artifacts for Qwen 3.8 27B, Ornith 9B, and North Mini
   Code. The two compact LFM2.5 GGUF routes now have bounded M4 failure evidence
   and should be revisited only with a specific runtime, prompting, or quality
   rationale.
2. Run license review before any LFM or OpenMDW artifact is downloaded.
3. Start with the compact, differentiated lanes: North Micro Vision, Nemotron
   Parse, Granite Vision, Shieldstral, Nemotron Embed 1B/VL 1B, Tiny Aya, and
   the smaller ASR candidates.
4. Use the existing fail-closed reliability scenarios for chat/coding models;
   add lane-specific quality fixtures for vision, safety, embedding, speech,
   and computer use.
5. Require a separate owner prompt before downloading or executing each newly
   prepared soak. Candidate research alone does not authorize a test.

Primary records include the official [Qwen 3.8 27B](https://huggingface.co/Qwen/Qwen3.8-27B),
[Gemma 4 documentation](https://ai.google.dev/gemma/docs/core),
[Gemma 4 E2B](https://huggingface.co/google/gemma-4-E2B-it),
[North Micro Vision](https://huggingface.co/CohereLabs/North-Micro-Vision-Instruct),
[Mage-VL](https://huggingface.co/microsoft/Mage-VL),
[Nemotron Parse 2.0](https://huggingface.co/nvidia/NVIDIA-Nemotron-Parse-2.0),
[Granite Vision 4.1](https://huggingface.co/ibm-granite/granite-vision-4.1-4b),
[Shieldstral 1.0](https://huggingface.co/mistralai/Shieldstral-1.0-3B),
[Nemotron 3 Embed](https://huggingface.co/nvidia/Nemotron-3-Embed-1B-BF16),
[Qwen3-ASR](https://huggingface.co/Qwen/Qwen3-ASR-0.6B-hf), and
[Fara 1.5](https://huggingface.co/microsoft/Fara1.5-4B),
[Tiny Aya](https://huggingface.co/CohereLabs/tiny-aya-global), and
[Riva Translate v2](https://huggingface.co/nvidia/Riva-Translate-4B-Instruct-v2)
repositories. Ollama
runtime candidates are recorded from [Ornith](https://ollama.com/library/ornith),
[North Mini Code](https://ollama.com/library/north-mini-code-1.0), and
[LFM2.5](https://ollama.com/library/lfm2.5),
[LFM2.5 1.2B Instruct GGUF](https://huggingface.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF), and
[LFM2.5 2.6B GGUF](https://huggingface.co/LiquidAI/LFM2.5-2.6B-GGUF).
