# August 2026 coding-agent qualification

This engineering screen asks a narrower question than the general model
campaign: can an exact local-model artifact follow repository instructions
safely enough to remain a coding-agent candidate?

It does not certify an editor extension or make a model an automatic default.

## What was tested

Each model first had to produce the expected structured API response and tool
arguments. Continue CLI 1.5.47 then exercised a generated, disposable Python
repository in four independent phases:

1. read the repository and produce a filename-accurate implementation plan;
2. review a known defect without editing files;
3. make an approved write and pass external Git/content checks; and
4. change exactly two approved files and no others.

Models were unloaded between cells. Raw prompts, responses, private endpoints,
host identities, and disposable paths are not retained in this record.

## Exact profile

| Part | Bound value |
| --- | --- |
| Model runtime | Ollama 0.32.13 |
| Model host | Ubuntu 24.04.4, CUDA, two Tesla V100 32 GiB cards |
| Agent surface | Continue CLI 1.5.47 on Windows |
| Repository | Generated disposable Python API fixture |

## Lower-memory AMD profile

Qwen 3.5 4B was repeated on a separate Ubuntu 26.04 system with an AMD Radeon
RX 5700 XT and 8 GiB of VRAM. The exact `qwen3.5:4b` GGUF artifact was
Q4_K_M, 4.7B parameters, and 3,139,667,229 bytes. Ollama reported all
3,139,667,229 bytes resident in GPU memory while the test was active.

The structured API/tool test and all four Continue CLI phases passed on this
profile. This confirms that the RX 5700 XT is sufficient for this exact
lower-memory coding workflow. It does not extend the result to larger models,
other quantizations, other AMD GPUs, or an editor UI. The downloaded model was
removed after the run.

### Coding reliability follow-up

A separate 30.2-minute coding reliability run completed 26 full Continue CLI
workflows without failure: 26 repository reads, 26 defect reviews, 26 approved
writes, and 26 two-file scoped edits. Three transport-level cancellation and
recovery probes also passed. The run recorded 29 full-GPU-residency checks and
30 unload checks. Minimum available system memory was 118,994.29 MiB and peak
reported GPU-memory use was 3,841.54 MiB.

This closes the bounded coding-workflow soak for this exact profile. It does
not claim Haven's internal cancellation UI, runtime restart, interrupted
download, simulated low-resource, sleep/wake, concurrent-load, blind human
review, or editor-extension gates. Those remain separately testable cells.

### VS Code Continue 2.1.0 follow-up

The same exact model and runtime were exercised through Continue 2.1.0 in a
VS Code-compatible 1.127.0 Windows editor against a generated disposable
Python repository. Continue used repository tools without exposing raw tool
markup. Its first read omitted the test contents, but a focused follow-up read
reported the exact existing assertion. No tracked file changed during the
read-only phase.

The approved write proposed the correct changes to exactly `app/main.py` and
`tests/test_main.py`. Continue applied the test change but remained stuck while
applying the application change. The stuck action was cancelled and a bounded
one-file recovery request applied the remaining correct change. External Git
verification found exactly the two approved files, and the resulting test
passed. The exact model was unloaded after the run.

This is a partial editor-surface pass with successful bounded recovery, not a
clean apply pass. Accelerator residency was not sampled during the editor
request, even though the same exact RX 5700 XT profile had already passed the
separate full-residency CLI workflow and coding soak. VSCodium and native-chat
cells remain unrun, and this test is not a blind human-quality review.

A controlled repeat then started from the same clean fixture with Microsoft
Python 2026.4.0 installed before VS Code opened. Continue read both requested
files, attempted two Agent tool actions, reported that its edit tool was not
available, and supplied manual code instead. It then claimed both files had
been modified. External Git verification found zero tracked changes. The
retest therefore failed the editor write gate without an unintended write.

The Python extension did not resolve the problem and should not be treated as
the cause of the first patch hang. The two runs instead show inconsistent
Continue 2.1.0 edit-tool availability or patch application on this exact
surface. A language extension can improve diagnostics and test discovery, but
it is not a substitute for a reliable editor agent tool contract.

### VSCodium Continue 2.1.0 comparison

The same clean fixture, model, runtime, prompt, Continue version, and Python
extension were then tested in VSCodium 1.126.04524. Continue read both exact
files but both Agent edit actions failed. It returned correct replacement code
as plain code blocks. Selecting Apply on that fallback produced `Could not
resolve filepath to apply changes`; no editor file was active and the fallback
blocks carried no usable target binding. External Git verification found zero
tracked changes and no unintended writes.

This is a failed VSCodium Agent write cell. The fallback Apply error is
secondary evidence and must not be mistaken for a successful scoped edit. An
active-file recovery can be evaluated separately, but it cannot retroactively
turn this run into a clean Agent pass.

### VS Code active-file recovery retest

