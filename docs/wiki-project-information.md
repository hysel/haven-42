# About Haven 42

Haven 42 runs useful AI locally instead of sending every conversation to a
hosted chat service. Its interface runs in a browser, while the application
and AI provider stay on hardware you control.

## What Haven 42 is designed to do

- Make local chat, writing, and summarization approachable for non-experts.
- Recommend models from results collected on comparable hardware.
- Explain downloads, storage locations, and network activity before asking for
  approval.
- Keep model choice open: recommendations are guidance, not restrictions.
- Stop safely when a download, model, server, or security check cannot be
  verified.

## What it does not do

Haven 42 does not provide a hosted AI account or silently send prompts to a
cloud service. It does not install drivers, change firewall rules, or grant
itself administrator access. Current builds do not save conversation history,
parse PDF or Office documents, install themselves as a system service, or run
unattended automatic updates.

Some features in the engineering documents are experiments, not parts of the
current app. A successful test applies only to the named model,
runtime, operating system, and hardware—not every similar computer.

## Releases

The latest public test build is the unsigned Windows `0.4.0-alpha.1`
prerelease. The latest stable release line is `0.3.0`. Changes in the source
repository are not a release until they are deliberately packaged and
verified.

Current development packages are unsigned. Windows or macOS may warn before
opening them, so use only files from a trusted Haven 42 test source.

## Privacy, security, and accessibility

- [[Privacy|Privacy-Policy]] explains what the app keeps in memory and what may
  leave the computer.
- [[Connection Security|Provider-Endpoint-Security]] explains safe local and
  private-network AI-server connections.
- The app's **About → Accessibility** page describes the current WCAG 2.1 AA
  target, implemented support, assessment method, and known limitations.

Report a security problem privately through the process in the repository's
`SECURITY.md`. Do not post passwords, private prompts, personal files, or
private network details in a public issue.

## Questions and feedback

For general or accessibility feedback, email `haven42localai@gmail.com` or use
the repository's issue forms. Include the operating system and the part of the
app involved, but do not include secrets or private content.

## For contributors

Everyday instructions stay in this wiki. Contributor architecture, validation,
and research material is organized in the
[[Engineering and Validation Index|Engineering-Index]]. Planned work is kept
in the [[Roadmap]] rather than mixed into user instructions.
