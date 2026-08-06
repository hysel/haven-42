# Alpha Usage Report

The `Alpha Usage Report` GitHub Actions workflow provides a weekly and
manually triggered view of aggregate interest in the current Haven 42 Windows
Alpha. It does not add telemetry to Haven 42 and does not identify a downloader
or repository visitor.

The report shows:

- the cumulative download count for the exact Windows Alpha ZIP;
- cumulative counts for the separately uploaded evidence and notice assets;
- cumulative release-asset counts without requiring a stored credential; and
- an explicit unavailable status for repository clone/view traffic.

GitHub-generated source ZIP and TAR links are not release assets and therefore
do not have a separate release-asset download count. Release counts may include
repeat downloads by the same person. Repository traffic is aggregate and
short-lived; it does not identify a visitor.

The workflow runs at 07:41 UTC each Monday and can also be started manually. It
adds the Markdown report to the workflow summary and uploads matching Markdown
and JSON files for 30 days. It never commits a report to the repository. The
workflow has read-only repository contents permission, uses only SHA-pinned
GitHub-owned actions, disables checkout credential persistence, and requests no
broader credential if repository traffic is unavailable.

GitHub's traffic API requires repository `Administration: read`, but that is
not one of the permissions a workflow can grant to its built-in
`GITHUB_TOKEN`. The default workflow therefore does not collect clone or view
traffic. Enabling those optional aggregate measurements later would require a
separately approved GitHub App token or fine-grained personal access token with
that repository permission. Haven 42 does not add or request such a stored
credential now.

The generator can also be run locally without a token. Anonymous mode reports
the public release-asset counts and marks repository traffic unavailable. It
does not look for a credential in files, Git configuration, or browser state.

The machine-readable boundary is
`config/github-alpha-usage-report-contract.json`. The generator accepts only
the fixed `hysel/haven-42` repository, exact `v0.4.0-alpha.1` tag, exact primary
asset name, fixed HTTPS GitHub API origin, bounded responses, validated counts,
safe asset names, and fixed-schema aggregate output. Redirects and unsafe
output targets fail closed. Command-line report output is restricted to the
repository's ignored `dist` tree.

Official GitHub references:

- [Release and release-asset API](https://docs.github.com/en/rest/releases/releases)
- [Repository traffic API](https://docs.github.com/en/rest/metrics/traffic)
- [Scheduled workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
