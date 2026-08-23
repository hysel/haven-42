# Model and Hardware Test Status

_Last reviewed: August 22, 2026._

Use this page to answer three practical questions:

1. Did this exact model complete the required workload?
2. Did it use the intended accelerator instead of quietly falling back to the CPU?
3. Did it remain stable long enough to support a recommendation?

The short version: **a model name alone does not prove support.**
The operating system, GPU, driver, AI engine, engine version, quantization,
available memory, and task all matter. A pass on one stack is evidence for that
stack only.

If you do not want to read the matrix, use **Choose for me · Recommended**.
Haven 42 makes an automatic choice only when the detected machine matches a
qualified profile. You can still select other models manually; Haven 42 labels
what it knows instead of pretending an untested combination is safe.

## Read this first

### Evidence labels

- **✅ Verified** — the required end-user checks passed on the exact listed stack.
- **🧪 Engineering evidence** — controlled task and reliability tests passed,
  but at least one packaged-product or lifecycle gate remains.
- **⚠️ Partial** — useful checks passed, but another required check failed or is
  incomplete.
- **❌ Did not pass** — a required gate failed on the listed stack.
- **⬜ Not tested** — there is no result for that exact combination.

These are evidence labels, not model rankings. They do not silently change the
default model, runtime policy, or support promise.

### What counts as a different result

Each of these changes creates a separate result:

- Windows, Linux, and macOS;
- NVIDIA CUDA, AMD Vulkan, Intel SYCL, or Apple Metal;
- Ollama and llama.cpp;
- a different runtime or driver version;
- a different model tag, quantization, or artifact digest;
- Chat, Writing, Summarization, Coding, Vision, or tool use;
- a different memory tier or GPU architecture.

For example, `Qwen 3.5 9B Q4_K_M` passing through Ollama on a Radeon RX 6800
does not prove the same model through llama.cpp, and it does not prove support
on every 16 GB GPU.

## Automatic selection: current qualified profiles

Automatic selection is deliberately cautious. Haven 42 checks the machine,
runtime, exact model artifact, available memory, and requested task before using
one of these choices.

| Tested computer and software combination | Automatic model | Why this model |
| --- | --- | --- |
| Tested Alpha 2 Linux computers running in CPU-only mode | Qwen 3.5 0.8B Q8 | Responsive low-risk fallback for Chat, Writing, and Summarization |
| Ubuntu 26.04 or Bazzite 44 with a Quadro RTX 5000 and 16 GB of graphics memory | Qwen 3.5 4B Q4_K_M | Balanced quality, speed, and memory headroom |
| The same Quadro RTX 5000 computers when the 4B model does not fit safely | Qwen 3.5 2B Q8 or 0.8B Q8 | Lower-memory fallback |
| The tested Windows 11 computer with NVIDIA graphics | Qwen 3.5 0.8B Q8 | Conservative Windows fallback |

Everything else below is either engineering evidence, partial evidence, or a
recorded failure. A nearby configuration is not automatically equivalent.

## Model matrix

The tables start with the model so you can see where it actually worked.
“Passed on” means the named profile has recorded task and reliability evidence;
it does not mean every route on that hardware is supported.

### Small and mid-size models

