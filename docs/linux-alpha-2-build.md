# Linux Alpha 2 Build

This page explains how maintainers create the unsigned Linux Alpha 2 test
package. Testers do not need these commands.

The Linux package is a separate Alpha 2 candidate. It does not replace the
published Windows Alpha 1 tag or ZIP file, and none of these commands can
publish a GitHub release.

## Build the portable package

On a supported x86-64 Linux build machine, run:

```bash
python3 scripts/build-portable-development-package.py \
  --release-line alpha2 \
  --output dist/portable-linux-alpha2
```

The build records its exact source commit, operating system, architecture,
application version, package contents, dependencies, notices, and SBOM. A
modified working tree is recorded as modified and cannot become a candidate.

## Assemble the candidate

After verifying the portable evidence, assemble the candidate:

```bash
python3 scripts/verify-portable-development-artifacts.py \
  --artifact-directory dist/portable-linux-alpha2/artifacts \
  --expected-version 0.4.0-alpha.2 \
  --self-test

python3 scripts/build-linux-alpha2-candidate.py \
  --portable-root dist/portable-linux-alpha2 \
  --output dist/linux-alpha2-candidate
```

The tester archive is:

```text
haven42-0.4.0-alpha.2-linux-x64-unsigned.tar.gz
```

The candidate directory also contains a checksum, inventories, third-party
notices, SBOM, provenance, and a candidate manifest. The assembler refuses a
non-Linux host, a non-x86-64 package, a modified source tree, a version
mismatch, missing evidence, extra files, links, or a changed archive.

Verify an existing candidate without rebuilding it:

```bash
python3 scripts/build-linux-alpha2-candidate.py \
  --portable-root dist/portable-linux-alpha2 \
  --output dist/linux-alpha2-candidate \
  --verify-only
```

## What this does not prove

A valid archive is not a support claim. Each distribution still needs its own
native setup, chat, writing, summary, attachment, accessibility, uninstall,
restart, logging, and recovery evidence before its label can be promoted.
Windows results cannot certify Linux, and one Linux distribution cannot certify
another.

Creating or verifying a candidate does not authorize publishing it. Alpha 2
publication and any automatic model-default change each require separate owner
approval.
