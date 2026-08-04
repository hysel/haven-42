# Local Video Provider Candidates

Recorded 2026-07-22 from official upstream repositories and model cards, then rechecked against official upstream requirements and licenses on 2026-08-04. These candidates are documentation-only. No video capability, adapter, harness, workflow, runtime configuration, model, or installer is admitted.

## HunyuanVideo 1.5

- Source code: Git commit `60783e704160023913bee78f0b47036d393d4dfa`; the project does not publish a GitHub release tag.
- Model repository: `tencent/HunyuanVideo-1.5` revision `9b49404b3f5df2a8f0b31df27a0c7ab872e7b038`.
- Declared license: Tencent Hunyuan Community License; legal review is required before redistribution or product promotion.
- Territorial restriction: the official license excludes the European Union,
  United Kingdom, and South Korea. This is a hard promotion blocker unless a
  later legal and product-policy review establishes a compliant scope.
- Claimed scope: 8.3B parameters, Linux/CUDA, text-to-video and image-to-video, 480p/720p paths, and consumer GPU operation with offloading.
- Repository aggregate: 371,770,754,991 LFS bytes across multiple independent checkpoints; a validation profile must download only its exact allowlisted files.

| Reference transformer | Bytes | Published SHA-256 |
| --- | ---: | --- |
| `480p_t2v` | 33,306,632,192 | `71f9affa1115fef2b14bd41fba30eab966fe80c9ed98e0fcba495dbc6d8fff86` |
| `480p_i2v_step_distilled` | 33,325,523,336 | `29418e43ef5bfa1868703c26f9b45c622b473960c479dc5be43bba7bd0004f6d` |

Official sources: [code](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5) and [model card](https://huggingface.co/tencent/HunyuanVideo-1.5).

## Wan2.2 TI2V-5B

- Source code: Git commit `42bf4cfaa384bc21833865abc2f9e6c0e67233dc`; the project does not publish a GitHub release tag.
- Model repository: `Wan-AI/Wan2.2-TI2V-5B` revision `921dbaf3f1674a56f47e83fb80a34bac8a8f203e`.
- Declared license: Apache-2.0.
- Claimed scope: unified text-to-video and image-to-video, 720p at 24 FPS, with the official single-GPU example requiring at least 24 GB VRAM.
- Recorded LFS download: 34,202,832,421 bytes.

| File | Bytes | Published SHA-256 |
| --- | ---: | --- |
| Transformer shard 1 | 9,825,014,472 | `720b06c4ade5e87c1246bba8ac95b664c638749cd9b102cf84d823bb44c026a1` |
| Transformer shard 2 | 9,995,661,736 | `09ec5ef720d8396f6cfa51fbdcbdb2327e37722afd6e89fd38f1e7e5e782c283` |
| Transformer shard 3 | 178,558,176 | `6306f7894c345de9093ad588771c2abfaeb668a81f7a6d9a918bd26ba3568e49` |
| VAE | 2,818,839,170 | `20eb789667fa5e60e7516bf509512f6cb61f01b0aa0695eadaea930c13892b36` |
| UMT5 encoder | 11,361,920,418 | `7cace0da2b446bbbbc57d031ab6cf163a3d59b366da94e5afe36745b746fd81d` |

Official sources: [code and requirements](https://github.com/Wan-Video/Wan2.2) and [model files](https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B).

## LTX-2.3

- Source code: Git commit `9377758131b1ffde4b7f766804590a6617bf2ab9`; the project does not publish a GitHub release tag.
- Model repository: `Lightricks/LTX-2.3` revision `4229404625088d21c4f112eb640fb04a0900ee25`.
- Declared license: LTX-2 Community License Agreement; exact use and redistribution rights require review.
- Claimed scope: text/image/video/audio-conditioned generation, interpolation, retake, and synchronized audio/video pipelines.
- Published local requirements remain a high-end NVIDIA/CUDA profile with about 32 GB VRAM and 100 GB storage. This is not a consumer-default candidate.
- Repository aggregate: 157,004,866,317 LFS bytes.

| Reference weight | Bytes | Published SHA-256 |
| --- | ---: | --- |
| `ltx-2.3-22b-dev.safetensors` | 46,149,344,974 | `7ab7225325bc403448ea84b6db2269811a880e5118cd2ee2b6282a93d585016f` |
| `ltx-2.3-22b-distilled.safetensors` | 46,149,345,038 | `14409a4d1337a8ded02fa87fb895b17a91ab2c6588f7cc3352e624ff18a689bf` |

Official sources: [system requirements](https://docs.ltx.io/open-source-model/getting-started/system-requirements), [pipelines](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/README.md), [code](https://github.com/Lightricks/LTX-2), and [model card](https://huggingface.co/Lightricks/LTX-2.3).

## Evaluation Order And Admission Decision

HunyuanVideo 1.5 and Wan2.2 require separate Linux NVIDIA evaluations for text-to-video and image-to-video. LTX-2.3 remains deferred until suitable 32 GB-class VRAM and storage are available. Every run must verify accelerator use, duration, resolution, frame rate/count, codec/container decoding, non-empty frames, cancellation, timeout, restart, retained state, cleanup, rollback, and uninstall.

An exact-profile preflight on 2026-08-03 evaluated an Ubuntu 26.04 host with a
Quadro RTX 5000 (16,384 MiB VRAM, CUDA capability 7.5), 16 GB system memory,
and 34,332,434,432 available filesystem bytes. Wan2.2 TI2V-5B was rejected
before download because its official single-GPU path requires at least 24 GB
VRAM and its 34,202,832,421-byte model set leaves no runtime, output, or safety
reserve. LTX-2.3 remained rejected against its published 32 GB VRAM and 100 GB
storage profile. HunyuanVideo 1.5 declares a 14 GB offloaded minimum, but its
33,306,632,192-byte reference transformer alone would leave only
1,025,802,240 bytes before the remaining checkpoint files, dependencies,
runtime, caches, and output. Its source-code path also enables prompt rewriting
by default and can use an external vLLM-compatible service, so any future cell
must explicitly disable rewriting and prove zero unapproved network activity.
No source tree, dependency, model, prompt, reference media, output, or service
was created by this fail-closed preflight.

Windows NVIDIA is a separate native profile. Windows Intel, Windows AMD, and Apple Silicon remain unavailable until a credible exact provider path passes. The identity, likeness, reference-media, generated-content, and commercial-use controls are defined in `docs/generative-media-consent-policy.md`.
