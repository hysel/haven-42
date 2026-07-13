# Sample Scenario Packs

`config/sample-scenario-packs.json` maps common local-AI coding tasks to the prompts, agents, workflows, sample repository types, and evidence that should be used before trusting a recommendation.

The current scenario packs are:

| Scenario | Default posture |
| --- | --- |
| Legacy migration | Plan first |
| Config refactoring | Dry-run first |
| Bug fixing | Scoped edit |
| Security review | Review-only by default |
| Test generation | Scoped edit |
| Documentation cleanup | Review then edit |

Each scenario keeps three boundaries explicit:

- Prompts and agents must exist in `.continue/`.
- Workflow IDs must exist in `config/workflows.json`.
- Evidence references must point to committed docs or examples.

Use these packs as starting lanes for the future starter-toolkit UI. They do not promote a model, agent surface, or workflow to approved-write status by themselves.
