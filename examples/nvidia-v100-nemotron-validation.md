# NVIDIA V100 Nemotron 3.5 Lightning Validation

This record covers two exact Nemotron 3.5 Lightning artifacts on one exact
high-memory NVIDIA test profile. It is engineering evidence, not an automatic
Haven 42 model choice.

## Tested profile

- Operating system: Ubuntu 24.04.4 LTS
- Accelerator: two NVIDIA Tesla V100-SXM2 cards with 32 GiB each
- Runtime: Ollama 0.32.9
- Workload: fixed chat, writing, and summarization contracts followed by a
  30-minute soak
- Privacy: no prompts, responses, machine names, addresses, or device IDs were
  retained

The first attempt on Ollama 0.32.8 stopped with provider errors before
inference. The same exact artifacts were retried only after the runtime was
updated to the models' recorded 0.32.9 minimum.

## Results

| Exact model | Manifest digest | Soak result | Samples | Average output speed | Peak reported GPU-resident bytes |
| --- | --- | --- | ---: | ---: | ---: |
| `nemotron-3.5-lightning:30b-a3b-q4_K_M` | `e7a64ff15fb174c42b4f463e5c888c4f2c7b9cabf9e8d65a1c0874405426c1b2` | Passed | 81 across 9 cycles | 62.067 tokens/s | 25,275,179,990 |
| `nemotron-3.5-lightning:30b-a3b-q8_0` | `9983b24ee511395c8d58ce1f92e0e8c11c4e2fb43029d1718c1d6694e8187117` | Passed | 72 across 8 cycles | 47.574 tokens/s | 35,176,694,411 |

Every completed cycle passed the fixed chat, writing, and summarization
contracts and unloaded between samples. The Q8 result required more than one
card's nominal 32 GiB capacity, which is useful aggregate-residency evidence.
The current record does not independently prove the exact split between the
two cards.

## Graphics-card energy

The same exact artifacts were measured separately with a two-minute idle
baseline followed by five minutes of the fixed three-task workload. These are
combined board readings from the two V100 cards, not whole-computer power.

| Exact model | Load average | Load peak | Measured energy | Idle-adjusted energy | Output efficiency | Peak temperature |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `nemotron-3.5-lightning:30b-a3b-q4_K_M` | 155.005 W | 280.01 W | 12.932521 Wh | 7.658127 Wh | 1,524.219 output tokens/Wh | 64 °C |
| `nemotron-3.5-lightning:30b-a3b-q8_0` | 141.373 W | 369.20 W | 11.852012 Wh | 6.552177 Wh | 1,274.383 output tokens/Wh | 53 °C |

The Q8 run had a lower five-minute average but a higher instantaneous peak and
lower output-token efficiency. This single controlled run is useful comparison
evidence; it is not a universal electricity-cost claim. CPU, memory, storage,
cooling, power-supply losses, and displays are outside the measurement.

## What remains open

- Tool use, thinking-mode behavior, recovery, and the planned 8K and 32K
  context checks were not part of this run.
- No llama.cpp result is implied by this Ollama result.
- Neither result changes the automatic model ladder. Product admission still
  requires the remaining gates and explicit owner approval.
