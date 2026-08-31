# Agent Skills Index

This repo uses the repository-local qquirk Skills bundle in `.agents/skills/`. This index is the operating map for the bundle and the first stop for any work-item or review flow.

## Work item flow

- `work-item-router` reads this index first before any spec, ticket, project board, or publication flow.
- `triage` uses the same index when classifying issues and PRs into durable states.
- `to-spec` and `to-tickets` use the issue tracker configuration and canonical work-item format documented here.
- `review-pr`, `plan-review-fixes`, `implement-review-fixes`, `publish-open-pr`, and `ship-subissue` preserve the same metadata contract.
- If a PR branch is conflicted while review or repair is in progress, branch-state resolution belongs to `resolving-merge-conflicts` before review or shipping resumes.

## Configuration docs

- [qquirk method](qquirk-method.md)
- [Provenance](provenance.md)
- [Issue tracker](issue-tracker.md)
- [Work item format](work-item-format.md)
- [Domain docs](domain.md)
- [Triage labels](triage-labels.md)
- [Skills map](skills-map.md)
- [Skill templates](skill-templates.md)
- [Adoption guide](adoption-guide.md)
- [Stack matrix](stack-matrix.md)
- [Skill style guide](skill-style-guide.md)
- [Release checklist](release-checklist.md)
- [Multi-agent protocol](multi-agent-protocol.md)
- [Provenance inventory](provenance-inventory.md)
