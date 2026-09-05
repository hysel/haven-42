# Haven 42 0.4.0 Alpha 2 — release notes draft

Not published; release date and final download links are pending. This summary
compares Alpha 1 (`v0.4.0-alpha.1`) with the Alpha 2 implementation through
`7a883fa9d9c9c18404b1c07ed99235dbc624fa3d`. Packaging/documentation changes after
that source must be reconciled before selecting the final release artifacts.

Haven 42 runs local models for chatting, drafting, and summarizing. Alpha 2
focuses on first-time setup, model discovery, and portable desktop packages.

## Planned downloads

| Platform | Release filename | Required trust checks |
| --- | --- | --- |
| Windows x64 | `haven42-0.4.0-alpha.2-windows-x64-signed.zip` | Launcher signature, approved publisher, trusted timestamp |
| Linux x64 | `haven42-0.4.0-alpha.2-linux-x64-unsigned.tar.gz` | Published checksum; unsigned archive |
| Apple Silicon macOS ARM64 | `haven42-0.4.0-alpha.2-macos-arm64-signed-notarized.zip` | Developer ID, notarization, stapling, Gatekeeper |

These are portable archives, not MSI/DEB/RPM installers. Intel Macs and
Windows/Linux ARM64 are not included. Linux compatibility depends on the tested
distribution, runtime and hardware; there is no blanket all-distribution claim.

## Changes since Alpha 1

### First-time setup

- Setup chooses a model based on hardware. After download approval, it downloads
  the model as part of setup and prepares it for chat.
- First-run downloads stay in setup on Windows, Linux and macOS rather than
  requiring a detour through the Models page.
- Existing Ollama detection, approved use of newer versions, interrupted-download
  recovery and model selection received fixes.

### Finding and using models

- Broader family-name searches return relevant candidates, with tested choices
  identified separately from untested results.
- Hardware-fit warnings remain visible. A search result is not a promise that a
  model will fit memory, run on every engine, or produce useful results.
- Download progress and model selection fixes prevent unrelated candidates from
  sharing one model's download state and keep the selected model connected to chat.

### Conversation and desktop behavior

- A conversation-first layout gives messages more room, with compact settings,
  reply actions, technical details and research controls.
- Section-specific help tours and keyboard, focus, contrast, reduced-motion and
  high-contrast improvements make the interface easier to navigate. Automated
  checks do not establish complete accessibility coverage.
- macOS setup requests, embedded Python/resource handling, app signing layout,
  and close/reopen behavior received targeted fixes. Closing the final app window
  shuts down its application-owned local service.
- Portable data/log placement and setup behavior are more consistent across
  platforms. A separately installed Ollama still owns its own files.

### Research, updates and documentation

- Web research requires approval before a request leaves the computer. Supported
  provider paths include Wikipedia and Brave Search, with provider-specific setup
  where required.
- Engine release discovery distinguishes the certified runtime from newer,
  user-approved versions and preserves a path back to the certified baseline.
- User documentation now emphasizes setup, everyday use and troubleshooting.
  Continue is historical evidence only, not a supported setup recommendation.
- More model/hardware results are documented without transferring a pass between
  unrelated operating systems, runtimes, model digests or graphics cards.

## Upgrade and testing

Close Haven 42 and retain the old package and your user-created files. Download
the package for your platform, check its SHA-256, and extract the entire archive
into a separate user-writable folder. Run the extracted app, not the archive.
Model weights are downloaded separately after approval.

Alpha 1 remains unchanged. This alpha does not supply an automatic updater or
promise data migration between arbitrary older folder layouts. Keep the old
copy until the new one has been checked successfully.

Read the [known limitations](alpha-2-known-limitations.md) and Accessibility
Statement. The release capabilities are Chat, Write and Summarize; coding-agent
integrations and image, audio and video generation are outside this package scope.
Report the version, platform and reproduction steps, but remove conversations,
attachments, credentials, addresses, identities and raw logs before posting.
Report vulnerabilities through the private security channel.

## Maintainer publication checklist

Do not publish this draft unchanged. Finalize the date, immutable source/tag,
download links, checksums and artifact evidence after signing and native package
review. Known-limitations snapshots must agree with the three-platform scope.
Separate owner approval is still required to publish a release.
