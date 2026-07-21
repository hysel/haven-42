# Wiki Maintenance

The GitHub wiki is a separate Git repository, but its mapped content is generated from this repository. `config/wiki-sync.tsv` defines each authoritative source file, wiki filename, navigation title, and order. `config/wiki-retired-pages.txt` lists obsolete wiki pages that synchronization removes.

Do not edit mapped wiki pages directly. Edit their repository source, run synchronization, review both repositories, and commit the wiki before pushing the main repository change.

## Synchronize

Windows PowerShell:

```powershell
.\scripts\sync-wiki.ps1 -WikiPath "..\local-engineering-agent-pack.wiki"
```

Linux:

```bash
./scripts/sync-wiki.linux.sh --wiki-path ../local-engineering-agent-pack.wiki
```

macOS:

```bash
./scripts/sync-wiki.macos.sh --wiki-path ../local-engineering-agent-pack.wiki
```

The scripts copy mapped pages byte-for-byte, regenerate `_Sidebar.md`, and remove explicitly retired pages. They do not commit or push either repository.

## Check

Use `-Check` on Windows or `--check` on Linux and macOS to fail when the wiki differs from its mapped sources:

```powershell
.\scripts\sync-wiki.ps1 -WikiPath "..\local-engineering-agent-pack.wiki" -Check
```

```bash
./scripts/sync-wiki.linux.sh --wiki-path ../local-engineering-agent-pack.wiki --check
```

Hosted CI clones the public wiki and runs this check. The exact-SHA verifier requires the `Wiki synchronization` job in addition to the Windows, Linux, and macOS repository jobs.

## Change Order

1. Update authoritative repository documentation and the wiki map when needed.
2. Run the platform synchronization script.
3. Review the wiki diff and confirm it contains no private endpoints, paths, tokens, transcripts, or customer data.
4. Commit and push the wiki repository.
5. Run repository validation and tests.
6. Commit and push the main repository.
7. Verify exact-SHA hosted CI, including the wiki synchronization job.

If the wiki cannot be updated, do not present the main documentation change as complete. Record the synchronization blocker and finish both repositories before release.