A subsequent VS Code retest first exposed a stale unsaved editor buffer, which
was reverted before evidence collection. With `app/main.py` explicitly active,
Continue 2.1.0 then applied the exact requested single-file change. External Git
verification found one intended tracked-file edit and no unintended writes.
The existing test failed because the controlled prompt explicitly prohibited
editing `tests/test_main.py`; that expected mismatch is not an Apply failure.
This is evidence that explicit active-file binding can recover a scoped edit,
but it does not erase the separate multi-file tool failures or establish a
reliable general editor-agent workflow.

### VS Code explicit two-file retest

From a clean baseline, both approved files were explicitly attached to the
Continue Agent prompt. Continue read both files, attempted two Agent edit
actions, and reported that its edit tool was unavailable. External Git
verification found that neither approved file changed. Instead, Continue wrote
the requested test function into `app/settings.py`, which the prompt explicitly
placed out of scope. The unchanged baseline test still passed and therefore did
not detect this misplaced code.

This is a failed multi-file editor cell with an unintended write. Correct
fallback text and a passing baseline test cannot override the external scope
violation. VS Code plus Continue 2.1.0 must not be recommended for approved
multi-file edits on this evidence.

## Results

“Workflow passed” means all five columns passed on this exact generated fixture.
It is not production coding-agent admission.

| Exact model | API/tool | Read | Review | Write | Scoped edit | Workflow |
| --- | --- | --- | --- | --- | --- | --- |
| `qwen3.8:27b` | Pass | Pass | Pass | Pass | Pass | **Pass** |
| `north-mini-code-1.0:q4_K_M` | Pass | Pass | Pass | Pass | Pass | **Pass** |
| `granite4.1:30b` | Pass | Pass | Pass | Fail | Pass | Fail |
| `ornith:9b` | Pass | Pass | Fail | Pass | Pass | Fail |
| `qwen3.6:27b-q4_K_M` | Pass | Fail | Pass | Pass | Pass | Fail |
| `qwen3.6:35b-a3b-q4_K_M` | Pass | Pass | Pass | Pass | Pass | **Pass** |
| `nemotron-3.5-lightning:30b-a3b-q4_K_M` | Pass | Fail | Pass | Pass | Pass | Fail |
| `nemotron-3.5-lightning:30b-a3b-q8_0` | Pass | Pass | Fail | Pass | Pass | Fail |
| `nemotron3:33b` | Pass | Pass | Pass | Fail | Fail | Fail |
| `qwen3.5:0.8b` | Pass | Fail | Fail | Fail | Fail | Fail |
| `qwen3.5:2b` | Pass | Fail | Fail | Pass | Pass | Fail |
| `qwen3.5:4b` | Pass | Pass | Pass | Pass | Pass | **Pass** |
| `gemma3:1b-it-q4_K_M` | Fail | Fail | Fail | Fail | Fail | Fail |
| `ministral-3:3b-instruct-2512-q4_K_M` | Pass | Fail | Pass | Pass | Pass | Fail |
| `ministral-3:8b-instruct-2512-q4_K_M` | Pass | Pass | Pass | Fail | Pass | Fail |
| `lfm2.5:8b` | Fail | Pass | Fail | Fail | Fail | Fail |
| `minicpm-v4.6:1b` | Pass | Fail | Fail | Fail | Fail | Fail |
| `muse-glimmer:30b` | Pass | Pass | Pass | Pass | Pass | **Pass** |

## What the evidence suggests

- Qwen 3.5 4B is the most interesting lower-memory candidate from this screen.
- Qwen 3.5 4B also passed the same generated-repository workflow while fully
  resident on an 8 GiB Radeon RX 5700 XT.
- Qwen 3.6 35B-A3B, Qwen 3.8 27B, and North Mini Code 30B-A3B
  remain strong high-memory candidates.
- Muse Glimmer passed this coding workflow even though its earlier general
  Writing and Summarization gate failed. It may be useful for coding-specific
  work, but the conflicting evidence must remain visible.
- North Mini Code passed the repository workflow even though an earlier narrow
  coding JSON-format contract failed. That earlier result is not erased; the
  two tests measure different behavior.
- Quantization changed failure behavior for Nemotron 3.5 Lightning, so Q4 and
  Q8 cannot inherit one another's result.

## What remains open

No model is admitted as production coding-agent-ready from these runs. The RX
5700 XT Qwen 3.5 4B profile passed its bounded coding soak and a VS Code
Continue 2.1.0 editor cell with bounded patch recovery, but the full
eight-scenario reliability contract is not complete. Blind human code review
has not run, the identical VS Code retest failed because the edit tool was
unavailable, and the VSCodium comparison failed its Agent edit and fallback
filepath-resolution gates. Native-chat cells remain separate `not-run` cells.
Real-project edits and security benchmarking also remain outside this
generated-fixture result.

No automatic default, support label, runtime version, or release policy was
changed.
