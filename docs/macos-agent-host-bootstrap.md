# macOS Setup And Qualification Boundary

This page separates the future Haven 42 end-user experience from maintainer
qualification work. They deliberately have different prerequisites.

## End users

The intended macOS setup is a self-contained, signed, notarized Haven 42
application. A person should not need to install Homebrew, Python, pip, a
compiler, or a command-line model tool. Haven 42 should:

1. inspect the Mac only after the person approves the readiness check;
2. explain the exact app-owned folder, runtime, model, download size, and free
   space requirement in plain language;
3. offer a reviewed, version-pinned runtime and hardware-fit model;
4. download only after explicit approval, verify the artifact before use, and
   keep recoverable partial downloads inside the app-owned folder;
5. bind local services to IPv4 loopback, show progress and recovery in the UI,
   and open Chat automatically after successful setup;
6. provide visible update, rollback, model removal, and complete uninstall
   controls without requiring Terminal.

When a person connects to Ollama on another computer, macOS displays its
system **Local Network** permission prompt. The app bundle provides a factual
usage description: Haven 42 connects only to the AI-server address the person
entered and does not scan for nearby devices. Same-computer loopback use does
not require private-LAN authority. If the person declines, Haven 42 must keep
working for loopback use, explain that the private-network connection was not
allowed, and point to **System Settings → Privacy & Security → Local Network**
for recovery. The application must never treat this operating-system grant as
permission to discover servers or contact a different address.

The current unsigned development package proves that the Haven 42 executable
can run without a Python installation on the destination Mac. It is not a
public macOS release: Apple Developer signing, notarization, clean-machine
installation, interactive accessibility review, and complete managed-runtime
update/rollback evidence remain required.

The repository also contains a bounded development-only wrapper that places
that exact embedded runtime in a conventional `Haven 42.app` Finder layout.
Its builder and independent verifier require a fixed bundle identifier, valid
numeric macOS bundle versions, an exact file inventory, archive parity, and
checksums. This improves the novice development-test path; it does not turn the
unsigned app into an installer or a public release. Physical app launch,
package parity, accessibility, Gatekeeper, signing, notarization, update,
rollback, and uninstall results remain separate evidence cells.

The packaged real-browser receipt records bounded attachment behavior,
automated accessibility checks, and the local privacy boundary as named gates
in addition to its aggregate check count. A count by itself is not accepted as
proof of those behaviors. Manual screen-reader, keyboard, zoom,
reduced-motion, and physical clipboard review remain separate open gates.

Ollama is the current beginner runtime candidate because its official macOS app
is signed and notarized and its Metal path works on Apple Silicon. Haven 42 must
still pin and verify the exact admitted artifact; it must not run a moving
remote installer or silently substitute a newer release.

MLX remains an advanced candidate. Direct native inference can be efficient,
but the tested `mlx_lm.server` describes itself as unsuitable for production,
has no API-key option, and has fragile local-model discovery. Do not expose it
to a network or make it the novice setup path until Haven 42 supplies and tests
an authenticated local boundary and a self-contained signed runtime.

## Maintainers and qualification hosts

Maintainers may use a separate isolated environment to build and test the
package. The discovery helper is read-only:

```bash
./scripts/bootstrap-macos-agent-host.sh
```

Its `--install`, `--with-ollama`, and `--with-mlx` flags intentionally refuse
to act. Haven 42 does not execute moving Homebrew bootstrap sources or
unresolved Python dependency trees. Install maintainer prerequisites through a
reviewed user-managed process, then rerun discovery and retain only sanitized
version and readiness evidence.

Copy a qualification source tree as one checksum-bound archive, extract it to
a new directory, and do not synchronize individual files into that directory
while a test pack or package build is running. Bind modified development
sources to the archive SHA-256 as well as the base commit. A test that observes
a partially updated tree is invalid even when a later retry passes; retain the
failed receipt for diagnosis and rerun from a fresh atomic extraction.

