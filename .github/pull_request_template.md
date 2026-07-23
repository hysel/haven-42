## Summary

Describe the user-visible and security-boundary changes.

## Security impact

- [ ] No new network, filesystem, process, credential, provider, installer, or updater authority.
- [ ] Any new authority has a threat-model delta, default-deny policy, hostile tests, and explicit promotion gate.
- [ ] Dependencies and executable artifacts use immutable reviewed identities.
- [ ] Prompts, endpoints, credentials, paths, machine identity, and raw provider output are absent from committed evidence.
- [ ] Failed or partial integrations leave documentation only.

## Verification

- [ ] Focused tests passed.
- [ ] Full cross-platform contract suite passed.
- [ ] Mapped wiki content is synchronized.
- [ ] Exact-SHA hosted jobs passed before merge.
