# Hardware-Aware Recommendation Validation

## Scenario

A private application-style repository was used to validate the hardware-aware recommendation flow end to end. Repository name, local paths, endpoint, and raw profile details are intentionally omitted.

## Date

2026-07-07

## Scope

Validated steps:

1. Installed the pack into a target repository using the default installer profile.
2. Confirmed existing target `.continue` content was backed up before replacement.
3. Reused an existing sanitized remote model profile JSON.
4. Generated a hardware-aware recommendation JSON.
5. Applied the recommendation into target `.continue/config.local.yaml`.
6. Verified the generated local config contains WRITE SAFE, PLAN ONLY, and DEEP REVIEW lanes.
7. Verified only WRITE SAFE includes `edit` and `apply` roles.
8. Ran Ollama API-level Agent model preflight against the recommended model.
9. Confirmed the pack repository remained clean after runtime outputs were written under ignored output paths.

## Result

| Check | Result |
| --- | --- |
| Pack install dry run | Pass |
| Pack install with backup | Pass |
| Recommendation generation | Pass |
| Local-only config generation | Pass |
| WRITE SAFE lane generated | Pass |
| PLAN ONLY lane generated | Pass |
| DEEP REVIEW lane generated | Pass |
| Local endpoint kept local-only | Pass |
| Ollama API model preflight | Pass |
| Failure signal | none |

## Recommended Model

`qwen3.5:9b` was selected for WRITE SAFE, PLAN ONLY, and DEEP REVIEW lanes for this validation run because it is the current approved-write-ready model in the evidence catalog and fit the available hardware profile.

## Boundary

This validation proves the script-level flow and Ollama API preflight. It does not replace editor-side Continue validation.

Remaining manual checks:

- Open the target repository in Continue.
- Confirm the generated model lanes appear.
- Run read-only repository discovery.
- Run the approved-write smoke test.
- Verify the changed file externally with shell and git status.

## Privacy

The evidence excludes:

- Private repository name
- Local absolute paths
- Private endpoint
- Raw hardware profile
- Raw model transcripts
- Usernames or hostnames