The current Apple-Silicon model plan is
`config/alpha-2-apple-silicon-16gib-qualification-plan.json`. It binds exact
Ollama tags and manifests to the reviewed inventory, requires IPv4 loopback,
unloads after each cell, removes only models pulled by that run, and grants no
automatic selection, default, support, or release authority. Run its offline
tests before any physical-Mac execution:

```bash
python3 scripts/test-alpha2-macos-model-qualification.py
```

The live runner is maintainer-only and requires the owner's explicit hardware
test approval:

```bash
python3 scripts/alpha2-macos-model-qualification.py \
  --pull-missing \
  --remove-new-models \
  --output /an/isolated/results/apple-silicon-model-qualification.json
```

The output is sanitized: it retains no prompts, responses, private addresses,
usernames, machine identifiers, or paths. Provider-level coding checks are
only a screen. A coding recommendation still requires the same model, runtime,
hardware, maintained editor or CLI surface, and surface version to pass the
disposable-repository read, review, scoped-write, external-diff, recovery, and
unintended-write gates.

Validate a completed result before retaining or publishing it:

```bash
python3 scripts/validate-alpha2-macos-model-qualification-result.py \
  /an/isolated/results/apple-silicon-model-qualification.json
```

The validator fails closed on stale plan or inventory bindings, missing cells,
inconsistent pass states, incomplete temporary-model cleanup, retained model
text, private addresses, user paths, and accidental recommendation authority.

The current physical-M4 result and its plain-language boundaries are recorded
in `config/alpha-2-apple-m4-16gib-model-qualification-result.json` and
`examples/apple-m4-16gib-model-qualification.md`. Nine of 16 exact artifacts
passed the bounded endpoint contract and all nine then passed their independent
30-minute soaks. OpenCode 1.18.19 completed all 16 coding screens but produced
no passing recommendation candidate. The native full suite, representative
power cells, runtime comparisons, and development-app tests are recorded
separately. None of this grants automatic-selection authority.

`config/alpha-2-apple-m4-qualification-status.json` is the fail-closed status
ledger for the complete physical-Mac program. It binds the current sanitized
evidence files by SHA-256, keeps every unfinished gate visible, and grants no
default, support, runtime, update, or release authority.

Model-bound power sampling is a separate maintainer cell. It requires the
reviewed root-owned restricted powermetrics helper and records only a compact
CPU/GPU/ANE summary while an exact model is generating:

```bash
python3 scripts/alpha2-macos-model-power-cell.py qwen35-4b-q4 \
  --pull-missing \
  --remove-new-model \
  --output /an/isolated/results/apple-silicon-model-power.json
```

Collect the idle comparison only when Ollama reports no loaded models:

```bash
python3 scripts/alpha2-macos-idle-power-cell.py \
  --output /an/isolated/results/apple-silicon-idle-power.json
```

Both result types require independent validation before cataloging:

```bash
python3 scripts/validate-alpha2-macos-power-result.py \
  /an/isolated/results/apple-silicon-idle-power.json
python3 scripts/validate-alpha2-macos-power-result.py \
  /an/isolated/results/apple-silicon-model-power.json
```

The validator binds the exact plan, runtime, hardware profile, and model
artifact; checks sample completeness and ordering; requires positive bounded
work and Metal residency for model cells; checks unload and temporary-model
cleanup; and rejects retained raw telemetry, identity, or promotion authority.

These figures are Apple SoC estimates. They are not wall-outlet power, total
system energy, or an electricity-cost measurement. Zero observed ANE power
means only that ANE use was not observed in that exact cell.

Core-pass candidates can then enter the standard 30-minute-per-artifact
reliability gate. The runner checkpoints after every model, handles termination
by unloading the current model, and can resume only when its plan and core
qualification bindings are unchanged:

