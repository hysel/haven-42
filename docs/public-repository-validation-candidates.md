# Public Repository Validation Candidates

The approved read-only candidate set covers a Python CLI library, a Node web framework, and a Rust CLI application at immutable tagged commits. Each entry binds the repository, annotated tag object, peeled commit, permissive license expression, and exact license-file SHA-256.

Local inspection uses ignored bare clones only. It never checks out a working tree, follows submodules, permits symlinks, runs hooks, installs packages, builds code, runs target tests, invokes a model, or accepts lazy network fetches during validation. The committed validator reports only public candidate identity, aggregate tree counts, extension counts, and exact license evidence; it records no local path or source content.

An initial ripgrep candidate was rejected without checkout because its tagged tree contains a symbolic link. The rule was not relaxed; serde_json replaced it in the passing candidate set.

This static inspection does not satisfy Aider or OpenCode non-generated-repository promotion. A future live surface run still requires the explicit provider, surface version, model, operating system, read-only behavior, sanitized evidence, and external verification gates.
