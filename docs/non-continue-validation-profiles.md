# Non-Continue Validation Profiles

Two candidate-only profiles prepare Aider and OpenCode for future read-only validation against explicitly approved public, permissively licensed repositories. They permit repository discovery, read-only review, and plan-only evaluation. They contain no executable command, provider endpoint, install action, generated configuration, model invocation, or write authority.

Targets must be immutable public commits in ignored disposable clones. Repository hooks, submodules, Git LFS smudge, dependency installation, builds, and target-provided tests stay disabled. Only sanitized summaries may be committed; raw transcripts, source content, absolute paths, and provider details stay local.

These profiles do not change either surface's current support tier, appear in the default product menu, or satisfy non-generated-repository promotion. A live run still requires separate provider availability and exact surface evidence.
