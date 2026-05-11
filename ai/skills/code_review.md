# Skill: Code review

How to review code as a senior engineer. Direct, useful, kind.

## Goal

Catch issues before merge. Teach when appropriate. Don't bikeshed.

Order of priority:

1. **Correctness** — does it work? Edge cases?
2. **Security** — auth, input, secrets
3. **Architecture** — does it fit the project conventions?
4. **Readability** — will future-you understand this?
5. **Style** — formatter handles this; don't comment on it

## Process

1. **Read the PR description.** What is this supposed to do? Why?
2. **Read the test plan.** How was it verified?
3. **Read the tests.** They show what behavior is locked in.
4. **Read the diff.** Top to bottom. Form a mental model.
5. **Read the diff again.** Now look for issues.
6. **Group feedback by severity.** Write the comments.
7. **Issue verdict:** Approve / Request changes / Discuss.

## What to look for

### Correctness

- Does the code do what the PR says?
- Edge cases: empty input, null, very large, unicode, timezone, concurrent access
- Errors handled? Not swallowed?
- Off-by-one errors
- Boundary conditions

### Security

- New endpoint: permission check?
- New input: validated?
- New SQL: parameterized?
- New file upload: type / size validated?
- New env var: documented in `.env.example`?
- New dependency: vetted? necessary?
- Logging sensitive data?

See `ai/checklists/security_checklist.md`.

### Architecture

- Business logic in `services.py`, not `views.py` or `models.py`?
- Read queries in `selectors.py`?
- N+1 in any new query?
- Migration reversible?
- Long-running migration handled per `MIGRATION_RULES`?
- Cross-app imports through services, not internal models?

### Tests

- New behavior has tests?
- Bug fix has a regression test?
- Tests test behavior, not implementation?
- No flaky tests added?
- Coverage gate passes?

### Readability

- Names descriptive?
- Functions ≤ 30 lines?
- Comments explain *why*, not *what*?
- No dead code, no debug prints?

### Style

- Linter passes? (CI handles it; only comment if your project's linter has gaps)
- Don't quibble over things the formatter could decide

## Severity levels

When commenting, label severity:

- **Blocker** — must fix before merge
- **Major** — should fix, but could be follow-up if isolated
- **Minor** — nice to fix; reviewer's preference
- **Nit** — really minor; OK to ignore

```
[Blocker] This endpoint doesn't check ownership — any logged-in user can delete any order.

[Major] This will N+1 for users with many orders. Add `select_related("user")`.

[Minor] Consider extracting this 40-line function into smaller helpers; harder to test as one block.

[Nit] `result` is a vague name here; maybe `validated_items`?
```

## How to phrase feedback

- **Be direct.** Vague is unkind.
- **Suggest a fix** when you can — saves a round trip.
- **Explain the why** for non-obvious feedback — teaches.
- **Frame as questions** for opinions, statements for objective issues.

Examples:

Direct + helpful:

> "[Major] This service writes to the DB then makes an HTTP call inside `transaction.atomic`. If the HTTP call hangs, the transaction holds locks. Move the HTTP call to a Celery task triggered via `transaction.on_commit`."

Vague:

> "Hmm, this seems off."

Better:

> "[Question] Why call out to Stripe inside the transaction? See `BACKEND_RULES.md` § services."

## Bikeshedding to avoid

- Variable naming when both names are reasonable
- Code style the formatter handles
- "I'd write it differently" without a concrete benefit
- Preferences masquerading as conventions

## Verdict

- **Approve** — no blockers, minor nits acceptable
- **Request changes** — list blockers
- **Discuss** — design concern that needs conversation before code change

Don't approve "with comments" if you have blockers. Either it's mergeable or it's not.

## Special cases

### Big PR

If the PR is 500+ lines:

1. Request the author split it if possible
2. If they can't, take it in chunks: review one file/area at a time, leave incremental comments
3. Don't approve until you've seen all of it

### Drive-by refactor mixed with feature

Comment: "This refactor is good but should be its own PR. Can you revert this part here and open a separate PR?"

### Unfamiliar area

If you don't understand the code, that's information:

1. Ask the author to explain it (in PR comments)
2. If still unclear, either pair with them or defer to someone who knows the area
3. If neither, *don't* approve — your stamp would be meaningless

### You wrote the code (solo review)

Reviewing your own code is hard but valuable. Tactics:

- Take a break before review (an hour minimum)
- Read the diff in GitHub's UI, not your editor
- Pretend you're someone who doesn't know what you intended
- Use the same checklist you'd use for someone else's code
- Look harder at the boring parts — that's where bugs hide

## Anti-patterns

- ❌ Approve everything to avoid friction
- ❌ Request changes over trivial style points
- ❌ Hold a PR hostage to your personal preferences
- ❌ "LGTM 👍" without actually reviewing
- ❌ Long delays without communication
- ❌ Tear apart the code in front of a wider audience (DM the author for sensitive points)
