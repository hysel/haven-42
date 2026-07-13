# Script Reference Appendix

This appendix is the long-form home for individual script documentation.

The main user experience should stay workflow- and intent-based:

- First-time setup.
- Health check.
- Model choice.
- Install or configure an agent.
- Validate model or agent behavior.
- Clean up local artifacts.
- Release readiness.

Individual script docs should remain available for advanced users, maintainers, automation authors, and troubleshooting. They should not be the primary navigation path for beginners.

## Navigation Rules

- User-facing docs should start from intent, not script name.
- Script docs should explain exact parameters, safety level, outputs, and examples.
- Workflow docs should point to the script appendix only when users need detailed command options.
- Appendix docs should preserve existing script-level documentation rather than hiding or deleting it.

## Current Reference Areas

| Reference area | Start here |
| --- | --- |
| Workflow registry and dispatcher | `docs/workflow-registry.md` |
| Beginner setup plan | `docs/beginner-setup-mode.md` |
| Hardware profile and recommendation | `docs/hardware-aware-recommendations.md` |
| Local model testing | `docs/local-agent-model-testing.md` |
| Agent CLI surface testing | `docs/agent-cli-surface-model-testing.md` |
| Evidence dashboard | `docs/evidence-dashboard.md` |
| Release packaging | `docs/release.md` |
| Cleanup and health workflows | `docs/workflow-registry.md` |

Future guided menu work should reduce how often beginners need this appendix, while keeping it complete enough for people who want direct script control.
