# Windows Alpha 2 Current UI Package Parity

Status: unsigned development package evidence; not release or accessibility
certification.

On August 16, 2026, Haven 42 built an ignored Windows Alpha 2-only portable
package from the current worktree. Alpha 1 was not built or modified.

The following checks passed:

- 460 source local-web security and behavior checks;
- 591 source Chromium-family headless browser checks;
- source-versus-package API and protected-resource parity;
- package relocation and read-only startup;
- abrupt-exit recovery and repeated lifecycle;
- port-collision, shutdown-authority, hostile-environment, and integrity
  checks; and
- 591 packaged Chromium-family headless browser checks.

The browser flow covers the current section tours, focus behavior, landmarks,
control target sizes, reduced motion, responsive behavior, status semantics,
the Accessibility Statement route, and the dormant controlled-research review
dialog's exact disclosure, trusted single-use approval, cancellation, focus
containment and return, inert background, and no-network boundary. The packaged
Accessibility Statement and protected UI bytes match source through the
resource-integrity manifest.

This evidence does not replace manual keyboard, 200%/400% zoom, forced-colors,
or NVDA, JAWS, VoiceOver, and TalkBack testing. The package is unsigned,
ignored local review material and was not published. Linux and macOS packaged
parity remain separate cells.
