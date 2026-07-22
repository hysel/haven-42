# Local Audio Provider Validation

## ACE-Step 1.5 Linux CUDA partial pass

A disposable exact-profile feasibility cell ran on 2026-07-22. It validates one instrumental REST operation and runtime lifecycle; it does not promote an audio provider or authorize executable integration files.

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

Official sources: [ACE-Step project](https://github.com/ace-step/ACE-Step-1.5), [installation guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md), and [API guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/API.md).
