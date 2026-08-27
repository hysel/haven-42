# Alpha 2 known limitations

These limitations apply to the Haven 42 `0.4.0-alpha.2` Windows and Linux
prerelease candidates.

- The archives are unsigned prerelease builds for invited testers. Windows,
  browsers, or endpoint-protection software may warn before opening them.
- Alpha 2 provides portable archives, not a native installer, system service,
  automatic updater, or production deployment.
- The release scope covers Windows x64 and Linux x64. macOS packaging is not
  part of this release.
- Native promotion evidence is limited to the exact Windows 11 NVIDIA, Ubuntu
  26.04 NVIDIA, and Bazzite 44 NVIDIA cells recorded for the candidate. CPU-only
  Linux package and desktop checks do not prove accelerator support.
- AMD, Intel, mixed-GPU, lower-memory, and other untested combinations keep
  their existing lower support label. Evidence from one operating system,
  accelerator, runtime, or memory profile does not transfer to another.
- The admitted product capabilities are Chat, Write, and Summarize. Coding-agent
  surfaces and image, audio, and video generation are outside this release
  boundary.
- Ollama `0.32.14` is the certified managed runtime for this release. A user may
  approve a newer unverified runtime, but its behavior is not inherited from the
  certified version and rollback to `0.32.14` must remain available.
- Model recommendations apply only to exact evidence-backed hardware, runtime,
  model digest, and capability combinations. Unknown combinations remain manual
  rather than receiving an inferred automatic selection.
- Haven 42 does not replace vendor GPU drivers or operating-system updates.
- The Accessibility Statement identifies the exact manual browser, operating
  system, assistive-technology, keyboard, zoom, motion, and forced-color cells
  reviewed for the published candidate. An untested cell must not inherit a pass.

These limitations do not authorize distribution. Publication still requires
the exact candidate archives, native validation, security and privacy review,
supply-chain evidence, hosted checks, and explicit owner approval.
