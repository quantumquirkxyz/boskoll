# qquirk Skills Adoption Guide

Use this guide when installing this skills bundle into a new or existing project repository.

## Adoption Flow

1. Copy or sync `.agents/skills/`, `.claude/skills/`, `docs/agents/`, `docs/adr/README.md`, `CONTEXT.md`, and `skills-lock.json` into the target repo.
2. Run `setup-qquirk-skills` once in the target repo.
3. Configure `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md` for the project's real tracker and domain layout.
4. Update `CONTEXT.md` with project-specific language. Do not copy domain vocabulary from another repo.
5. Run the validation commands in this guide.
6. Start normal work through `ask-to` or the canonical feature flow.

## Required Repo Files

- `AUTHORSHIP.md` — authorship, naming, and integrity rules for the qquirk method.
- `.agents/skills/` — canonical skill definitions.
- `.claude/skills/` — compatibility symlinks to the canonical skill folders.
- `skills-lock.json` — SHA-256 hashes for every canonical `SKILL.md`.
- `docs/agents/index.md` — governance index read by work-item skills.
- `docs/agents/qquirk-method.md` — method vocabulary and quality bar.
- `docs/agents/provenance.md` — origin, redesign, and retired-name record.
- `docs/agents/work-item-format.md` — metadata shape for specs, tickets, PRs, and review comments.
- `docs/agents/skill-templates.md` — map of artifact templates owned by each skill.
- `CONTEXT.md` — repository-local domain vocabulary.

## Validation Commands

Run these from the target repo root:

```bash
node .agents/skills/platform/check-all.mjs
```

Expected result: the command returns `status: "pass"`.

## First Project Run

For a standard feature:

```text
ask-to
-> grill-with-docs
-> to-spec
-> to-tickets
-> implement
-> publish-open-pr
-> review-pr
-> review-fix-loop when needed
-> ship-subissue after a clean review
```

For a bug:

```text
ask-to
-> diagnosing-bugs
-> tdd
-> implement
-> publish-open-pr
-> review-pr
```

For operations work:

```text
release-management
-> deployment
-> observability
-> monitoring-alerting
```

## Specialization Rules

- Keep skill names stable unless the target repo has a strong reason to fork them.
- Specialize through `CONTEXT.md`, ADRs, issue tracker docs, validation commands, and stack-specific skills.
- Do not embed another repo's domain terms, branch names, issue numbers, or examples.
- Preserve `AUTHORSHIP.md`, `docs/agents/qquirk-method.md`, and `docs/agents/provenance.md` unless intentionally forking the method.
- Add new skills only when the behavior is repeatedly useful and cannot be expressed cleanly through existing skills.
- Prefer scenario fixtures under `evaluate-skill/scenarios/` before changing core workflow skills.

## Readiness Checklist

- [ ] `setup-qquirk-skills` has run or equivalent docs exist.
- [ ] `CONTEXT.md` names only this repo's domain.
- [ ] `docs/agents/issue-tracker.md` reflects the actual tracker.
- [ ] `docs/agents/triage-labels.md` matches actual label strings.
- [ ] `skills-lock.json` matches all local `SKILL.md` hashes.
- [ ] `.claude/skills` has a symlink for every canonical skill.
- [ ] Scenario evaluation passes.
- [ ] Semantic audit passes.
- [ ] Behavioral fixtures pass.
- [ ] Any real use of the bundle is captured under `case-studies/` when it changes the method.

## Maintenance Cadence

- Run `check-all.mjs` after every skill edit.
- Run `audit-semantics.mjs` before publishing the bundle when you need the detailed semantic report.
- Run `evaluate-scenarios.mjs` after changing routing, templates, or workflow skills when you need the scenario-only report.
- Add a scenario before fixing a repeated routing or artifact-quality failure.
