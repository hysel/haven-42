# Ministral 3 Task-Contract Retry on Ollama 0.32.13

Status: exact-profile negative engineering evidence; no automatic selection or
default change.

On August 16, 2026, the exact Ministral 3 3B and 8B Q4 artifacts were retried
against the current Haven 42 Chat, Writing, and Summarization qualification
contract. The review environment used Ubuntu 24.04.4, Ollama 0.32.13, 128 GiB
of system memory, and two Tesla V100 32 GiB cards. Ollama was reached only
through an authenticated local tunnel to its IPv4 loopback endpoint.

The runner retained no prompt or response text, endpoint, machine identity,
account information, or filesystem path. Passing cells required three samples,
three unload proofs, and nonzero CUDA residency. A model had to pass all three
tasks before a reliability soak could start.

## Results

| Exact model | Manifest digest | Chat | Writing | Summarization | Soak |
| --- | --- | --- | --- | --- | --- |
| `ministral-3:3b-instruct-2512-q4_K_M` | `f04aa1c738f64e13c625b82ae92504fc0260fa6723b509ed1ece0fa188179b1d` | Passed: 3 samples and 3 unloads; 155.310 tokens/s average | Failed: more than one sentence | Passed: 3 samples and 3 unloads; 154.890 tokens/s average | Not started |
| `ministral-3:8b-instruct-2512-q4_K_M` | `1922accd5827ebe6829e536369195db25eaf664528dc66206d646ea3bb386b71` | Passed: 3 samples and 3 unloads; 94.987 tokens/s average | Failed: more than one sentence | Failed: more than one sentence | Not started |

The passing 3B cells reported a peak of 2,838,872,718 GPU-resident bytes. The
passing 8B Chat cell reported 5,802,473,552 GPU-resident bytes. These are
runtime-reported residency measurements from this aggregate-GPU environment,
not proof for a smaller physical memory tier.

## Interpretation

Both exact artifacts can load, generate, use CUDA, and unload on this profile.
They still do not satisfy all of Haven 42's deterministic task requirements,
so neither artifact entered a 30-minute soak or became eligible for automatic
selection. The failure is task-specific rather than a download, startup,
runtime-crash, or GPU-offload failure.

This result preserves rather than replaces the earlier Ollama 0.32.9 negative
evidence. It also does not generalize to another prompt contract, runtime,
operating system, accelerator vendor, quantization, or model digest. A future
retest needs a reviewed reason, exact metadata, and the same fail-closed task
gate before any soak.
