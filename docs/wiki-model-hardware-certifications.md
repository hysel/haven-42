# Model Compatibility

_Last reviewed: August 21, 2026._

This page helps you understand which local models Haven 42 can choose safely.
A result applies only to the listed model, AI engine, operating system, and
hardware. A model that works on one graphics card may fail, run slowly, or use
the CPU on another.

You do not need to study this page before using Haven 42. Start with **Choose
for me · Recommended**. Haven 42 checks your computer and offers only an
automatic choice backed by matching results. Other installed models remain
available as clearly labeled manual choices.

## What the labels mean

- **✅ Verified** — the required checks passed on that exact setup.
- **🧪 Engineering evidence** — useful controlled tests passed, but the complete end-user
  route has not been verified.
- **⚠️ Partial** — some checks passed and another required check is incomplete
  or failed.
- **❌ Did not pass** — a required check failed.
- **⬜ Not tested** — no result is available for that combination.

These labels describe test results, not the size or general quality of a
model.

## Automatic choices available today

Automatic selection is intentionally narrow. Haven 42 matches the operating
system, AI engine, runtime version, available memory, model checksum, and task
before using one of these choices.

| Computer | Automatic choice | Intended use |
| --- | --- | --- |
| Exact CPU-tested Alpha 2 Linux profiles | Qwen 3.5 0.8B Q8 | Responsive chat, writing, and summarization fallback |
| Exact Ubuntu 26.04 or Bazzite 44 NVIDIA profile with 16 GB usable graphics memory | Qwen 3.5 4B Q4 | Balanced chat, writing, and summarization |
| Same 16 GB NVIDIA profiles when the larger choice does not fit | Qwen 3.5 2B Q8 or 0.8B Q8 | Lower-memory fallback |
| Exact tested Windows NVIDIA baseline | Qwen 3.5 0.8B Q8 | Conservative Windows fallback |

A nearby but untested configuration is not treated as equivalent. Other
successful tests below are candidates, not automatic choices.

## Useful results by hardware class

| Hardware class | What has worked | What the result means |
| --- | --- | --- |
| NVIDIA, 4 GB | Qwen 3.5 0.8B Q8, Gemma 3 1B Q4, and MiniCPM V 4.6 1B Q4 passed on both tested Windows and Ubuntu GTX 1650 Super setups. Granite 4.1 3B Q4 and Llama 3.2 3B Q4 also passed on the tested Ubuntu setup. | Small-model choices for those exact setups; not blanket 4 GB support. |
| AMD, 8 GB | Nine profiles passed the Ubuntu RX 5700 XT task and acceleration checks. | Tested Vulkan route; no automatic recommendation yet. |
| NVIDIA, 12 GB | Fourteen profiles passed on the tested Windows RTX 3060; all 19 tested profiles passed on the tested Ubuntu RTX 3060. | Strong candidate coverage, kept separate by operating system. |
| Intel, 12 GB | Granite 4.1 8B Q4 passed the tested Ubuntu Arc B580 SYCL route. | Narrow tested candidate; no broad Intel default. |
| NVIDIA, 16 GB | Qwen 3.5 4B Q4 is the approved balanced choice on the exact Ubuntu 26.04 and Bazzite 44 profiles. Several larger candidates also passed controlled tests. | The broadest completed end-user recommendation among current 16 GB profiles. |
| AMD, 16 GB | Fourteen profiles passed the tested Windows RX 7800 XT task and soak route. | Broad candidate set; comparative quality and complete lifecycle checks remain separate. |
| Apple M4, 16 GB unified memory | Ten of seventeen exact Ollama artifacts passed the task gates and their own 30-minute Metal soaks, including the separately approved Gemma 4 12B QAT addendum. | Apple Silicon engineering results; no automatic Apple default yet. |
| NVIDIA, 32 GB or more | Large Qwen and Nemotron candidates passed controlled single- or dual-V100 tests. | High-memory engineering results, not consumer-card equivalence. |

For the exact operating systems, engines, versions, and limitations, open
[[Hardware Compatibility|Tested-Hardware-And-AI-Engines]].

## How Haven 42 chooses

Haven 42 first removes choices that do not match the installed AI engine,
runtime version, model checksum, task, or available memory. It also checks that
the intended accelerator was actually used instead of silently falling back to
the CPU.

Among the remaining choices, reliability comes before model size. Task quality,
response speed, memory headroom, and energy use can then distinguish otherwise
suitable models. The largest model that starts is not automatically the best
model for everyday use.

Ollama and llama.cpp are separate routes. A passing Ollama result does not
prove the same model on llama.cpp, and Haven 42 does not silently switch engines
or graphics backends.

## Why some installed models are labeled untested

Ollama may list models that Haven 42 has not tested for your exact task and
computer. They remain available for manual selection because the model belongs
to you. The label is a warning, not a block.

A model becomes eligible for automatic selection only after its exact files,
runtime, task behavior, reliability, memory fit, accelerator use, and cleanup
have passed on a matching setup. A single successful prompt is not enough.

## Power and electricity

Power use changes with the model, task, runtime, driver, and computer. See
[[Power Use and Electricity Costs|Model-Power-And-Electricity-Evidence]] for
measured examples and a simple cost formula. Those readings describe graphics
board or Apple SoC power unless the row explicitly says wall power.

## More detail

- [[Hardware Compatibility|Tested-Hardware-And-AI-Engines]] lists exact tested
  operating-system, graphics, and AI-engine combinations.
- [[Power Use and Electricity Costs|Model-Power-And-Electricity-Evidence]]
  explains measured energy use.
- [[Engineering and Validation Index|Engineering-Index]] links to complete
  model matrices, failures, test methods, and machine-readable evidence.

To request a model test, use the
[model request form](https://github.com/hysel/haven-42/issues/new?template=model-test-request.yml)
or email `haven42localai@gmail.com`. Include the model name and intended use if
you know them. Do not include keys, passwords, private addresses, prompts, or
files.
