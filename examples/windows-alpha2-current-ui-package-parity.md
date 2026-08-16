# Windows Alpha 2 Current UI Package Parity

Status: unsigned development package evidence; not release or accessibility
certification.

On August 15, 2026, Haven 42 built an ignored Windows Alpha 2-only portable
package from the current worktree. Alpha 1 was not built or modified.

The following checks passed:

- 460 source local-web security and behavior checks;
- 529 source Chromium-family headless browser checks;
- source-versus-package API and protected-resource parity;
- package relocation and read-only startup;
- abrupt-exit recovery and repeated lifecycle;
- port-collision, shutdown-authority, hostile-environment, and integrity
  checks; and
- 529 packaged Chromium-family headless browser checks.

The browser flow covers the current section tours, focus behavior, landmarks,
control target sizes, reduced motion, responsive behavior, status semantics,
and Accessibility Statement route. The packaged Accessibility Statement bytes
match source through the protected-resource manifest.

This evidence does not replace manual keyboard, 200%/400% zoom, forced-colors,
or NVDA, JAWS, VoiceOver, and TalkBack testing. The package is unsigned,
ignored local review material and was not published. Linux and macOS packaged
parity remain separate cells.
