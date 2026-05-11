# Skill: Incident analysis

How to handle a production incident, and how to write the postmortem afterward.

## Phase 1 — Stabilize (in the moment)

Goal: stop the bleeding. Understanding can wait.

1. **Acknowledge.** Reply in the channel: "Looking into it, ETA X minutes."
2. **Triage.** What's broken? Who's affected? How bad?
3. **Stabilize.** The fastest safe action:
   - Roll back the recent deploy (if recent deploy correlates)
   - Disable the feature flag (if there's one)
   - Failover to backup (if applicable)
   - Scale up (if capacity issue)
4. **Communicate.** Update status page / channel every 15-30 min.
5. **Don't multi-task.** Pick one root-cause hypothesis at a time.

What NOT to do during an incident:

- Don't optimize while debugging — fix forward
- Don't refactor — apply the smallest patch
- Don't blame in channel — that's for the postmortem
- Don't lose evidence — copy logs / screenshots before they rotate out

## Phase 2 — Investigate (after stable)

Once the bleeding has stopped:

1. **Verify it's actually fixed** — check error rate stays down for 30+ min
2. **Preserve evidence:**
   - Logs (specific time range)
   - Sentry issue links
   - Metrics graphs
   - Screenshots
   - Git diff of the change that broke things (if known)
3. **Root cause:** dig until you find *why*, not just *what*. See `ai/skills/debugging.md`.

## Phase 3 — Postmortem (within 48 hours)

Write a blameless postmortem. Use `ai/templates/architecture_decision.md` adapted — or this template:

```markdown
# Postmortem: <short title>

**Date:** YYYY-MM-DD
**Authors:** <names>
**Status:** draft / final
**Severity:** S1 (outage) / S2 (degraded) / S3 (minor)

## Summary

<2-3 sentences: what happened, who was affected, how long.>

## Impact

- Users affected: <number / percentage>
- Duration: <start> to <end> (<duration>)
- What broke: <user-visible description>
- Data loss: <yes/no, what>
- Revenue impact: <if applicable>

## Timeline

All times in <timezone>.

- HH:MM — Deployed version X
- HH:MM — Error rate started climbing on `/orders/`
- HH:MM — On-call paged via Sentry alert
- HH:MM — Identified deploy correlation
- HH:MM — Rolled back to version X-1
- HH:MM — Error rate normalized
- HH:MM — Customer comms sent
- HH:MM — Incident closed

## Root cause

<the why, in 2-5 paragraphs. Be specific. Include code snippets if relevant.>

## What went well

- <thing 1>
- <thing 2>

## What went poorly

- <thing 1>
- <thing 2>

## Where we got lucky

- <thing 1 — sometimes a near-miss reveals more than the actual bug>

## Action items

| # | Action | Owner | Due | Severity |
|---|--------|-------|-----|----------|
| 1 | <action> | <name> | <date> | high |
| 2 | <action> | <name> | <date> | medium |

Action items must be:
- Specific (not "improve testing")
- Assigned (a name, not a team)
- Dated
- Tracked (file as issues)

## Detection

- How did we find out? <alert / user report / chance>
- How fast? <time from incident start to detection>
- How can we detect faster? <action item>

## Mitigation

- How did we fix it? <action>
- How fast? <time from detection to resolution>
- How can we mitigate faster? <action item>

## Prevention

- How can we prevent this class of bug? <action items>
```

## Blameless

The postmortem focuses on systems and processes, not people. "X deployed a bug" is wrong framing. "Our deploy process allowed a change without a regression test for case Y, and our staging didn't catch it because Z" is right.

Reasons:

- The person who broke production is already feeling bad; piling on doesn't help and discourages future ownership
- Bugs are systemic; blaming individuals doesn't fix the system
- A culture of blame leads to hiding mistakes, which is much worse than fixing them publicly

## Severities

- **S1 (outage):** site down, payments broken, data loss/leak. Drop everything.
- **S2 (degraded):** major feature broken, latency >10× normal, error rate >5%
- **S3 (minor):** small feature broken, one customer affected, easy workaround exists

S1 + S2 get postmortems. S3 might just need a bug fix + note.

## Patterns

### Bad deploy

Action items usually include:

- Better test coverage for the broken path
- Staging environment closer to production
- Canary or gradual rollout
- Faster rollback mechanism

### Capacity / scale

- Better monitoring of headroom
- Load test before traffic events
- Auto-scaling rules
- Rate limiting

### Data corruption

- Better input validation
- Better DB constraints
- Backup verification
- Disaster recovery drill

### External dependency

- Timeouts everywhere
- Circuit breakers
- Fallback paths
- Graceful degradation

## Common mistakes

- ❌ Postmortem with no action items (then nothing changes)
- ❌ Action items with no owner / due date (they don't happen)
- ❌ "Pay more attention" as an action item (not actionable)
- ❌ Burying the postmortem (publish it; lessons spread)
- ❌ Skipping the postmortem because "we know what happened" (writing it surfaces things you missed)

## After the postmortem

- Share with the team
- Track action items to completion
- Reference in future incidents ("we had a similar thing in incident-2026-04-15")
- Use to update `AI_CONTEXT.md` or relevant rule files if it reveals a project-wide gap
