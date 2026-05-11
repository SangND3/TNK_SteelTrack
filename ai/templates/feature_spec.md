# Feature spec template

Use this before starting a non-trivial feature. The spec is the bridge between "I want X" and "AI implements X without 17 clarifying questions".

A good spec saves an hour of back-and-forth. A bad spec costs a day of building the wrong thing.

```markdown
# Feature: <name>

**Status:** draft / approved / in progress / shipped
**Owner:** <who's driving this>
**Date:** YYYY-MM-DD

## Summary

<2-3 sentences. What is this, and why are we building it now?>

## Goals

What success looks like:

- <measurable or observable outcome>
- <measurable or observable outcome>

## Non-goals

What we're explicitly NOT trying to do (saves arguments later):

- <thing we won't do>
- <thing we won't do>

## User story

As a **<role>**, I want to **<action>**, so that **<outcome>**.

Add multiple stories if the feature has distinct user perspectives (e.g., end-user + admin).

## User flow

Step-by-step what the user experiences:

1. User does X
2. System responds with Y
3. User does Z
4. System persists, etc.

Include alternate paths (errors, empty states):

- If <condition>, then <behavior>
- If <condition>, then <behavior>

## UX

<Sketch / wireframe / link to design. Or describe in words:>

- **Entry points:** where in the app does the user reach this?
- **Primary action:** what's the main interaction?
- **States:** loading, empty, error, success — what does each look like?
- **Accessibility:** any specific concerns?
- **Mobile:** specific considerations?

## Data model

<Schema additions / changes:>

- New model `<Name>` with fields:
  - `field_a` — type, constraints
  - `field_b` — type, constraints, why it's needed
- Modified model `<Name>`:
  - Adding `field_c`

Migration strategy: <single / expand-migrate-contract — link to MIGRATION_RULES if non-trivial>

## API / endpoints

<HTMX endpoints needed:>

- `GET /<path>/` — <what it returns>
- `POST /<path>/` — <what it does>

<JSON API endpoints needed: none (or list)>

## Business rules

The rules that govern this feature:

- <rule that must hold>
- <rule that must hold>

Edge cases:

- <case + expected behavior>
- <case + expected behavior>

## Permissions

- Who can read / list?
- Who can create?
- Who can edit?
- Who can delete?

## Performance

- Expected request rate?
- Expected data size (rows / KB per request)?
- Budget per `PERFORMANCE_RULES.md` if different from default?

## Security

- Inputs that need validation
- Sensitive data involved
- Authorization model
- Rate limits

## Background work

- Any Celery tasks?
- Periodic jobs?
- External API calls?

## Notifications

- Should anyone get emailed / notified on what events?

## Migrations & rollout

- Feature flag? (if so, name)
- Gradual rollout? (e.g., 10% → 50% → 100%)
- Communication plan?

## Open questions

Things still TBD that block work or affect design:

- [ ] <question — who answers>
- [ ] <question — who answers>

## Decisions made

Things that *were* TBD and are now decided (with reasoning):

- **<question>** → **<decision>**, because <reason>

## Acceptance criteria

The feature is done when:

- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>
- [ ] Tests cover <areas>
- [ ] Docs updated (README / feature_map / AI_CONTEXT as appropriate)

## Out of scope (filed as follow-up)

- <thing> — issue #N
- <thing> — issue #N

## Estimate

<Rough effort: small (<1 day), medium (1-3 days), large (>3 days), epic (split into smaller features)>

## References

<Links to related ADRs, issues, design files, prior work.>
```

---

## Tips

### Write the spec before writing code

A spec written after the fact is documentation. A spec written before code is a thinking tool — it forces decisions that would otherwise come up mid-implementation.

### Use the spec as the input to AI

When asking AI to implement, paste the spec. The clearer the spec, the less back-and-forth. Specs make AI 10× more useful.

### Update the spec as decisions are made

The spec is a living document during implementation. As open questions are answered, move them from "Open questions" to "Decisions made" so the rationale is captured.

### Size your specs

A 10-page spec for a 30-minute change is wasted effort. A bullet-point sketch for a multi-week feature is asking for trouble. Match the depth to the size.

### Distinguish from a PRD

This is a *feature spec* — engineering-oriented, with data model and API. A *product requirements document* (PRD) is broader — strategy, user research, success metrics. PRDs feed into specs; specs feed into code.
