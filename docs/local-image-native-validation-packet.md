# Local Image Native Validation Packet

This packet prepares later native Windows AMD, NVIDIA, and Intel runs. It does
not authorize a download, installation, provider launch, or machine change.
Each run must use the exact candidate profile manifest, a non-administrator
account, ignored disposable storage, and the existing source and unsigned
portable package from the same reviewed commit.

## Preflight

1. Record only sanitized OS, architecture, accelerator, driver/runtime, and
   available VRAM evidence.
2. Select exactly one matching profile from
   `config/local-image-candidate-profiles.json`; reject a mismatch or unknown
   value and never fall back to CPU.
3. Recompute every provider archive and checkpoint digest before extraction.
4. Verify adequate destination and temporary space using the recorded profile
   budget. Do not borrow evidence from another operating system or accelerator.
5. Show the exact single-use effect disclosure before any permitted network,
   write, process, retention, cleanup, update, or rollback action.

## Source And Package Cells

Run the same fixed workflow against source and the unsigned portable package.
For each cell verify loopback-only binding, exact provider/process identity,
accelerator use, typed metadata-free PNG output, bounded cancellation,
provider-history cleanup, exact-process shutdown, and endpoint closure. The
package must not read the repository or contain a provider runtime, checkpoint,
generated image, or installer payload. Image bytes need not match because the
generation runtime may be nondeterministic; policy fields must match exactly.

## Lifecycle Cells

Exercise occupied-port rejection without terminating the foreign listener,
startup timeout, invalid workflow, active cancellation, provider crash and
fresh-identity recovery, stale PID/process-reuse rejection, automatic idle
shutdown, exact update/rollback selection, retention choices, and exact-file
uninstall cleanup. Preserve user data unless the user separately selects the
bounded delete option.

## Result Boundary

Keep each profile `partial-pass-unpromoted` until its exact native source and
package cells pass and licensing/redistribution approval exists. Commit only
sanitized summaries: no endpoint, account, host, path, PID, prompt, image,
provider log, archive, runtime, model, or machine-specific identifier.
