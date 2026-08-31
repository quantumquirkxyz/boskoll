# Skill Provenance

This document records the origin and redesign status of the skills bundle. It exists to keep the method explicit, auditable, and portable.

## Provenance Classes

- **Original qquirk:** authored in this repository for the qquirk workflow.
- **qquirk redesign:** based on an existing public or prior workflow shape, then rewritten, renamed, rerouted, or re-scoped into the qquirk system.
- **Compatibility name retained:** a stable command name kept because it is useful to users, while the surrounding behavior belongs to this bundle.
- **Retired legacy alias:** an old name intentionally removed from active routing.

## Current System

The active workflow is:

```text
setup-qquirk-skills
-> ask-to
-> grill-with-docs
-> to-spec
-> to-tickets
-> implement
-> publish-open-pr
-> review-pr
-> review-fix-loop
-> ship-subissue
```

## Retired Names

The following names are intentionally not active skills in this repository:

- `ask-matt`
- `setup-matt-pocock-skills`
- `doc-draft-pr`
- `ship-review-fix-loop`
- `frontend-development`
- `improve-codebase-architecture`

When a retired name represents useful behavior, the behavior has been routed through the active qquirk vocabulary instead.

## Active Name Decisions

- `ask-to` replaces person-branded routing with a neutral qquirk router.
- `setup-qquirk-skills` replaces repo- or person-branded setup.
- `grill` is retained as a stable shorthand for the qquirk questioning primitive.
- `grill-with-docs` is retained because it describes the useful behavior: question deeply while updating durable docs.
- `review-fix-loop` is the repair coordinator; it does not merge or close work.
- `plan-review-fixes` and `implement-review-fixes` remain separate so planning and mutation do not blur.

## Influence Policy

The bundle may be influenced by public skill patterns, GitHub workflow practices, ADR conventions, and prior repository workflows. Influence is acceptable when:

- active files are rewritten into this repository's method and vocabulary
- stale names and project-specific examples are removed
- provenance is recorded here
- validation confirms no legacy aliases remain in active routing

The point is not to hide influence. It is to turn influence into a distinct qquirk system with its own vocabulary, template ownership, and delivery flow.

## Maintenance Rule

When adding, renaming, or retiring a skill:

1. Update this provenance file.
2. Update `docs/agents/skills-map.md`.
3. Update or add scenario fixtures under `.agents/skills/evaluate-skill/scenarios/`.
4. Run `validate-skills.mjs`, `audit-semantics.mjs`, and `evaluate-scenarios.mjs`.