```bash
python3 scripts/alpha2-macos-model-soak.py \
  /an/isolated/results/apple-silicon-model-qualification.json \
  --pull-missing \
  --remove-new-models \
  --resume \
  --output /an/isolated/results/apple-silicon-model-soak.json
```

Only core-pass artifacts enter this soak. A failed task, full-Metal-residency,
unload, duration, or temporary-model-cleanup gate remains failed; elapsed time
does not convert it into a pass.

Validate the final soak before using it as evidence:

```bash
python3 scripts/validate-alpha2-macos-model-soak-result.py \
  /an/isolated/results/apple-silicon-model-soak.json \
  --qualification-result /an/isolated/results/apple-silicon-model-qualification.json
```

The validator requires the exact core-pass candidate set in its original
order, 30 minutes of measured work for every passing cell, positive cycle and
token measurements, full temporary-model cleanup, unchanged plan/runtime
bindings, and the privacy and no-promotion fields. A partial checkpoint is not
a completed result.

## Coding surfaces

Continue CLI and the Continue extensions for VS Code and VSCodium are legacy,
evidence-only surfaces. Preserve their sanitized historical records, but do
not generate new configuration, repair work, qualification runs, or
recommendations from them.

New coding evidence belongs to maintained, version-pinned surfaces such as VS
Code Native Chat with the official Ollama provider or a separately admitted
CLI agent. Evidence never transfers between a CLI, VS Code, VSCodium, native
chat, or an extension version.

The physical-M4 qualification uses the exact OpenCode 1.18.19 macOS arm64
binary in a disposable generated Python repository. It runs every executable
candidate from the Apple plan, not only the models that passed the general
task gate. The runner records deterministic structured code, exact and unknown
tool behavior, repository read/plan/review, approved two-file edits, external
Git verification, unintended writes, a forced timeout and recovery, and model
unload. It checkpoints after each model and resumes only against the same
plan, core result, policy, hardware, runtime, and surface artifact:

```bash
python3 scripts/alpha2-macos-opencode-coding-screen.py \
  /an/isolated/results/apple-silicon-model-qualification.json \
  --opencode /an/isolated/tools/opencode \
  --opencode-archive /an/isolated/tools/opencode-darwin-arm64.zip \
  --fixture runtime-validation-output/sample-repositories/python-api \
  --pull-missing \
  --remove-new-models \
  --resume \
  --output /an/isolated/results/apple-silicon-opencode-coding.json
```

Validate the sanitized result independently before cataloging it:

```bash
python3 scripts/validate-alpha2-macos-opencode-coding-result.py \
  /an/isolated/results/apple-silicon-opencode-coding.json \
  --qualification-result /an/isolated/results/apple-silicon-model-qualification.json
```

The runner uses raw surface events only in memory. The retained result contains
gate statuses, durations, digests, cleanup proofs, and failure codes—not raw
prompts, responses, tool events, repository paths, user identity, or endpoint
details. A passing exact cell remains only eligible for later human review; it
does not change a default, support label, runtime, or release policy.

## Runtime comparison cells

Ollama evidence does not transfer to MLX or llama.cpp. Run each comparison
against an offline, digest-bound runtime and model artifact, then validate its
sanitized result independently. The MLX cell requires an isolated Python
environment plus manifests that bind every installed wheel and every local
model file:

```bash
python3 scripts/alpha2-macos-mlx-lifecycle.py \
  --python /an/isolated/mlx/bin/python \
  --model-directory /an/isolated/models/qwen35-4b-mlx \
  --model-manifest /an/isolated/manifests/mlx-model.json \
  --wheel-manifest /an/isolated/manifests/mlx-wheels.json \
  --output /an/isolated/results/apple-silicon-mlx-lifecycle.json
python3 scripts/validate-alpha2-macos-mlx-lifecycle-result.py \
  /an/isolated/results/apple-silicon-mlx-lifecycle.json
```

The llama.cpp cell requires the exact native server binary, GGUF file, commit,
and SHA-256 values reviewed for that run:

