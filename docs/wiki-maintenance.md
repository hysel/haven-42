# Wiki Maintenance

The GitHub wiki is a separate Git repository, but this repository generates its mapped content. `config/wiki-sync.tsv` defines every authoritative source file and wiki filename. `config/wiki-navigation.tsv` independently defines the small, grouped, end-user-first sidebar. Repository files remain canonical for engineering material; synchronized `Eng-` pages contain a banner and a source link instead of copying the complete document. The Engineering and Validation Index keeps those records reachable without crowding the primary navigation. `config/wiki-retired-pages.txt` lists obsolete wiki pages that synchronization removes.

Do not edit mapped wiki pages directly. Edit their repository source, synchronize, review both repositories, and commit the wiki before pushing the main repository change.

Evidence-record pages are generated rather than edited individually. Change
`config/evidence-catalog.tsv`, run
`python scripts/generate-evidence-wiki-pages.py`, and then synchronize the
wiki. `python scripts/generate-evidence-wiki-pages.py --check` verifies that
the page set, index, wiki mappings, and future-update evidence registry all
match the catalog.

## Writing style

Public wiki pages use a practical technical field-guide voice:

- Lead with the problem the page solves and the shortest safe answer.
- Name the exact operating system, hardware, runtime, version, backend, model
  artifact, and task whenever a result depends on them.
- Separate observed results from inference, recommendation, and roadmap work.
- Keep failures, unsupported routes, and missing gates visible; do not turn a
  successful startup or one prompt into a compatibility claim.
- Explain unfamiliar terms where they first appear and link to the Glossary.
- Prefer compact tables for repeated exact-profile comparisons and numbered
  steps for procedures. Do not use tables merely to decorate prose.
- State what a command or setting proves before showing it, and state the
  expected result afterward.
- Keep user pages direct and readable. Move raw manifests, hashes, harness
  internals, and exhaustive logs behind the Engineering and Validation Index.
- Do not imitate a personality, use promotional filler, or hide uncertainty
  behind vague terms such as “supported” or “works.”

README remains a concise entry point, the wiki owns the full user journey, and
repository `docs/` files own engineering detail. A rewrite must preserve those
canonical boundaries rather than duplicating the same explanation everywhere.

## Synchronize

Windows PowerShell:

```powershell
.\scripts\sync-wiki.ps1 -WikiPath "..\haven-42.wiki"
```

Linux:

```bash
./scripts/sync-wiki.linux.sh --wiki-path ../haven-42.wiki
```

macOS:

```bash
./scripts/sync-wiki.macos.sh --wiki-path ../haven-42.wiki
```

The scripts copy user pages from their mapped sources, render each `Eng-` page as a labeled canonical-source pointer, regenerate `_Sidebar.md` from the explicit navigation allowlist, and remove explicitly retired pages. They require exactly one level-one heading, paired code fences, resolvable internal links on user pages, and HTML-free line spacing on short user-facing pages. A navigation entry must reference a mapped page, and duplicate or path-like destination names fail closed. The scripts do not commit or push either repository.

## Check

Use `-Check` on Windows or `--check` on Linux and macOS to fail when the wiki differs from its mapped sources:

```powershell
.\scripts\sync-wiki.ps1 -WikiPath "..\haven-42.wiki" -Check
```

```bash
./scripts/sync-wiki.linux.sh --wiki-path ../haven-42.wiki --check
```

Hosted CI clones the public wiki and runs this check. It retries three times
with a fast-forward pull to tolerate short GitHub propagation delay, but never
updates or accepts drift. The exact-SHA verifier requires the
`Wiki synchronization` job in addition to the Windows, Linux, macOS, and
portable-package jobs.

## Change Order

1. Update authoritative repository documentation and the wiki map when needed.
   Update the separate navigation map only when a page belongs in the short
   public sidebar; mapping a detailed page does not make it primary navigation.
2. Run the platform synchronization script.
3. Review the wiki diff and confirm it contains no private endpoints, paths, tokens, transcripts, or customer data.
4. Commit and push the wiki repository; wait for the push to complete.
5. Run repository validation and tests.
6. Stage the complete main-repository change, run Full to create the exact
   staged-tree receipt, then commit and push without further content edits.
7. Verify exact-SHA hosted CI, including the wiki synchronization job.

If the wiki cannot be updated, do not present the main documentation change as complete. Record the synchronization blocker and finish both repositories before release.
