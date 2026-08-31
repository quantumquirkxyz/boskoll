# qquirk Method

The `qquirk` method is a workflow for agent-assisted project development. It is designed for repositories where work must move from ambiguous intent to reviewed delivery without losing context, widening scope, or hiding risk.

## Principles

- **Context before action.** Build a fresh context pack before broad work. Prefer repo docs, ADRs, issue tracker state, and direct code evidence over memory.
- **Questions before commitments.** Use `grill` or `grill-with-docs` when the work is ambiguous. Decisions are made with the user, not guessed.
- **Artifacts over vibes.** Specs, tickets, PR bodies, review plans, implementation notes, ADRs, and handoffs must be durable enough for another agent to consume later, and each artifact shape should belong to the skill that emits it.
- **Vertical slices over horizontal dumps.** Tickets should be narrow, complete paths through behavior, validation, and delivery.
- **Measurement before repair.** `review-pr` measures Standards and Spec separately. `plan-review-fixes` plans. `implement-review-fixes` executes. `ship-subissue` ships.
- **Branch-state before repair.** If a PR branch is conflicted, resolve that branch-state problem first with `resolving-merge-conflicts`, then return to review and repair.
- **Repo-local specialization.** Each project owns its own domain language, tracker configuration, commands, and risk boundaries.
- **Fail closed on uncertainty.** Missing fixed points, stale plans, unclear issue traceability, unresolved blockers, and skipped validation must be surfaced.

## Vocabulary

- **Context pack:** a bounded set of fresh reads and provenance that gives the next skill enough evidence to act.
- **Domain language:** the project's chosen terms, recorded in `CONTEXT.md` and ADRs.
- **Seam:** the public boundary where design, implementation, testing, or operations become explicit.
- **Tracer bullet:** a ticket that makes one narrow end-to-end behavior work.
- **Frontier:** tickets that are unblocked and claimable now.
- **Review axis:** one of the two independent review dimensions: Standards and Spec.
- **Repair plan:** a durable PR comment that converts findings into scoped, validated fixes.
- **Ship state:** the state where review is clean, validation is known, and linked work can be merged or completed.

## Canonical Flow

```text
setup-qquirk-skills
-> ask-to
-> grill-with-docs
-> to-spec
-> to-tickets
-> implement
-> publish-open-pr
-> review-pr
-> review-fix-loop when needed
-> ship-subissue after clean review
```

## Alternate Entry Points

- Use `project-development` when the project's shape or stack is not yet clear.
- Use `wayfinder` when the effort is too large or foggy for one session.
- Use `triage` when raw issues or external PRs need classification.
- Use `diagnosing-bugs` when the failure needs a tight reproduction loop.
- Use stack skills such as `nextjs`, `react`, `postgres`, `auth`, `deployment`, and `monitoring-alerting` when a specific technical surface needs sharper constraints.

## Quality Bar

A qquirk artifact is acceptable when it answers:

- What is the source of truth?
- What is in scope?
- What is explicitly out of scope?
- Who or what consumes this artifact next?
- What evidence proves it is done?
- What risk remains?

If an artifact cannot answer those questions, improve the artifact before routing it downstream.

## Operating Checks

The method is maintained by executable checks:

- `validate-skills.mjs` checks bundle parity and lock coverage.
- `audit-semantics.mjs` checks semantic drift, retired names, weak templates, links, and risk signals.
- `evaluate-scenarios.mjs` checks workflow route expectations.
- `evaluate-behavioral-fixtures.mjs` checks representative artifact shape.
- `check-all.mjs` runs the full local gate.
