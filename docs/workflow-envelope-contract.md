# Workflow Envelope Contract

## Purpose

`config/workflow-envelope-contract.json` defines the versioned JSON exchanged between workflow dispatchers and automation such as the planned local web UI.

The contract adds an automation interface without replacing the existing dispatcher list, dry-run, JSON, or direct argument modes.

## Request

Schema version 1 accepts these fields:

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
  arguments = @("-ExpectedVersion", "0.3.0")
} | ConvertTo-Json -Compress

.\scripts\invoke-workflow.ps1 -RequestJson $request
```

Linux example:

```bash
./scripts/invoke-workflow.linux.sh --request-json \
  '{"schemaVersion":1,"requestId":"setup-preview","workflowId":"validate-pack","platform":"linux","dryRun":true,"arguments":["--expected-version","0.3.0"]}'
```

## Response

Every response envelope includes:

- `schemaVersion`: currently `1`.
- `kind`: `workflow-execution`.
- `status`: `planned`, `succeeded`, or `failed`.
- `workflow`: sanitized registry metadata and argument count.
- `events`: ordered `accepted`, `progress`, `warning`, `result`, or `error` records.
- `result`: exit code, invocation state, dry-run state, and output-line count.

Dry runs include a `DRY_RUN` warning. Resolution and execution failures return a structured error event and a nonzero process exit code.

## Privacy Boundary

Responses omit argument values and child output by default so local paths, endpoints, or secrets do not spill into UI logs.

`includeOutput` is an explicit local-only opt-in. Raw child output may contain private machine or repository data. Do not persist or commit it without sanitization.

The envelope does not replace workflow-specific output files. The invoked workflow still owns its reports and artifacts.
