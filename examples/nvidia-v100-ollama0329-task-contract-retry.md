# NVIDIA V100 Ollama 0.32.9 Task-Contract Retry

This record covers a bounded runtime-update retry for five exact model
artifacts. It records negative engineering evidence so a future updater cannot
assume that installing a newer runtime fixed a model-specific validation
failure.

## Tested profile

- Operating system: Ubuntu 24.04.4 LTS
- Accelerator: two NVIDIA Tesla V100-SXM2 cards with 32 GiB each
- Runtime: Ollama 0.32.9
- Gate: fixed chat, writing, and summarization task contracts before a planned
  30-minute soak
- Privacy: no prompts, responses, machine names, addresses, or device IDs were
  retained

## Results

| Exact model | Manifest digest | Result |
| --- | --- | --- |
| `gemma3:1b-it-q4_K_M` | `8648f39daa8fbf5b18c7b4e6a8fb4990c692751d49917417b8842ca5758e7ffc` | Failed the task-contract gate |
| `phi4-mini:3.8b-q4_K_M` | `78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753` | Failed the task-contract gate |
| `ministral-3:3b-instruct-2512-q4_K_M` | `f04aa1c738f64e13c625b82ae92504fc0260fa6723b509ed1ece0fa188179b1d` | Failed the task-contract gate |
| `ministral-3:8b-instruct-2512-q4_K_M` | `1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71` | Failed the task-contract gate |
| `muse-glimmer:30b` | `de878ce33ad81d060001db1469a02eebe4d86f0ad58cfe52dc062fdcbe4464c1` | Failed the task-contract gate |

All five exact artifacts received the same `soak-task-contract-failed`
classification previously observed with Ollama 0.32.8. Because the mandatory
task gate failed, the runner correctly did not treat an unstarted 30-minute
soak as a pass.

## What this means

- Updating from Ollama 0.32.8 to 0.32.9 did not resolve these five failures on
  this exact profile.
- This does not prove that the models cannot run. It proves only that the exact
  artifact/runtime/profile combinations did not satisfy Haven 42's required
  task behavior.
- The result does not apply to another runtime, operating system, accelerator,
  quantization, or model digest.
- Nothing in this retry changes the automatic model ladder or admits a model.
