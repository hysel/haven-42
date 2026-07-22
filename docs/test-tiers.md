# Test Tiers And Exact-Tree Receipts

Haven 42 separates routine checks from integration-heavy validation while keeping the full cross-platform GitHub gate authoritative.

## Tiers

| Tier | Purpose | Typical contents |
| --- | --- | --- |
| `Fast` | Short local feedback while editing. | Schemas, required files, documentation contracts, safety invariants, and static workflow checks. |
| `Integration` | Exercise scripts that create disposable files or invoke child processes. | Installers, sample repositories, configuration generation, routing, artifacts, packaging plans, and wiki synchronization. |
| `Full` | Release and push confidence. | Every Fast and Integration check with per-test timing. This remains the GitHub Actions tier. |

Windows:

```powershell
.\scripts\test-pack.ps1 -Tier Fast
.\scripts\test-pack.ps1 -Tier Integration
.\scripts\test-pack.ps1 -Tier Full
```

Linux or macOS:

```bash
./scripts/test-pack.linux.sh --tier fast
./scripts/test-pack.linux.sh --tier integration
./scripts/test-pack.linux.sh --tier full
```

The full suite includes repository validation, so callers should not run `validate-pack` immediately before `test-pack` unless they intentionally want an isolated validation result.

## Timing

Each selected test reports elapsed time. The final summary records the selected tier, executed count, skipped count, and total duration. Use this output to move expensive tests into Integration or remove repeated process and fixture setup; do not weaken assertions merely to reduce time.

## Exact-Tree Receipt

A successful Full run on a clean Git working tree writes `haven-42-test-receipt-v1` inside the repository's private `.git` directory. It records the exact commit and Git tree, tier, schema, and runner. It is not committed or included in release packages.

The pre-push hook skips its duplicate local Full run only when:

- the working tree is clean;
- the receipt schema and tier match;
- both the receipt commit and tree exactly match `HEAD`.

Any edit, new commit, missing receipt, partial tier, or failed test causes the pre-push hook to run the Full suite. GitHub Actions always runs Full independently and never trusts a local receipt.

Use `-NoReceipt` or `--no-receipt` for ephemeral runners and hosted CI.

## Live Tests

Model servers, agent surfaces, ComfyUI, and hardware validation remain separate explicit workflows. A Full pack test does not contact Ollama or another model provider unless a future test is deliberately classified and disclosed as live. Before every live phase, state whether the configured Ollama server is required.
