# On-Demand Runtime Version Certification

Haven 42 checks runtime releases only when the owner asks for a check. It does
not silently follow `latest`, install a runtime, start a soak, or change a
managed default. Discovery is the first step of certification, not a passing
result.

The shared contract is
`config/runtime-certification-sources.json`. It currently covers official
Ollama and llama.cpp GitHub releases. A future runtime can use the same process
after its official repository, immutable tag syntax, expected release assets,
platforms, and backends are added to that reviewed allowlist.

## Run an on-demand check

From the repository root:

```powershell
python scripts/discover-runtime-certification-candidates.py `
  --output-path dist/runtime-certification/latest.json `
  --markdown-output-path dist/runtime-certification/latest.md
```

Limit the check to one runtime with `--runtime ollama` or
`--runtime llama-cpp`. The generated files stay under ignored `dist/` until a
reviewer intentionally turns exact, sanitized results into repository
evidence.

The command reads only the official GitHub release APIs declared in the
contract. It accepts a stable release only when the immutable tag, release
page, publication time, artifact names, byte lengths, SHA-256 digests, and
download URLs agree with the allowlist. Drafts, prereleases, redirects,
unexpected hosts, mutable tags, duplicate assets, missing digests, and
ambiguous profile matches fail closed.

## What the report means

`already-tracked-exact-version` means the exact upstream version is present in
`config/alpha-2-runtime-compatibility.json`. It does not mean every platform,
backend, model, or product lifecycle is certified.

`new-official-release-candidate` means the stable official release is newer
than the versions represented by that runtime's tracked collection. It remains
blocked until all required certification gates have evidence.

`blocked-required-artifact-profiles-missing` means the official release does
not currently contain every platform/backend artifact in Haven 42's reviewed
matrix. This can happen while a fresh release is still publishing assets or
when upstream stops producing one. The process reports the gap and does not
silently narrow the claimed support matrix.

The report deliberately sets these authorities to false:

- downloading a runtime or model;
- starting native, hardware, regression, or soak tests;
- writing the compatibility registry;
- changing a managed default or model/runtime binding;
- changing a support label or release policy; and
- promoting or publishing a release.

## Certification sequence

For each candidate, complete these stages in order:

1. Confirm the official release, immutable source identity, release notes,
   license, and redistribution terms.
2. Review every intended platform/backend artifact, its exact digest and size,
   archive inventory, dependencies, notices, and hostile extraction behavior.
3. After an explicit test-start prompt, run native install, start, health,
   inference, stop, cleanup, interruption, recovery, reuse, and uninstall
   checks on each claimed operating-system and hardware profile.
4. Run the shared model/task regression baseline, followed by hardware-fit
   model expansions. Record negative results; one passing GPU or model does not
   certify another.
5. Repeat the managed-setup path in source and the exact package, including
   novice flow, keyboard, screen-reader, zoom, contrast, reduced-motion,
   recovery, and removal checks.
6. Update exact evidence, known limitations, runtime/model requirements, and
   human-facing documentation without replacing earlier evidence.
7. Ask for a separate owner decision before changing the admitted runtime,
   managed default, support label, package, or release policy.

When a model needs a newer engine, Haven 42 should select the newest *admitted*
compatible version for that exact model, platform, and backend. Older admitted
versions remain compatibility fallbacks when newer releases regress. A
mutable upstream `latest` value is never an installation input.

## Offline and hostile validation

The discovery boundary can be exercised without network access:

```powershell
python scripts/test-runtime-certification-candidates.py
```

Fixture mode is intended for tests and review only:

```powershell
python scripts/discover-runtime-certification-candidates.py `
  --fixture ollama=path/to/official-release-response.json `
  --runtime ollama `
  --output-path dist/runtime-certification/fixture.json
```

Fixture evidence cannot certify a release by itself. Live official metadata,
downloaded artifact verification, native execution, and human review remain
separate requirements.