```bash
python3 scripts/alpha2-macos-llamacpp-lifecycle.py \
  --server /an/isolated/llama.cpp/llama-server \
  --model /an/isolated/models/model.gguf \
  --runtime-commit REVIEWED_COMMIT \
  --expected-server-sha256 REVIEWED_SERVER_SHA256 \
  --expected-model-sha256 REVIEWED_MODEL_SHA256 \
  --output /an/isolated/results/apple-silicon-llamacpp-lifecycle.json
python3 scripts/validate-alpha2-macos-llamacpp-lifecycle-result.py \
  /an/isolated/results/apple-silicon-llamacpp-lifecycle.json
```

These cells prove only their exact native lifecycle, acceleration, recovery,
and cleanup boundaries. They do not inherit Ollama task or coding results and
do not admit a beginner runtime, self-contained package, or public release.

After every input validates, build the fail-closed program ledger. Include the
existing medium-model power record as well as the new idle, small, and large
cells so no retained evidence silently disappears:

```bash
python3 scripts/summarize-alpha2-apple-m4-qualification.py \
  --plan config/alpha-2-apple-silicon-16gib-qualification-plan.json \
  --core config/alpha-2-apple-m4-16gib-model-qualification-result.json \
  --soak config/alpha-2-apple-m4-16gib-model-soak-result.json \
  --coding config/alpha-2-apple-m4-16gib-opencode-1.18.19-coding-result.json \
  --coding-policy config/model-coding-agent-qualification-policy-apple-m4-opencode-1.18.19.json \
  --native-tests config/alpha-2-apple-m4-native-test-result.json \
  --idle-power config/alpha-2-apple-m4-idle-power-result.json \
  --small-power config/alpha-2-apple-m4-qwen35-2b-power-result.json \
  --medium-power config/alpha-2-apple-m4-qwen35-4b-power-result.json \
  --large-power config/alpha-2-apple-m4-ministral3-8b-power-result.json \
  --package config/alpha-2-apple-m4-development-app-result.json \
  --keychain config/alpha-2-apple-m4-keychain-lifecycle-result.json \
  --mlx config/alpha-2-apple-m4-mlx-0.31.3-lifecycle-result.json \
  --llamacpp config/alpha-2-apple-m4-llamacpp-b10520-lifecycle-result.json \
  --output config/alpha-2-apple-m4-qualification-status.json \
  --replace
```

The ledger remains `in-progress` until its explicitly open signing,
notarization, interactive accessibility, Keychain, update, rollback, and
uninstall cells are satisfied. Aggregation never grants product authority.
The frozen coding-policy input is required because a later policy revision
must not be used to reinterpret evidence collected under an earlier contract.

## Security and accessibility gates

- Runtime and model listeners stay on `127.0.0.1` unless a separately reviewed
  authenticated and encrypted private-network design is approved.
- Keychain operations require an interactive packaged-app test. A successful
  API-availability probe or an SSH session does not prove real credential
  storage, lock handling, or access-control behavior.
- `scripts/alpha2-macos-keychain-lifecycle.py` may exercise only a fixed
  synthetic validation item after explicit owner approval. It refuses a
  pre-existing item, generates secrets in memory, bounds each system command,
  performs create/read/update/delete/absence checks, and attempts cleanup in a
  `finally` path. An unattended denial is recorded as `blocked`; it is not
  converted into Keychain, encrypted-history, package, or production
  admission.
- Every setup and update flow needs keyboard, screen-reader, focus, contrast,
  zoom, reduced-motion, forced-colors, and error-recovery review in the source
  UI and packaged app.
- Apple signing and notarization evidence applies only to the exact artifact
  tested. An ad-hoc-signed upstream binary is not a novice-ready component.
- Private host identity, network details, credentials, raw prompts, and raw
  responses never belong in repository evidence.

Historical MLX and Continue observations remain in
`examples/mlx-model-validation.md`. They do not grant current support or coding
admission.
