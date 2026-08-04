# Local Image Runtime License And Redistribution Review

## Decision Boundary

Haven 42 does not redistribute, install, or package external image-provider
software. ComfyUI runtimes and models remain separately acquired, independently
versioned software. This review inventories exact upstream portable archives
without executing or importing their code. It supports compatibility and
security assessment; it is not legal advice, permission to ship those archives,
or a path for adding them to Haven packages.

The governing contract is `config/local-image-runtime-license-contract.json`. The offline auditor is `scripts/audit-local-image-runtime.py`. It requires a contracted profile and archive SHA-256, refuses links and reparse points, bounds traversal and reads, writes only a new caller-selected report, records no absolute path or machine identity, and never turns metadata into automatic license clearance.

## Exact Profile Status

| Profile | Exact portable | Audit status | Redistribution status |
| --- | --- | --- | --- |
| Windows AMD / ROCm | ComfyUI v0.30.0, SHA-256 `0f3816fa1149e5a739e4d095d7733bc4ea28b02c8872fadeb8f73b933b141568` | Exact retained archive and extracted runtime audited | External by policy; redistribution remains blocked |
| Windows Intel / XPU | ComfyUI v0.30.0, SHA-256 `3fc6b62317c8aae50f43296762929a3808615ae891900587218d00234d366135` | Exact retained archive and extracted runtime audited | External by policy; redistribution remains blocked |
| Windows NVIDIA / CUDA | ComfyUI v0.30.0, SHA-256 `f4353d069dd7342e3bef421f07f003cca53ca84168102705cfc83f66449f5ae5` | Exact retained archive and extracted runtime audited | External by policy; redistribution remains blocked |

No result in this table changes the promoted Linux ComfyUI connection profile or grants download, installer, updater, package, or runtime authority. License findings cannot block Haven's core package merely because the external provider was evaluated, but they continue to prohibit Haven from redistributing the affected provider archive.

## Windows AMD v0.30.0 Inventory

The retained official archive independently matched its contracted digest before the extracted tree was inspected. The offline scan covered 62,021 regular files, 104 Python distributions, 168 license-like files, and 448 native `.dll`, `.exe`, `.pyd`, or `.sys` files totaling 3,634,965,975 bytes. Every native artifact received a size and SHA-256 record in ignored local evidence.

The exact result remains `review-required` for three reasons:

- `comfyui_frontend_package`, `rocm`, `rocm-sdk-core`, and `rocm-sdk-libraries-custom` do not provide usable license metadata in their installed distribution records.
- `comfy-aimdo` lacks usable metadata but carries an exact packaged GPLv3 license file. Its recorded SHA-256 is bound to a narrow reviewed override, so the missing-metadata blocker is resolved for that exact version and file only. Redistribution review remains required.
- Nineteen distributions do not carry license evidence beneath their own `.dist-info` directory. Some may have related material elsewhere in the archive, but association and completeness require manual reconciliation.
- The 448 native files require file-by-file mapping to their originating component, exact source or binary terms, required notices, and any non-copyright obligations. Python package metadata alone cannot clear them.

The apparent `packaging` duplication was resolved without deleting anything: 26.2 is the top-level distribution, while 26.0 is an independently recorded vendored copy beneath `setuptools`. The inventory now records installation scope and does not collapse vendored and top-level components.

The audit mapped 417 native files to 49 installed distributions through their wheel `RECORD` entries and verified every available recorded SHA-256. The remaining 31 belong to the contracted CPython 3.12.10 embedded-runtime boundary. No native file is ownerless and no recorded native hash mismatches, but component license reconciliation remains open.

The sanitized audit was also transformed into deterministic ignored candidate evidence: a dependency/license inventory, exact native-file inventory, CycloneDX 1.6 SBOM, candidate third-party notice, and digest-bound review summary. Hostile tests require the input archive to have been independently verified, reject unsafe paths and malformed hashes or overrides, require reviewed license records to match an exact packaged license digest, refuse output replacement, and reject any true installation, packaging, redistribution, or promotion authority. These files organize review; they remain explicitly unsuitable for distribution.

## Windows Intel And NVIDIA v0.30.0 Inventories

Fresh physical-host audits on 2026-08-04 independently reverified each
contracted archive before scanning its matching extraction. The Intel/XPU
inventory covered 59,089 regular files, 121 Python distributions, and 449
native files. The NVIDIA/CUDA inventory covered 56,611 regular files, 101
Python distributions, and 380 native files. Both scans completed without an
ownerless-native-file blocker after the auditor learned the two exact
contracted embedded-runtime root shapes.

