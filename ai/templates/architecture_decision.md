# ADR template

Use this when you're making a decision that:

- Has multiple reasonable options
- Will be hard to reverse later
- Will surprise someone reading the code in a year ("why did they do it this way?")
- Affects more than one app / module

Examples of decisions that warrant an ADR:

- Choosing a payment provider
- Choosing a search backend (Postgres FTS vs Meilisearch vs Elasticsearch)
- Multi-tenancy approach (shared schema vs schema-per-tenant)
- Event sourcing for a specific subsystem
- Adopting a new significant dependency

Save as `ai/decisions/NNN-short-name.md` with a zero-padded number.

```markdown
# ADR NNN: <short title>

**Date:** YYYY-MM-DD
**Status:** proposed / accepted / superseded by ADR XXX / rejected
**Deciders:** <names>

## Context

<What's the situation? What problem are we solving? What forces are in play (constraints, requirements, team size, timeline, prior decisions)? 1-3 paragraphs.>

## Decision

<What did we decide? Be specific. Should be readable in isolation — someone who finds this ADR via grep should understand what was decided without reading anything else.>

## Alternatives considered

### Option A: <name>

<Description, pros, cons. Why we did NOT pick this.>

### Option B: <name>

<Description, pros, cons. Why we did NOT pick this.>

### Option C: <name> (chosen)

<Description, pros, cons. Why we picked this.>

## Consequences

### Positive

- <good thing that follows>
- <good thing that follows>

### Negative

- <cost we accept>
- <cost we accept>

### Neutral / informational

- <thing that follows but is neither good nor bad>

## Reversibility

<How hard is this to undo? What would we need to do to reverse it? When (if ever) might we want to?>

## Compliance

<What does this mean for daily work? Which rule files / examples / checklists reflect this decision?>

## References

<Links to docs, articles, prior art, conversations.>
```

---

## Tips for writing good ADRs

### Status matters

- **proposed** — being discussed, not in effect yet
- **accepted** — in effect
- **superseded by ADR XXX** — a later ADR replaces this; keep this one around for history
- **rejected** — considered and decided against (still valuable to record)

Don't delete ADRs. Mark them superseded or rejected. History is the value.

### Context, then decision

Resist the urge to lead with the decision. The decision only makes sense in context. Spend the words to set up *why* before *what*.

### Specific over general

Bad: "We use Celery for background work."
Good: "We use Celery with Redis broker, accept-IDs convention, transaction.on_commit triggering, and per-task retry policies. See § Conventions for details."

The general statement is true of every Celery project. The specifics tell you what's distinctive about ours.

### Consequences include the bad stuff

Every decision has costs. List them honestly. Future-you may forget the trade-off and try to "fix" the cost without realizing it was the price you paid for the benefit.

### Don't write an ADR for everything

ADRs are for *significant* decisions. Not "I named this function `_compute_total` instead of `calculate_total`". You'll dilute the signal if every choice gets an ADR.

A rough test: would a new contributor reading the codebase six months from now wonder why we did this? If yes, ADR. If no, just commit the code.
