# Local Audio Provider Candidates

Recorded 2026-07-22 from official upstream repositories, model cards, and one disposable Linux CUDA feasibility cell. The live cell is partial evidence only. It does not promote a provider or add `audio.music.create`, scripts, adapters, workflows, configuration, or installer assets.

## ACE-Step 1.5

The current application release is `v0.1.8`, resolving to Git commit `dce621408bee8c31b4fcf4811682eb9359e1bc94`. The separately versioned official `ACE-Step/Ace-Step1.5` model repository was observed at revision `19671f406d603126926c1b7e2adc169acbcade22`, with 10,079,024,720 bytes of LFS-managed blobs.

| Baseline file | Bytes | Published SHA-256 |
| --- | ---: | --- |
| `acestep-v15-turbo/model.safetensors` | 4,787,825,604 | `3f6e0797fad420a39bd33979eb6e840e30989e34a3794e843d23b60ec6e422d7` |
| `acestep-5Hz-lm-1.7B/model.safetensors` | 3,708,521,528 | `f161689da73e5ecefa28ff780d51c2d92a00f056d021d7933c779ed5c6cd7db8` |
| `vae/diffusion_pytorch_model.safetensors` | 337,431,388 | `da17edb604c40deaf09e9b24974e590d1ca83a374070e5d0884cfa4bed9a99b0` |

The project and model card declare MIT licensing and describe text-to-music, lyrics/vocals, instrumental generation, reference audio, cover, repaint, and related editing operations. Upstream currently claims Python 3.11–3.12 plus CUDA, ROCm, Intel XPU, Apple Silicon MLX/MPS, and CPU paths. These are claims, not Haven 42 evidence; every OS/accelerator/operation remains candidate-only.

The first Linux CUDA REST cell ran at commit `6d467e4b5081ccb0abf1ec1bf4fdf9051a2d34b0`. A deterministic 10-second instrumental request produced a valid stereo 48 kHz WAV and the isolated runtime cleaned up successfully. Automatic selection of the 4B planner caused an undisclosed additional download even with `thinking=false`; exact pre-execution model disclosure is therefore a required product gate. Vocal generation, signal/clipping analysis, listening review, cancellation, and forced recovery remain open. See `examples/local-audio-provider-validation.md`.

Official sources: [release](https://github.com/ace-step/ACE-Step-1.5/releases/tag/v0.1.8), [project](https://github.com/ace-step/ACE-Step-1.5), [model card](https://huggingface.co/ACE-Step/Ace-Step1.5), and [hardware guide](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/GPU_COMPATIBILITY.md).

## Stable Audio 3

Stable Audio 3 uses the Stability AI Community License and redistributes T5Gemma components under their own terms. Model access is gated and commercial use must be evaluated against the current Stability licensing program; this is a product-policy constraint, not merely attribution text.

| Candidate | Model revision | LFS bytes | Primary weight SHA-256 | Intended evaluation |
| --- | --- | ---: | --- | --- |
| Small SFX | `ae12755283df9d62ca39a9b050a39a0b607b8c20` | 3,493,474,189 | `ed9cf1b6172f1a8c2921a9560c21109ff3239524563ced9dce6dcdef41e2f515` | Sound effects, editing, continuation |
| Medium | `27b5a21b791b1b033d193a9e1e3ce78493f102f9` | 10,445,205,909 | `48d9c65e290e7bcd5194e0633bfc2424a59ee9683f5c2d58762d997b7d8ce0b5` | Music, sound effects, editing, longer duration |

Both recorded profiles use `t5gemma-b-b-ul2/model.safetensors` at 1,183,022,944 bytes with SHA-256 `9b05ea5a4f211d023832f706fb2c0e83e4fc721b6da35ab69ceb0b55eb7800d3`.

The official Small Music repository is visible but gated metadata could not be resolved anonymously on 2026-07-22. Its exact immutable revision, files, and hashes therefore remain an explicit blocker; Haven 42 must not substitute the Small SFX revision or infer identity from the 0.6B parameter label.

Official sources: [Stable Audio 3 collection](https://huggingface.co/collections/stabilityai/stable-audio-3), [Small SFX](https://huggingface.co/stabilityai/stable-audio-3-small-sfx), [Medium](https://huggingface.co/stabilityai/stable-audio-3-medium), and [Stability licensing](https://stability.ai/license).

## Admission Decision

No audio provider is promoted. ACE-Step has a partial Linux CUDA instrumental feasibility pass but has not completed its external gate. Stable Audio remains gated by authenticated model acquisition plus exact license review. The shared consent boundary is defined in `docs/generative-media-consent-policy.md`.
