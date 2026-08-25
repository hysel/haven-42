# Local Audio Provider Validation

## ACE-Step 1.5 Linux CUDA partial pass

A disposable exact-profile feasibility cell ran on 2026-07-22. It validates one instrumental REST operation and its runtime lifecycle without promoting an audio provider or authorizing executable integration files.

| Field | Value |
| --- | --- |
| Source commit | `6d467e4b5081ccb0abf1ec1bf4fdf9051a2d34b0` |
| Package / resolver | `ace-step==1.5.0`; uv 0.11.31; frozen lock |
| Runtime | Python 3.12.3; PyTorch 2.10.0+cu128 |
| Hardware | Linux x64; Tesla V100-SXM2 32 GB selected; compute capability 7.0 |
| Model profile | `acestep-v15-turbo` plus auto-selected `acestep-5Hz-lm-4B` |
| Source artifact SHA-256 | turbo `3f6e0797fad420a39bd33979eb6e840e30989e34a3794e843d23b60ec6e422d7`; LM shards `ada9d0d4ff48f112de3f7b82cd4e7d57b4245932657e8b8edc9a5ded6a23b77f` and `6302100c3577e2f1dbf32573e9b5e6e6b1bea7af101b433c2d3d6280faa8ab68` |
| Observed loaded GPU memory | 19,449 MiB on the selected V100 |
| Generated artifact | stereo PCM WAV; 48 kHz; 10.000 seconds; 1,920,078 bytes |
| Generated SHA-256 | `5bf012e0420ec9ce2862e5da9509b638762246e5b450374eb38ae8556fae76aa` |

The loopback API passed health, queue submission, deterministic seed, bounded generation, RIFF/WAVE decoding, exact duration, sample rate, channels, and in-memory hashing. Model initialization succeeded, the output was generated in about 3.3 seconds after initialization, and the exact owned process stopped without affecting Ollama or ComfyUI. The isolated checkout, dependencies, weights, output, and run-created uv/Hugging Face caches were removed.

The cell exposed an onboarding risk: the 32 GB hardware tier automatically downloaded and initialized the 4B planner even though the request set `thinking=false` and supplied metadata. Haven 42 must disclose the resolved planner, added download, storage, and memory before execution and must pin rather than silently accept this choice.

Status remains `partial-pass`. Vocal generation, audio non-silence and clipping analysis, listening/quality review, cancellation during diffusion, failure recovery, retention controls, and a provider-neutral typed artifact adapter remain open. No prompt, endpoint, task ID, raw response, server address, or output audio is committed.

## Quadro RTX 5000 follow-on partial pass

A second disposable Linux CUDA cell ran on 2026-08-03 using the same source
commit and frozen package lock on Ubuntu 26.04, Python 3.12.13, PyTorch
`2.10.0+cu128`, NVIDIA driver 595.84, and a Quadro RTX 5000 16 GB. The exact
model revision remained `19671f406d603126926c1b7e2adc169acbcade22`.
Only the turbo DiT, VAE, and required Qwen text encoder were downloaded, for
6,336,680,772 selected bytes. Their large-file SHA-256 values were,
respectively,
`3f6e0797fad420a39bd33979eb6e840e30989e34a3794e843d23b60ec6e422d7`,
`da17edb604c40deaf09e9b24974e590d1ca83a374070e5d0884cfa4bed9a99b0`,
and
`0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd`.
The 1.7B and 4B planners were not downloaded.

An ignored review harness generated separate instrumental and lyric-bearing
vocal requests with complete metadata and disabled thinking, formatting, CoT,
random seed selection, reference audio, and planner initialization. Both
outputs were decodable 10-second stereo 48 kHz WAV files. The instrumental
artifact was 1,920,044 bytes with SHA-256
`bf4e248e09f3aaf886388917b834eab5a688dc07ccf5c88851bb5a4dda10237f`;
its RMS was 0.11778012, peak magnitude 0.89126587, near-silence fraction
0.020703125, and clipping fraction zero. The vocal-request artifact was the
same size with SHA-256
`78f97a4eec093a04750dbb0a4a3f073455b51ac78361e239c00d2a54f9bf23b5`;
its RMS was 0.1101364, peak magnitude 0.89126587, near-silence fraction
0.0139458333, and clipping fraction zero. Structural success for a vocal
request is not a listening-quality claim; both WAVs remain only in ignored
local review storage for owner listening.

The run used 7,624 MiB of GPU memory. A separate 600-second task reached 93%
GPU utilization before the exact run-owned process group received `SIGTERM`.
It stopped without a forced kill, emitted no WAV, and left no process or
listener. The same pinned runtime then restarted, passed health, generated a
fresh valid instrumental recovery artifact, and shut down exactly.

The native entry point exposed two upstream admission defects. Its OpenRouter
`/v1/models` route shadows the authenticated local inventory route and remains
public even when an API key is configured. It also reports a default LM model
name in completed-task metadata while inventory and execution logs prove the
planner is disabled and unused. The live cell therefore used an ignored
single-import launcher with constant-time top-level authentication on every
route except health, and queried the unambiguous `/v1/model_inventory` route.
This review-only mitigation is not shipped and does not promote the upstream
entry point.

Status remains `partial-pass`. Signal and clipping analysis, separate
instrumental/vocal structural requests, active process cancellation, forced
recovery, isolated artifact retention, and a review-only typed audio envelope
now pass on this exact Quadro profile. Human listening, actual retention
deletion, complete uninstall, a production authentication/route fix, a shipped
provider-neutral adapter, package parity, and native non-Linux profiles remain
open. No prompt, lyrics, endpoint, task ID, raw response, server address,
account, local path, log, model, runtime, or output audio is committed.

Official sources: [ACE-Step project](https://github.com/ace-step/ACE-Step-1.5), [installation guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md), and [API guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md).
