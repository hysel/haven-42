# Wiki Maintenance

The GitHub wiki is a separate Git repository, but its mapped content is generated from this repository. `config/wiki-sync.tsv` defines every authoritative source file and wiki filename. `config/wiki-navigation.tsv` defines the small, grouped, end-user-first sidebar independently. Detailed engineering pages remain mapped and reachable through the Documentation Index without crowding the primary navigation. `config/wiki-retired-pages.txt` lists obsolete wiki pages that synchronization removes.

Do not edit mapped wiki pages directly. Edit their repository source, run synchronization, review both repositories, and commit the wiki before pushing the main repository change.

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

The scripts copy mapped pages byte-for-byte, regenerate `_Sidebar.md` from the explicit navigation allowlist, and remove explicitly retired pages. They require exactly one level-one heading, paired code fences, resolvable internal links, and HTML-free line spacing on the short user-facing pages. A navigation entry must reference a mapped page, and duplicate or path-like destination names fail closed. The scripts do not commit or push either repository.

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