| Exact model | Passed on | Limits or failures | Status |
| --- | --- | --- | --- |
| Qwen 3.5 0.8B Q8 | CPU-only Alpha 2 Linux computers; Quadro RTX 5000 on Ubuntu 26.04 and Bazzite 44; GTX 1650 Super on Windows 11 and Ubuntu 26.04 | Used automatically only on the tested combinations that Haven 42 recognizes | ✅ Qualified fallback |
| Qwen 3.5 2B Q8 | Quadro RTX 5000 on Ubuntu 26.04 and Bazzite 44, plus the high-memory NVIDIA test servers | Did not fit completely in the GTX 1650 Super's 4 GB of graphics memory | ✅ Qualified on the named Quadro computers |
| Qwen 3.5 4B Q4_K_M | Quadro RTX 5000 on Ubuntu 26.04 and Bazzite 44; Radeon RX 5700 XT on Ubuntu 26.04; high-memory NVIDIA test servers | Too large to remain completely in the GTX 1650 Super's 4 GB of graphics memory | ✅ Qualified on the named Quadro computers; 🧪 engineering evidence elsewhere |
| Qwen 3.5 9B Q4_K_M | Radeon RX 6800 on Ubuntu 26.04; Radeon RX 7800 XT on Windows 11; high-memory NVIDIA test servers | Haven 42 does not yet choose it automatically on AMD graphics | 🧪 Candidate for tested 16 GB graphics cards |
| Gemma 3 1B Q4_K_M | GTX 1650 Super on Windows 11 and Ubuntu 26.04 | Failed the required Summarization check on the RX 6800 Ubuntu computer | 🧪 Useful only on the named tested computers |
| Gemma 3 4B Q4_K_M | Radeon RX 5700 XT and RX 6800 on Ubuntu 26.04; other separately recorded higher-memory computers | More human comparison of answer quality is still needed | 🧪 Repeated task-and-soak pass |
| Gemma 3 12B Q4_K_M | Radeon RX 6800 on Ubuntu 26.04 and separately recorded higher-memory computers | Has not qualified on lower-memory graphics cards | 🧪 Candidate for tested 16 GB graphics cards |
| Gemma 4 E2B QAT | Radeon RX 5700 XT and RX 6800 on Ubuntu 26.04; Apple M4 on macOS 26.6.2 | Installation, update, recovery, and packaged-app checks remain | 🧪 Small-model candidate |
| Gemma 4 E4B QAT | Radeon RX 5700 XT and RX 6800 on Ubuntu 26.04; Apple M4 on macOS 26.6.2 | Installation, update, recovery, and packaged-app checks remain | 🧪 Mid-size candidate |
| Gemma 4 12B QAT | Radeon RX 6800 on Ubuntu 26.04; Apple M4 on macOS 26.6.2; separately recorded higher-memory computers | Haven 42 does not yet choose it automatically on AMD or Apple hardware | 🧪 Candidate for tested 16 GB computers |
| Granite 4.1 3B Q4_K_M | GTX 1650 Super, RX 5700 XT, and RX 6800 on Ubuntu 26.04; Apple M4 on macOS 26.6.2 | The Windows result on a 4 GB graphics card remains a separate, failed memory-fit result | 🧪 Small-model candidate on several tested computers |
| Granite 4.1 8B Q4_K_M | RX 5700 XT and RX 6800 on Ubuntu 26.04; RTX 3060 on Windows 11 and Ubuntu 26.04; Intel Arc B580 on Ubuntu; Apple M4 on macOS 26.6.2 | The Intel result applies only to the tested llama.cpp SYCL software path | 🧪 Candidate with results on AMD, NVIDIA, Intel, and Apple hardware |
| Llama 3.2 3B Q4_K_M | GTX 1650 Super, RX 5700 XT, and RX 6800 on Ubuntu 26.04; other separately recorded higher-memory computers | Failed Summarization on the Apple M4 and has no broadly approved default | 🧪 Small-model candidate on the named computers |
| Phi-4 Mini 3.8B Q4_K_M | RX 5700 XT and RX 6800 on Ubuntu 26.04; separately recorded higher-memory computers | Did not fit completely in the GTX 1650 Super's 4 GB of graphics memory and failed the structured-tool check on Apple M4 | 🧪 Mid-size candidate on the named computers |
| Ministral 3 3B Q4_K_M | Apple M4 on macOS 26.6.2 and separately recorded Linux/NVIDIA computers | Failed required task checks on RX 6800 Ubuntu, RX 7800 XT Windows, and other recorded combinations | ❌ No broad recommendation |
| Ministral 3 8B Q4_K_M | Apple M4 on macOS 26.6.2 and separately recorded Linux/NVIDIA computers | Failed required task checks on RX 6800 Ubuntu, RX 7800 XT Windows, and other recorded combinations | ❌ No broad recommendation |
| MiniCPM V 4.6 1B Q4_K_M | GTX 1650 Super Windows/Ubuntu | Failed tested RX 5700 XT core and Vision contracts | ⚠️ Narrow 4 GB evidence only |

### Large and specialized models

