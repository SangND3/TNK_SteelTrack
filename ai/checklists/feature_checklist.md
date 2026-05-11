# Feature checklist

Walk this before declaring a feature done. Don't skip items "because they obviously pass" — the act of checking is the value.

## Correctness

- [ ] Does what the issue asked for, nothing more
- [ ] Edge cases handled: empty input, large input, unicode, timezone, null/None, negative numbers
- [ ] Errors are raised, logged, or returned — not swallowed
- [ ] Concurrent access considered (race conditions, locks)

## Architecture

- [ ] Business logic in `services.py`, not `views.py` or `models.py`
- [ ] Read queries in `selectors.py` or model managers
- [ ] No cross-app imports of internal models (use service interfaces)
- [ ] No new abstractions added "just in case"

## Database

- [ ] Migration committed alongside model change
- [ ] Migration reviewed (no surprise renames/extras)
- [ ] Migration reversible (`migrate <previous>` works)
- [ ] Indexes on columns used in WHERE/ORDER BY/JOIN
- [ ] No N+1 (verify with `django-debug-toolbar` or `nplusone`)
- [ ] Foreign keys have explicit `on_delete`
- [ ] If migration touches a large production table → uses `AddIndexConcurrently` or expand-migrate-contract pattern

## API / endpoints

- [ ] URL follows convention (plural, trailing slash, hyphens)
- [ ] HTTP method matches semantics (GET safe, POST mutates)
- [ ] Permission checked server-side, queryset scoped by owner
- [ ] Input validated via Form / Serializer
- [ ] HTMX request returns partial; non-HTMX returns full page
- [ ] Errors return consistent shape (JSON) or re-render form with errors (HTMX)

## Frontend

- [ ] Semantic HTML (`<button>`, `<label>`, etc.)
- [ ] Every input paired with `<label>`
- [ ] `alt` on every `<img>`
- [ ] Keyboard navigation works (Tab, Enter, Esc)
- [ ] Focus states visible
- [ ] Color contrast ≥ 4.5:1
- [ ] No info conveyed by color alone
- [ ] HTMX swaps with dynamic updates have `aria-live` where appropriate
- [ ] Works at 200% zoom

## Tests

- [ ] New behavior has tests
- [ ] Bug fixes include a regression test (fails before fix, passes after)
- [ ] Tests test behavior (inputs → outputs / side effects), not implementation
- [ ] No flaky tests added
- [ ] Test suite runs in <60s locally
- [ ] Mocks are at boundaries (external services), not internals
- [ ] Permission boundary tested (anonymous, wrong user)

## Quality

- [ ] No dead code, no commented-out code, no debug `print()`
- [ ] Names are descriptive
- [ ] Functions ≤ 30 lines (or justified)
- [ ] No magic numbers; constants named
- [ ] No `# noqa` / `# type: ignore` without inline justification
- [ ] Imports organized (stdlib / third-party / first-party / local)

## Security

- [ ] No secrets in code or commits
- [ ] User input validated and escaped
- [ ] Permissions checked on protected endpoints
- [ ] No SQL injection (parameterized queries only)
- [ ] No XSS (`|safe` only on trusted content)
- [ ] No sensitive data logged (passwords, tokens, PII)
- [ ] New env var added to `.env.example`
- [ ] New dependency vetted and justified

## Documentation

- [ ] Public APIs have docstrings
- [ ] Non-obvious code has *why* comments
- [ ] README / docs updated if behavior changed
- [ ] `ai/feature_maps/` updated if domain area changed
- [ ] `ai/AI_CONTEXT.md` updated if project state changed

## Tooling

- [ ] Ruff lint passes
- [ ] Ruff format applied
- [ ] Mypy passes (or new ignores justified)
- [ ] Pytest passes locally
- [ ] CI passes on the PR

## PR

- [ ] Branch named per convention (`feature/...`, `fix/...`, etc.)
- [ ] Commits follow Conventional Commits
- [ ] PR description includes What / Why / How / Test plan
- [ ] Screenshots for UI changes
- [ ] Migration notes for schema changes
- [ ] Anything deferred / skipped is listed

## Final

- [ ] I would be comfortable shipping this to production right now
