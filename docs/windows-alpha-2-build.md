# Windows Alpha 2 Build

This page explains how maintainers create the unsigned Windows Alpha 2 test
package. Testers do not need these commands.

Alpha 2 is a separate build. It does not replace the published Alpha 1 tag or
ZIP file, and none of these commands can publish a GitHub release.

## What changed

The ordinary Windows development build remains `0.4.0-alpha.1`. Maintainers
must explicitly request Alpha 2:

```powershell
python scripts/build-portable-development-package.py --release-line alpha2 --output dist/portable-windows-alpha2
```

That command embeds `0.4.0-alpha.2` in the executable and uses the same version
for the About screen, logs, setup receipts, network identification, build
provenance, and SBOM. The build fails if its embedded identity is missing,
unknown, or inconsistent.

The portable archive initially keeps its engineering name. Assemble the
reviewable candidate with:

```powershell
python scripts/build-windows-alpha2-candidate.py --portable-root dist/portable-windows-alpha2 --output dist/windows-alpha2-candidate
```

The resulting tester archive is:

```text
haven42-0.4.0-alpha.2-windows-x64-unsigned.zip
```

The candidate directory also contains its checksum, file and dependency
inventories, third-party notices, SBOM, runtime-component inventory, build
provenance, and a candidate manifest. The manifest explicitly says that
publication and distribution are not authorized and native validation is
still required.

## Verification

Verify the portable evidence before assembling the tester archive:

```powershell
python scripts/verify-portable-development-artifacts.py --artifact-directory dist/portable-windows-alpha2/artifacts --expected-version 0.4.0-alpha.2 --self-test
```

Then verify the assembled candidate:

```powershell
python scripts/build-windows-alpha2-candidate.py --portable-root dist/portable-windows-alpha2 --output dist/windows-alpha2-candidate --verify-only
```

A package built from uncommitted source records that fact and is not a final
release candidate. The final Windows and Linux candidates must come from the
same clean commit and must pass their own native test cells. A Windows result
cannot certify Linux, and a Linux result cannot certify Windows.

## Alpha 1 protection

The existing Alpha 1 builder, contract, release record, tag, and asset name are
unchanged. The normal Windows portable command still selects Alpha 1. The
Alpha 2 candidate manifest says `alpha1AssetsMayBeModified: false`, and the
release contract treats any Alpha 1 asset mutation as a stop condition.

Creating a candidate does not authorize publishing it. Tagging or publishing
Alpha 2 requires a separate explicit owner approval after native testing.