| Exact model | Test profile | Result | Status |
| --- | --- | --- | --- |
| Qwen 3.6 27B Q4_K_M | Dual Tesla V100 Ubuntu | Core tasks and 30-minute soak passed | 🧪 High-memory candidate |
| Qwen 3.6 35B-A3B Q4_K_M | Dual Tesla V100 Ubuntu | Core tasks and 30-minute soak passed | 🧪 High-memory candidate |
| Qwen 3.8 27B Q4_K_M | Dual Tesla V100 Ubuntu | Core tasks and soak passed; separate Vision gate failed; native VS Code evidence is read-only | ⚠️ Partial; not a Coding recommendation |
| Granite 4.1 30B Q4_K_M | Dual Tesla V100 Ubuntu | Core, soak, tools, and recovery passed; the separate coding-surface approved-write gate failed | ⚠️ Not a Coding recommendation |
| Ornith 1.0 9B Q4_K_M | RX 5700 XT Ubuntu | Core, soak, tools, and recovery passed; the separate coding-surface repository-review gate failed | ⚠️ Not a Coding recommendation |
| North Mini Code 1.0 30B-A3B Q4_K_M | Dual Tesla V100 Ubuntu | Core and soak passed; an earlier Coding JSON contract failed; later Continue evidence does not qualify a maintained surface | ⚠️ Not a Coding recommendation |
| Nemotron 3.5 Lightning 30B-A3B Q4_K_M and Q8_0 | Dual Tesla V100 Ubuntu | Both passed core tasks and 30-minute soaks | 🧪 Additional capability work remains |
| Muse Glimmer 30B Q4_K_M | Dual Tesla V100 Ubuntu | Chat passed; Writing and Summarization failed; soak correctly did not run | ❌ Required gates failed |
| LFM 2.5 8B-A1B Q4_K_M | RX 5700 XT Ubuntu | Required task and Coding gates failed | ❌ No recommendation |

Exact artifact IDs, runtime versions, test records, and failure codes are linked
from the [[Engineering and Validation Index|Engineering-Index]].

### Apple M4 16 GB model results

The native macOS 26.6.2 campaign used signed and notarized Ollama 0.32.15 with
Metal. The original frozen campaign checked sixteen exact artifacts; an
independently approved addendum applied the same contract to Gemma 4 12B QAT.

| Exact model | Core gate | Independent 30-minute soak | Coding surface |
| --- | --- | --- | --- |
| Qwen 3.5 2B Q8 | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Qwen 3.5 4B Q4 | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Gemma 4 E2B QAT | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Gemma 4 E4B QAT | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Gemma 4 12B QAT addendum | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Granite 4.1 3B Q4 | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Granite 4.1 8B Q4 | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Ministral 3 3B Q4 | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Ministral 3 8B Q4 | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Ornith 9B | Passed | Passed | OpenCode 1.18.19 did not pass every required gate |
| Qwen 3.5 0.8B Q8 | Failed Summarization | Not run | No recommendation |
| Gemma 3 1B Q4 | Failed Summarization, structured tool, and structured code | Not run | No recommendation |
| Gemma 3 4B Q4 | Failed Summarization and structured tool | Not run | No recommendation |
| Phi-4 Mini 3.8B Q4 | Failed structured tool | Not run | No recommendation |
| Llama 3.2 3B Q4 | Failed Summarization | Not run | No recommendation |
| LFM 2.5 8B | Failed Chat, Writing, and Summarization; license review remains open | Not run | No recommendation |
| MiniCPM V 4.6 1B | Failed structured code | Not run | No recommendation |

Two separate LFM2.5 GGUF candidates—1.2B Instruct Q4_K_M and 2.6B Q4_K_M—
proved full Metal offload through pinned llama.cpp `b10520`, but each failed
required core gates and timed out in the read-only OpenCode screen without
changing files. Neither entered soak or earned a recommendation.

## Find results for a specific graphics card

This page is organized by model. For card-by-card results, open
[[Hardware Compatibility|Tested-Hardware-And-AI-Engines]]. Its **Detailed
card-by-card records** section links to the full NVIDIA, AMD, Intel, and Apple
test reports. Those engineering records contain the exact versions, speeds,
failures, test duration, and measurement limits without making this summary
page favor whichever card was tested most recently.

## Hardware coverage at a glance

