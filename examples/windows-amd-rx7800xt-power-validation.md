# Radeon RX 7800 XT model power validation

## What was tested

On 2026-08-13, a 30-minute Windows 11 soak ran `qwen3.5:9b` Q4_K_M
through Ollama 0.32.5 on one Radeon RX 7800 XT with 16 GiB of graphics
memory. The bounded Chat, Writing, and Summarization matrix completed 50 of
50 cells. Every cell reported full graphics-card offload, and the average
generation speed was 65.93 tokens per second.

AMD Software: Adrenalin Edition recorded `GPU BRD PWR` once per second during
the run. The soak and metrics windows were correlated by UTC time. No prompt,
response, computer name, account name, network address, or local path is in
this record.

The controlled rerun included the required 120-second idle baseline and 1,807
active one-second samples. Haven 42's importer accepted the result as an
exact-profile GPU energy measurement. This remains engineering evidence: it
does not approve the model as an automatic default or make a whole-computer
claim.

## Measured result

| Scope | Average | Peak | Energy |
|---|---:|---:|---:|
| Full 30-minute soak | 40.084 W | 261 W | 20.142 Wh |
| Idle baseline | 24.202 W | — | — |
| Idle-adjusted full soak | 15.882 W | — | 7.981 Wh |

During the individual response windows, Chat averaged 53.663 W, Writing
averaged 57.688 W, and Summarization averaged 52.173 W. The highest task peak
was 249 W during Writing. Peak graphics temperature was 48 °C.

## How to read this result

The full-soak average includes idle gaps because the model was deliberately
unloaded after every test cell. That makes the result useful for this exact
Haven 42 usage pattern, but not as a universal power rating for the model.
The response-window figure isolates the recorded generation windows more
closely.

These are **graphics-card board-power readings**, not whole-computer power.
They omit the CPU, memory, storage, cooling, power-supply losses, and display.
The evidence supports a GPU-only electricity estimate for this exact hardware,
runtime, model, quantization, and workload. It does not change Haven 42's
automatic model choice, automatically enable cost estimates, or certify other
AMD cards.
