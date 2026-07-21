# Typed Artifact Contract

`config/typed-artifact-contract.json` defines result shapes shared by general-purpose capabilities and engineering workflow routing.

Every persisted result must identify its schema version, artifact type, status, creation time, source capability, content, and material policy effects. The initial types are chat messages, Markdown documents, images, engineering reports, configuration plans, and repository-change reviews.

## Write Boundary

Capability routing does not create an artifact and never authorizes a write. Before writing an artifact, the execution layer must:

1. Resolve an available provider or workflow.
2. Select a repository-optional session workspace or user-approved destination.
3. Disclose the exact output location.
4. Disclose local versus external execution, repository reads, file writes, network access, downloads, and approval requirements.
5. Obtain approval when the capability or resolved provider requires it.
6. Return a typed result with failure or blocked status instead of fabricating an output path.

Raw local paths, endpoints, prompts, credentials, and provider output remain local. Only sanitized evidence may enter the repository or wiki.

## Engineering Boundary

An engineering report or repository-change review does not replace the workflow evidence contract. Approved-write readiness remains keyed by agent surface, version, provider, model, operating system, operation, and validation mode.