| Hardware class | Recorded result | Practical interpretation |
| --- | --- | --- |
| NVIDIA 4 GB | Small Qwen, Gemma, Granite, Llama, and MiniCPM candidates passed on specific GTX 1650 Super Windows or Ubuntu routes | Useful small-model tier; not blanket 4 GB support |
| AMD 8 GB | Nine profiles passed the RX 5700 XT Ubuntu task and acceleration gates | Vulkan engineering route; no automatic AMD default |
| NVIDIA 12 GB | 14 profiles passed on RTX 3060 Windows; all 19 tested profiles passed on RTX 3060 Ubuntu | Strong coverage, with Windows and Linux kept separate |
| Intel 12 GB | Granite 4.1 8B Q4 passed the exact Arc B580 Ubuntu SYCL route | Narrow Intel evidence cell |
| NVIDIA 16 GB | Qwen 3.5 4B Q4_K_M is qualified on exact Ubuntu 26.04 and Bazzite 44 profiles | Most complete current 16 GB end-user route |
| AMD 16 GB | 10 of 13 candidates passed the RX 6800 Ubuntu route; 14 of 17 passed a separate RX 7800 XT Windows route | Broad RDNA 2/RDNA 3 engineering evidence |
| Apple M4, 16 GB unified | Ten of seventeen exact Ollama artifacts passed required core gates and independent Metal soaks; two LFM2.5 llama.cpp candidates proved full offload but failed core and coding gates | Broad exact-profile engineering evidence; no automatic Apple default or coding recommendation |
| NVIDIA 32 GB+ | Large Qwen, Granite, and Nemotron candidates passed controlled V100 campaigns | High-memory results; not consumer-card equivalence |

See [[Hardware Compatibility|Tested-Hardware-And-AI-Engines]] for exact OS,
driver, engine, and accelerator combinations.

## How qualification works

A model is not eligible for automatic selection merely because it loads or
answers one prompt. The qualification path checks:

1. **Artifact identity** — exact tag, quantization, and digest.
2. **Runtime support** — supported engine and version.
3. **Memory fit** — enough usable system or graphics memory with headroom.
4. **Accelerator use** — the intended GPU or Apple accelerator is actually used.
5. **Task gates** — deterministic requirements for each claimed task.
6. **Reliability** — repeated runs, timeout recovery, cleanup, and unload.
7. **Soak** — sustained execution only after the required task gates pass.
8. **Product lifecycle** — install, update, rollback, reconnect, and packaged UI.

Coding qualification is separate. A model must pass repository read, planning,
review, scoped-write, filename fidelity, tool-call, timeout-recovery, and
unintended-write checks in a maintained coding surface before Haven 42 calls it
a Coding recommendation.

## Common interpretation mistakes

### “It appears in Ollama, so it is supported”

No. Ollama inventory proves that an artifact is present. It does not prove task
quality, GPU acceleration, memory safety, or long-run stability.

### “It has the same amount of VRAM, so the result transfers”

No. GPU architecture, backend, driver, memory behavior, and operating system can
change the result. Memory size is a fit signal, not certification.

### “The largest model that starts must be the best choice”

No. A smaller model may be faster, more reliable, and better at the requested
task. Haven 42 prioritizes required-task reliability before model size.

### “An Ollama pass proves llama.cpp”

No. They are separate execution routes with separate versions, model artifacts,
and backend behavior.

## Power and electricity evidence

Power depends on the model, task, runtime, driver, and complete system. See
[[Power Use and Electricity Costs|Model-Power-And-Electricity-Evidence]] for
measured examples and the cost formula. A row reports board or SoC power unless
it explicitly says wall power.

## Detailed evidence

- [[Hardware Compatibility|Tested-Hardware-And-AI-Engines]] — exact tested
  hardware, operating systems, drivers, and AI engines.
- [[Power Use and Electricity Costs|Model-Power-And-Electricity-Evidence]] —
  measured power evidence and its limitations.
- [[Engineering and Validation Index|Engineering-Index]] — complete matrices,
  methods, failure records, and machine-readable artifacts.

To request another model, use the
[model test request](https://github.com/hysel/haven-42/issues/new?template=model-test-request.yml)
or email `haven42localai@gmail.com`. Include the exact model and intended task
if you know them. Never include API keys, passwords, private addresses, prompts,
or private files.
