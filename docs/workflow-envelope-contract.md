# Workflow Envelope Contract

## Purpose

`config/workflow-envelope-contract.json` defines the versioned JSON boundary between the workflow dispatchers and automation such as the planned local web UI.

The contract is additive. Existing dispatcher list, dry-run, JSON, and direct argument modes remain supported.

## Request

Schema version 1 accepts:

- `workflowId`: a stable ID from `config/workflows.json`.
- `platform`: `windows`, `linux`, or `macos`.
- `dryRun`: whether to resolve without invoking the workflow.
- `arguments`: workflow-specific string arguments.
- `requestId`: an optional caller-generated correlation value.
- `includeOutput`: an explicit opt-in for transient child output.

Windows PowerShell example:

```powershell
$request = @{
  schemaVersion = 1
  requestId = "setup-preview"
  workflowId = "validate-pack"
  platform = "windows"
  dryRun = $true
  arguments = @("-ExpectedVersion", "0.2.0")
} | ConvertTo-Json -Compress

.\scripts\invoke-workflow.ps1 -RequestJson $request
```

Linux example:

```bash
./scripts/invoke-workflow.linux.sh --request-json \
  '{"schemaVersion":1,"requestId":"setup-preview","workflowId":"validate-pack","platform":"linux","dryRun":true,"arguments":["--expected-version","0.2.0"]}'
```

## Response

Every envelope has:

- `schemaVersion`: currently `1`.
- `kind`: `workflow-execution`.
- `status`: `planned`, `succeeded`, or `failed`.
- `workflow`: sanitized registry metadata and argument count.
- `events`: ordered `accepted`, `progress`, `warning`, `result`, or `error` records.
- `result`: exit code, invocation state, dry-run state, and output-line count.

Dry runs include a `DRY_RUN` warning. Resolution and execution failures return a structured error event and a nonzero process exit code.

## Privacy Boundary

Argument values and child output are omitted from responses by default. This avoids casually echoing local paths, endpoints, or secrets into UI logs.

`includeOutput` is an explicit local-only opt-in. Raw child output may contain private machine or repository data. Do not persist or commit it without sanitization.

The envelope does not replace workflow-specific output files. Reports and artifacts remain owned by the invoked workflow.
