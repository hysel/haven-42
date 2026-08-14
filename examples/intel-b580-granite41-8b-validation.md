# Intel Arc B580 Granite 4.1 8B Validation

This record covers one exact Granite 4.1 8B artifact on the Linux Intel SYCL
route. It is a narrow recovery result after earlier mixed-model Intel runs
exposed load failures and host instability.

## Tested profile

- Operating system: Ubuntu Linux
- Accelerator: Intel Arc B580 with 12 GiB graphics memory
- Runtime: llama.cpp b10375, SYCL source build
- Runtime binary SHA-256:
  `d7416c77bd3584a28c48a724221e59e5dd92280f796c1fa1d4a2ac9b8f47be86`
- Model artifact size: 5,347,914,400 bytes
- Model artifact SHA-256:
  `ed902ac9eb6adce5a90c6a08c8ea201b50e23fdc5976d1cd0362006afac5309e`

## Result

The 30-minute run passed 15 samples: five chat, five writing, and five
summarization checks. llama.cpp reported all 41 model layers on the SYCL
device. The listener closed and the process stopped at the end.

The completed samples produced 140 output tokens at about 40.7 tokens per
second. Card-only energy telemetry recorded 463.334 joules during active
inference, or 3.310 joules per output token. The broader 30-minute interval
included deliberate idle time, so its 34.933-watt average must not be treated
as whole-computer power or as continuous-generation load.

## Evidence boundary

- This proves the exact Granite artifact and runtime binary on this Linux Arc
  B580 profile only.
- It does not erase the failures of other Intel models or establish Windows
  SYCL support.
- It does not admit llama.cpp b10375, Granite 4.1 8B, or Intel SYCL as an
  automatic Haven 42 route. Package lifecycle, broader recovery, and owner
  approval remain open.
- No prompts, responses, addresses, hostnames, usernames, or device IDs are
  included in this record.
