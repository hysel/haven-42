# Haven 42 repository instructions

## Model-family version certification

- When the owner prompts for model-version research or certification, check official primary sources for newer families and versions of every model family in scope. Do not rely on mutable `latest` tags or community claims as release evidence.
- When a newer version is found, inventory its official release status, license, local weights or registry artifacts, exact tags and digests, supported runtimes, sizes, quantizations, and hardware fit. Keep local, hosted-API-only, announced-but-unreleased, and unavailable candidates visibly distinct.
- Identify every credible candidate that can run on a supported local computer. Prepare a version-pinned capability matrix and a fail-closed soak-test definition for each eligible candidate.
- Give every executable local-model candidate a coding-agent screen, even when its publisher does not market it as a coding model. The screen must cover deterministic structured code generation, repository read and planning, review, exact filename fidelity, scoped edits, structured tool calls, bounded context use, timeout recovery, unload, and detection of unintended writes.
- Do not infer coding-agent suitability from a chat, benchmark, or API coding response. Before recommending a model for coding, require sanitized evidence from a maintained coding surface's disposable-repository read, review, scoped-write, and unintended-write gates. Treat VS Code, VSCodium, their native chat surfaces, and each extension/version as separate evidence cells that need their own validation.
- Continue is a legacy, evidence-only surface. Preserve its sanitized historical records, but do not add new Continue configuration, packaging, automation, qualification runs, recommendations, or repair work unless the owner explicitly reverses this decision.
- Record every required coding gate as passed, failed, blocked, or not-run. A missing or failed gate must remain visible and must not be silently converted into a coding recommendation.
- Preparing a soak does not authorize running it. Do not download a new model, start or reconfigure hardware, or execute a newly prepared soak until the owner explicitly prompts to start that hardware-dependent test.
- Version discovery and test evidence must not change an automatic model default, selection ladder, managed runtime, or release policy without explicit owner approval.
- Never write private lab addresses, host identities, credentials, keys, or other internal infrastructure details to the repository.

## UI accessibility and compatibility lifecycle

- Treat accessibility and compatibility as design, implementation, review, packaging, update, rollback, and release requirements. They are not a one-time audit and may not be deferred merely because an individual UI change is small.
- For every new or changed user-facing element, reassess semantic structure, accessible name and description, keyboard operation, focus order and return, status announcements, non-color cues, text scaling and zoom, contrast, target size, responsive layout, reduced motion, forced colors, and background interaction while a modal surface is active.
- Keep section help tours aligned with the interface. When a tour gains or materially changes guidance, increment only that section's revision so returning users see the new guidance once. Preserve manual relaunch and never persist a partial step or user content.
- Run the novice, local-web, and real-browser accessibility checks for relevant UI changes. Run source-versus-package parity and the planned operating-system/browser/assistive-technology matrix before promotion. Automated checks do not replace the documented manual screen-reader, keyboard, zoom, and packaged-application review.
- Keep the Accessibility Statement's review date, implemented features, assessment method, contact path, and known limitations factual. Never turn a WCAG target or self-assessment into a certification claim without matching evidence.
- Treat an accessibility or supported-platform regression as a release blocker. Record the exact affected surface and configuration; do not generalize a passing configuration to other browsers, operating systems, hardware, or assistive technologies.

## README and wiki documentation lifecycle

- Maintain one canonical source for each topic. The wiki owns the full Quick Start, Home capability summary, and Glossary; `ROADMAP.md` owns roadmap detail; repository `docs/` files own contributor and engineering material. README stays concise and points to those sources instead of restating them.
- Treat README, mapped repository documentation, and the separate wiki as one coordinated user journey. Do not reorganize or rename wiki pages without auditing README, repository docs, release notes, navigation, and incoming links at the same time.
- Keep the public wiki navigation small and user-first. Detailed validation material uses generated `Eng-` pointer pages, the internal-engineering banner, and the single Engineering and Validation Index rather than appearing in the primary sidebar.
- Preserve the linear Quick Start to Using Haven 42 to Troubleshooting flow, canonical Glossary terminology, and the shared evidence-status taxonomy. Keep roadmap milestone labels explicitly distinct from evidence labels.
- Use direct, factual, human-friendly language. Remove generic filler and repeated claims, preserve technical meaning and caveats, and flag possibly outdated or inaccurate claims for owner review instead of silently rewriting the claim.
- For every mapped documentation change, run the wiki synchronization check, review both repositories for drift and private data, commit and push the wiki first when its generated content changes, and then validate and publish the main-repository change. Do not declare documentation complete while the two repositories disagree.

## Wiki voice-pass project (bucket-based rewrite, in progress)

This section covers the operational mechanics for the ongoing bucket-by-bucket wiki
rewrite. The voice standard itself is set by "README and wiki documentation lifecycle"
above — this section adds the specific safety mechanics for this multi-session project.

- Source of truth for style and progress: `WIKI-STYLE.md` and `OVERNIGHT-REVIEW.md`,
  currently in the haven-42.wiki repo. Read both before any wiki edit in this project.
  If either is missing from a repo you're working in, say so before proceeding — do not
  reconstruct their rules from memory of a prior session.
- `WIKI-STYLE.md` maintains a "Protected strings — do not reword" registry: exact
  phrases enforced by tests (`scripts/test-*.py`, `scripts/test-pack.ps1`). Never reword
  these, even by one word. If you find a test asserting on wiki text not yet in the
  registry, add it before proceeding and say so explicitly.
- Validation workflow per page: rewrite the canonical source, run
  `pwsh -NoProfile -File scripts/test-pack.ps1 -Tier Full -NoReceipt`, and compare the
  result against the known-failure baseline recorded in `OVERNIGHT-REVIEW.md` — exact
  test names and exact count, not just the same number of failures. Only stage a page
  when the result matches that baseline exactly.
- Staged-not-committed workflow: do not commit past this repository's commit hooks
  (no `--no-verify`) without a fresh, explicit, per-batch approval from the owner. A
  prior approval does not carry forward to a new batch or session.
- Hard-stop conditions specific to this project — stop the whole run and wait for
  direction rather than working around them: the known-failure baseline changes; more
  than ~15% of a batch ends up flagged; a repository safety mechanism blocks a
  validated change; a page's actual content (not wording) appears stale or conflicts
  with established policy elsewhere in this file (as with Continue, above) — flag it
  as a standalone content item, do not resolve it as a voice edit.
- When reporting progress on this project, always state plainly: pages reviewed,
  pages rewritten and validated, pages flagged and why, whether any hard-stop condition
  was hit, and what is staged/uncommitted vs. committed.