Both results remain `review-required` for the same three fail-closed reasons:
missing distribution license evidence, missing or unusable license metadata,
and exact native-component review. Each scan produced an ignored,
candidate-only dependency/license inventory, native-file inventory,
CycloneDX 1.6 SBOM, third-party-notice candidate, and review summary. Neither
result authorizes packaging, redistribution, installation, promotion, or
runtime execution.

ROCm is licensed per component, and AMD explicitly warns that components can include third-party code under additional terms. The general ROCm documentation license is therefore not a blanket redistribution grant for the portable runtime. See the [official ROCm component-license index](https://rocm.docs.amd.com/en/develop/about/license.html) and [Windows HIP SDK documentation](https://rocm.docs.amd.com/projects/install-on-windows/en/latest/).

ComfyUI itself is [GPL-3.0](https://github.com/comfy-org/ComfyUI). PyTorch uses a BSD-style license whose binary redistribution conditions require preserving its notices; its bundled third-party material must also be reconciled from the exact archive. See the [official PyTorch license](https://github.com/pytorch/pytorch/blob/main/LICENSE).

## Model Is A Separate Gate

The SDXL checkpoint is not covered by the runtime audit. Its exact tested revision uses the CreativeML Open RAIL++-M license, including notice, downstream-use, redistribution, and use-restriction obligations. Runtime clearance cannot imply model clearance, and Haven 42 must not bundle the checkpoint until the exact revision and required user-facing terms are separately approved. See the [exact tested SDXL revision](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/tree/f298da3c058bd8f1f1c62f3ecfa775244a243897).

## Remaining Clearance Gates

Each Windows profile must independently complete all of the following before any runtime files can ship:

1. Verify the exact official archive byte size and SHA-256, then run the offline audit against the matching extracted tree.
2. Resolve every missing, ambiguous, classifier-only, and duplicate Python distribution record against immutable upstream license evidence.
3. Map every native artifact digest to its originating component and exact version. For NVIDIA, match CUDA files to the exact CUDA EULA Attachment A; the display driver is not an application redistributable. For AMD and Intel, use each component's own terms rather than a suite-level summary.
4. Assemble complete license texts, copyright notices, source-offer or source-delivery obligations, and third-party notices for the exact proposed package.
5. Review codec, patent, trademark, export, model-use, and other non-copyright obligations where applicable.
6. Generate package inventory, third-party notices, and SBOM from the exact final bytes, and fail on any unmatched file or changed digest.
7. Repeat vulnerability, malware, source-versus-package parity, clean-host install, update, rollback, idle shutdown, cleanup, and uninstall gates on the exact candidate.
8. Obtain an explicit human redistribution decision. The audit cannot make that decision and defaults every authority field to false.

The NVIDIA review must use the [exact CUDA 13.0 EULA](https://docs.nvidia.com/cuda/archive/13.0.0/pdf/EULA.pdf), whose Attachment A identifies redistributable files and whose codec section leaves additional third-party rights to the distributor. Intel components must likewise be reconciled individually; the archived [Intel Extension for PyTorch repository](https://github.com/intel/intel-extension-for-pytorch) declares Apache-2.0 for that project but does not by itself license every native binary in a portable archive.

## Local Evidence Handling

Raw reports remain beneath ignored `dist/local-review/` storage. They can contain thousands of dependency filenames and hashes and are not committed. A committed summary may record exact public artifact identities, aggregate counts, blockers, and decisions, but must never include a machine path, account, hostname, endpoint, prompt, generated image, or private output.

## Prepared Windows Audit Commands

Run these only on the matching Windows machine after independently verifying
the official archive. Replace each angle-bracket placeholder with a local path;
keep the report under ignored review storage and use a new output directory.
The commands inventory bytes only and do not import or execute the provider.

Intel XPU:

```powershell
python scripts/audit-local-image-runtime.py --runtime <extracted-runtime> --archive <official-archive> --profile windows-intel-comfyui-0.30.0 --artifact-sha256 3fc6b62317c8aae50f43296762929a3808615ae891900587218d00234d366135 --output <new-audit-report.json>
python scripts/build-local-image-runtime-review-evidence.py --audit-report <new-audit-report.json> --output-directory <new-evidence-directory>
```

NVIDIA CUDA:

```powershell
python scripts/audit-local-image-runtime.py --runtime <extracted-runtime> --archive <official-archive> --profile windows-nvidia-comfyui-0.30.0 --artifact-sha256 f4353d069dd7342e3bef421f07f003cca53ca84168102705cfc83f66449f5ae5 --output <new-audit-report.json>
python scripts/build-local-image-runtime-review-evidence.py --audit-report <new-audit-report.json> --output-directory <new-evidence-directory>
```

Both profiles remain blocked regardless of audit outcome until every exact
license, native-component, model, vulnerability, package-parity, lifecycle,
and human redistribution gate passes.
