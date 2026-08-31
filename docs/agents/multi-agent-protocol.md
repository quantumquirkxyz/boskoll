# Multi-agent Protocol

Use this protocol when more than one agent or session works on the same project.

## Rules

- One agent owns one work item at a time.
- Every handoff names the source artifact, next consumer, current status, validation evidence, and unresolved blockers.
- Do not duplicate work already claimed in the tracker.
- Do not merge review, repair, and ship responsibilities into one opaque action.
- A subagent may investigate or review, but the main agent owns final synthesis and user-facing state.

## Standard Handoffs

| Producer | Consumer | Artifact |
| --- | --- | --- |
| `grill-with-docs` | `to-spec` | clarified decisions, glossary/ADR updates |
| `to-spec` | `to-tickets` | spec issue |
| `to-tickets` | `implement` | claimable ticket |
| `implement` | `publish-open-pr` | validated issue branch |
| `review-pr` | `plan-review-fixes` | Standards and Spec findings |
| `plan-review-fixes` | `implement-review-fixes` | Review Fix Plan PR comment |
| `implement-review-fixes` | `review-pr` | implementation note and validation |
| `review-pr` | `ship-subissue` | clean review state |

## Conflict Handling

- If two agents touch the same branch or ticket, stop and reconcile ownership.
- If a plan is stale, rerun the measurement step before editing.
- If validation fails after a repair, keep the PR in review-fix-loop and do not ship.
