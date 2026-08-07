# Style Guide

## Purpose

This style guide keeps the product, documentation, prompts, rules, agents, and
templates consistent as Haven 42 grows.

The product and its primary documentation are written first for people who are
new to local AI. Maintainer material remains precise, reviewable, and safe, but
must not make the everyday experience feel like an engineering console.

## Audience and progressive disclosure

- Assume an end user knows how to open an application and follow on-screen
  instructions, but does not know Python, Ollama, model quantization, API
  terminology, network scopes, package formats, or software supply-chain terms.
- Lead with what the user can do, what will happen, and whether anything will
  leave or change their computer.
- Put commands, identifiers, hashes, ports, protocols, evidence states, and
  implementation detail under clearly labeled **Advanced** or maintainer
  sections unless the user must act on them.
- Explain a necessary technical term the first time it appears. For example:
  “A model is the AI that reads your request and writes the response.”
- Prefer a safe recommended default. Explain alternatives only when the user
  opens an advanced control.
- Error messages state the problem, whether Haven stopped safely, and the next
  action. Do not show internal error codes in the primary UI.
- Never simplify away permission prompts, security warnings, limitations, or
  uncertainty. Translate them into plain language and keep technical detail in
  an expandable explanation or linked advanced document.

## General Writing

- Use plain technical English.
- Prefer short sections with specific headings.
- Avoid marketing language.
- Avoid claiming implemented behavior before it exists.
- State assumptions explicitly.
- Distinguish required behavior from recommended behavior.
- Use examples when they remove ambiguity.
- Prefer common words: “check” over “scan,” “available” over “admitted,” “AI
  server” over “provider,” and “this computer” over “loopback” in primary copy.
- Use the precise term in parentheses or an Advanced section when it helps
  support and troubleshooting.
- Do not use stock phrases such as “leverage,” “unlock,” “seamless,” “robust,”
  “comprehensive,” or “cutting-edge” when a concrete sentence will do.
- Avoid internal phrases such as “evidence-gated,” “capability surface,”
  “typed artifact,” “authority boundary,” and “runtime admission” in README,
  wiki, UI, and setup instructions. State what works, what does not work, and
  what the user should do next. These terms remain acceptable in security and
  maintainer documents when they have a precise defined meaning.
- Prefer active sentences with a named subject. For example, write “Haven 42
  checks the file before opening it,” not “file validation is performed.”

## Markdown Conventions

- Use `#` for the document title.
- Use `##` for primary sections.
- Use `###` only when it improves scanability.
- Use fenced code blocks for file trees, command examples, and structured snippets.
- Use bullets for unordered guidance.
- Use numbered lists for ordered workflows.
- Keep line length readable, but do not force hard wrapping.

## README Style

The README should be user-facing.

It should answer:

- What is this?
- Who is it for?
- What works today?
- How do I use it?
- Where do I go for deeper detail?

The README should not carry detailed implementation planning once that content belongs in `ROADMAP.md` or `TODO.md`.

The first screenful must help a first-time user understand the product and
find the recommended start path. Contributor and evidence links belong after
the end-user path.

## Project Documentation Style

Top-level documentation should separate concerns:

- `PROJECT.md` defines scope and intent.
- `ARCHITECTURE.md` explains structure and responsibility boundaries.
- `ROADMAP.md` explains staged delivery.
- `TODO.md` tracks tactical implementation work.
- `DECISIONS.md` records meaningful project decisions.
- `CHANGELOG.md` records released changes.
- `AI.md` guides AI assistants and contributors.

## Prompt Style

Prompt files should include:

- Purpose
- When to use
- Required context
- Process
- Output format
- Quality checks

Prompts should be task-specific. They should not duplicate full rule files.

## Rule Style

Rule files should include:

- Scope
- Required practices
- Avoid
- Review checklist, where useful

Rules should be concise and enforceable. Avoid broad advice that cannot guide a review or implementation decision.

## Agent Style

Agent files should define:

- Role
- Responsibilities
- Operating principles
- Boundaries
- Expected outputs

Agents should describe durable behavior. Task sequences belong in prompts.

## Template Style

Templates should be structured for repeatable outputs.

Prefer sections such as:

- Summary
- Context
- Findings
- Recommendations
- Risks
- Open Questions
- Next Steps

Templates should be easy to paste into issues, pull requests, architecture records, or review documents.

## Tone

- Be precise.
- Be calm.
- Be direct about risk.
- Be respectful of existing code.
- Prefer actionable guidance over abstract criticism.

## Terminology

Use consistent terms:

- "IDE tools package" for the separate Continue, Aider, and OpenCode bundle
- "agent" for a role-specific assistant definition
- "prompt" for a task-specific workflow
- "rule" for reusable engineering guidance
- "template" for structured output
- "local-first" for the default model and privacy posture
