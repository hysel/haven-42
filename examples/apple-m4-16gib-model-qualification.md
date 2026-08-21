# Apple M4 16 GB model qualification

On August 20, 2026, Haven 42 ran a bounded engineering qualification on a
physical Apple M4 Mac with 16 GB of unified memory. The test used the exact
signed and notarized Ollama 0.32.15 macOS artifact over IPv4 loopback and
checked 16 exact model manifests with Metal acceleration.

This is exact-profile engineering evidence. It does not certify every M4 Mac,
another memory capacity, another macOS or runtime version, a packaged Haven 42
release, or any coding editor. It does not change an automatic model default,
support label, runtime admission decision, or release policy.

## What the bounded gate checked

Every candidate received five deterministic checks:

- a short general-chat answer;
- a constrained one-sentence writing task;
- a one-sentence summary containing the required facts;
- one exact structured file-read tool call; and
- exact-path JSON code that compiled and ran.

Each cell also had to report full Metal residency and unload successfully.
The public result retains durations and aggregate token rates, but no raw
prompt or response text and no private machine identity.

## Results

| Exact candidate | Result | Average output rate | Failed bounded gate |
| --- | --- | ---: | --- |
| Qwen 3.5 0.8B Q8 | Failed | 93.360 tokens/s | Summarization |
| Qwen 3.5 2B Q8 | Passed | 45.647 tokens/s | — |
| Qwen 3.5 4B Q4 | Passed | 33.003 tokens/s | — |
| Gemma 3 1B Q4 | Failed | 110.152 tokens/s | Summarization, structured tool, structured code |
| Gemma 3 4B Q4 | Failed | 40.269 tokens/s | Summarization, structured tool |
| Gemma 4 E2B QAT | Passed | 63.444 tokens/s | — |
| Gemma 4 E4B QAT | Passed | 34.494 tokens/s | — |
| Granite 4.1 3B Q4 | Passed | 46.750 tokens/s | — |
| Granite 4.1 8B Q4 | Passed | 21.071 tokens/s | — |
| Phi-4 Mini 3.8B Q4 | Failed | 42.066 tokens/s | Structured tool |
| Llama 3.2 3B Q4 | Failed | 51.585 tokens/s | Summarization |
| Ministral 3 3B Q4 | Passed | 45.451 tokens/s | — |
| Ministral 3 8B Q4 | Passed | 21.628 tokens/s | — |
| Ornith 9B | Passed | 19.466 tokens/s | — |
| LFM 2.5 8B | Failed | 82.377 tokens/s | Chat, writing, summarization; license review also remains open |
| MiniCPM V 4.6 1B | Failed | 123.652 tokens/s | Structured code |

A failure here means the exact response missed this strict test contract. It
does not mean that the model cannot answer ordinary prompts or run on Apple
Silicon. A pass proves only this bounded endpoint gate; it is not yet a
quality ranking or an automatic recommendation.

## Reliability soak

All nine core-pass artifacts completed an independent 30-minute reliability
cell. Across the nine cells, the runner recorded 392 complete task cycles,
1,960 bounded samples, 1,960 unload proofs, and no failures. Average output
rates ranged from 19.680 tokens/s for Ornith 9B to 64.010 tokens/s for Gemma 4
E2B QAT. The runner removed only models downloaded by this campaign and did
not retain prompt or response text.

This proves bounded reliability only for the exact manifests, runtime,
operating system, and M4 16 GB profile recorded here. It does not prove every
prompt, longer contexts, another M4 memory tier, or an automatic product
recommendation.

## Power and thermal samples

Four separate `powermetrics` cells covered idle plus small, medium, and large
models. Each model cell retained ten samples, reported nominal thermal
pressure, proved Metal use and unload, and removed its temporary model.

| Cell | Work | Average CPU | Average GPU | Average CPU/GPU/ANE | GPU-active residency |
| --- | --- | ---: | ---: | ---: | ---: |
| Idle | No loaded model; background and display state not controlled | 0.052 W | 0.002 W | 0.054 W | 0.481% |
| Qwen 3.5 2B Q8 | 596 output tokens across two requests | 0.916 W | 8.804 W | 9.720 W | 97.776% |
| Qwen 3.5 4B Q4 | 512 output tokens | 1.835 W | 11.528 W | 13.363 W | 100% |
| Ministral 3 8B Q4 | 512 output tokens | 1.268 W | 12.275 W | 13.543 W | 100% |

These are Apple CPU/GPU/ANE estimates, not wall-outlet or whole-computer
energy. They exclude the display and external devices and should not be
compared directly with graphics-board measurements from other computers.

## Coding and runtime comparison results

The version-pinned OpenCode 1.18.19 screen completed for all 16 candidates.
Every exact cell failed at least one required coding-agent gate, so none is
eligible for a coding recommendation from this surface. Continue evidence was
not accepted or extended.

Separate native comparison cells passed bounded lifecycle checks for MLX-LM
0.31.3 with a pinned Qwen 3.5 0.8B artifact and llama.cpp commit `cd644c395`
with a pinned Qwen 3.5 0.8B GGUF. Those results prove their exact Metal,
timeout-recovery, and cleanup boundaries only; neither runtime is admitted as
the managed beginner default or as a coding surface.

## Package and repository checks

The exact merged source commit passed the native full tier on the physical Mac:
81 test groups, no skips. A fresh self-contained arm64 development app built
from that commit passed 619 packaged real-browser checks plus relocation,
read-only startup, recovery, attachment, accessibility-flow, local-privacy,
port, shutdown, and integrity gates. Its app metadata now explains the macOS
Local Network permission without granting device discovery. The app remains
unsigned, unnotarized, rejected by Gatekeeper, and not admitted for public
distribution or automatic updates.

Two different exact arm64 development-app archives also passed a physical,
development-only transition on August 21. The bounded runner performed
side-by-side staging, package-integrity and loopback-health checks, atomic
selection, an intentionally injected post-selection failure, automatic
baseline rollback and health confirmation, healthy-candidate reactivation,
marker-owned candidate removal, managed uninstall, separate user-data
preservation, and qualification-workspace cleanup. This proves those mechanics
for the two exact unsigned archives; it is not the Haven 42 production updater.

## What remains open

- A maintained coding surface that passes every required gate. OpenCode
  1.18.19 completed but all 16 exact candidates failed at least one gate.
- Gemma 4 12B QAT was identified after this frozen 16-model campaign began.
  Its exact one-candidate addendum is prepared but has not been run; starting
  that new hardware-dependent soak requires a separate owner prompt.
- Whole-system wall-power measurement. The retained Apple figures are SoC
  estimates rather than electricity-at-the-outlet measurements.
- Manual packaged-app screen-reader, keyboard, zoom, reduced-motion, physical
  clipboard, and clean-machine beginner review.
- Interactive Keychain lifecycle. The unattended synthetic create attempt was
  denied and correctly retained as blocked.
- A signed native installer and production updater with immutable release
  discovery, trusted verification, compatibility preflight, interruption
  recovery, and the already demonstrated transition mechanics.
- Signed and notarized public Haven 42 packaging. The current development app
  is intentionally ad-hoc signed and Gatekeeper does not admit it for public
  distribution.

The qualification runner removed every model it downloaded and verified
unload after every cell. The pre-existing model on the test Mac was preserved.
