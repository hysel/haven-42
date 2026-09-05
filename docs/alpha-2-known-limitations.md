# Alpha 2 known limitations

These limitations apply to the Haven 42 `0.4.0-alpha.2` Windows x64, Linux x64,
and Apple Silicon macOS ARM64 prerelease candidates. Publication and final-package
validation remain separate from building a candidate.

- The release requires a signed, timestamped Haven 42 launcher on Windows and a
  Developer ID signed, notarized, stapled app on macOS. Linux remains unsigned.
  Check the final published SHA-256 manifest; a signature is not a guarantee that
  an alpha has no bugs. Unsigned preparation builds are not signed release packages.
- Alpha 2 provides portable archives, not a native installer, system service,
  automatic updater, or production deployment.
- There are no MSI, DEB, or RPM installers in this release set. Intel Macs and
  Windows/Linux ARM64 packages are outside its scope. A Linux x64 archive does
  not imply support for every Linux distribution.
- Native results apply to the exact package and hardware/OS configuration tested.
  Earlier Windows, Linux, or Apple M4 candidate results do not replace review of
  the final artifacts. CPU-only Linux package and desktop checks do not prove
  accelerator support.
- AMD, Intel, mixed-GPU, lower-memory, and other untested combinations keep
  their existing lower support label. Evidence from one operating system,
  accelerator, runtime, or memory profile does not transfer to another.
- The admitted product capabilities are Chat, Write, and Summarize. Coding-agent
  surfaces and image, audio, and video generation are outside this release
  boundary.
- Ollama `0.32.14` is the certified managed runtime for this release. A user may
  approve a newer unverified runtime, but its behavior is not inherited from the
  certified version and rollback to `0.32.14` must remain available.
- Tested recommendations apply to recorded hardware, runtime, model digest, and
  capability combinations. Search may also show untested models with hardware
  warnings; visibility is not a promise of compatibility, memory fit, or quality.
- Model weights are downloaded separately after approval, not bundled in the
  application archive. Separately installed providers keep their own data paths.
- Haven 42 does not replace vendor GPU drivers or operating-system updates.
- The Accessibility Statement identifies the exact manual browser, operating
  system, assistive-technology, keyboard, zoom, motion, and forced-color cells
  reviewed for the published candidate. An untested cell must not inherit a pass.

These limitations do not authorize distribution. Publication still requires
the exact candidate archives, native validation, security and privacy review,
supply-chain evidence, hosted checks, and explicit owner approval.
