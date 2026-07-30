# PDF Production Isolation Assessment

Status: assessment complete; production isolation is not satisfied.

The review-only PDF worker proves that bounded parsing can fail closed against
the synthetic corpus on Windows and Ubuntu Linux. It does not prove that the
worker is safe to expose to arbitrary user documents. Python API replacement,
resource limits, timeouts, output ceilings, and process-count limits reduce
risk but do not replace operating-system capability isolation.

## Required common boundary

A future admitted worker must receive document bytes rather than a path, parse
one document in one disposable process, run without network or filesystem-write
authority, create no temporary file or child process, and terminate its entire
process tree on timeout, crash, or cancellation. CPU, memory, wall-time,
input/output, object, expansion, and nesting limits must be enforced outside
the parser. Every packaged worker and dependency file must have an exact
inventory and SHA-256 identity.

## Platform gaps

- Windows currently assigns a suspended worker to a one-process Job Object
  before execution. Production still requires a restricted token,
  AppContainer-equivalent capability boundary, OS-enforced network denial,
  explicit filesystem denial, and packaged process-tree evidence.
- Linux currently applies POSIX resource ceilings and parent termination.
  Production still requires `no_new_privs`, network/user/mount/PID namespace
  isolation or an equivalent, a seccomp-equivalent syscall policy, a
  Landlock-equivalent filesystem policy, and packaged cgroup/process-tree
  evidence.
- macOS has no native source evidence yet. A physical Mac must validate an
  OS-supported sandbox policy, network/filesystem denial, process-tree
  termination, resource limits, and the packaged worker.

No fallback may silently weaken these controls. If a required platform control
is unavailable, PDF parsing must remain unavailable.

## Non-synthetic corpus boundary

Metadata-only research considered the
[PDF Association corpora index](https://github.com/pdf-association/pdf-corpora),
[Mozilla PDF.js](https://github.com/mozilla/pdf.js), and
[pypdf](https://github.com/py-pdf/pypdf). Repository-level licensing does not
automatically establish the origin, redistribution rights, privacy status, or
integrity of every linked PDF. No document was selected, downloaded, opened,
parsed, or retained.

Future intake requires an immutable source revision, HTTPS source and artifact
identity, SHA-256 before opening, explicit per-artifact redistribution
permission, privacy and malware review, a bounded hostile category, and a
manual ignored-quarantine decision. Known live malware and repository
retention remain prohibited.

## Admission status

Windows and Ubuntu Linux source review cells passed. macOS source and every
packaged cell remain false. `pypdf` is not installed, imported by the
application, included in a package, or exposed through a route or UI. This
assessment grants no production-readiness, signing, or release authority.
