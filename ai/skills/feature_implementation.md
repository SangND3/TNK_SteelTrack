# Skill: Feature implementation

How to take a feature request from "I want X" to "merged and shipped" without drama.

## Phase 1 — Understand

1. Read the issue / requirement twice
2. Read `ai/AI_CONTEXT.md` for domain context
3. Check `ai/feature_maps/` for the relevant domain area — find existing patterns
4. Read relevant rule files (`PROJECT_RULES`, `ARCHITECTURE`, plus domain-specific)
5. Identify ambiguities

Output: list of clarifying questions, if any. Send them as a single message with options:

> "Before I plan this out, two things to clarify:
> 1. <question A — option 1 / option 2>
> 2. <question B — option 1 / option 2>"

## Phase 2 — Plan

Write a plan using the format in `ai/rules/PROJECT_RULES.md` § 4:

```
## Plan

**Goal:** <one line>

**Affected:**
- apps/<app>/models.py — add Field
- apps/<app>/services.py — add x_create
- apps/<app>/views.py — add x_create_view
- apps/<app>/urls.py — add route
- templates/<app>/create.html — new
- templates/<app>/partials/x_row.html — new
- apps/<app>/tests/test_services.py — new tests

**Approach:**
<3-6 sentences>

**Schema changes:**
- Add `xyz` column to `orders` table (nullable initially)

**Tests:**
- service: happy path
- service: validation error case
- view: HTMX renders partial, full request renders page
- view: permission check

**Risks:**
- migration on large table — see MIGRATION_RULES § zero-downtime

**Estimated scope:** medium (~3 hours)
```

Stop here. Wait for approval if:

- Schema changes
- New dependencies
- Auth/payment/permission changes
- >5 files
- Major design choice

## Phase 3 — Implement

Work bottom-up, layer by layer:

1. **Models + migration** — commit alone
   - Verify migration is reversible
   - Run `make migrate` forward + backward
2. **Services** — implement + unit tests
   - Follow `ai/examples/backend/service_example.py`
   - Commit when tests pass
3. **Selectors** — implement + unit tests
   - Follow `ai/examples/backend/selector_example.py`
4. **Forms** — implement + tests for validation
5. **Views + URLs** — implement + integration tests
   - Follow `ai/examples/backend/view_example.py`
6. **Templates** — full page + partials
   - Follow `ai/examples/frontend/htmx_form.html`
7. **JS** (if any) — minimal, vanilla, in `static/js/app.js`
8. **Celery tasks** (if any) — see `ai/examples/backend/celery_task_example.py`

After each step:

```bash
make lint
make test path=apps/<app>
```

Fix as you go. Don't accumulate broken tests across steps.

## Phase 4 — Self-review

Walk `ai/checklists/feature_checklist.md`. Don't skip items.

Key checks:

- [ ] All hard rules in `PROJECT_RULES.md` § "Hard rules" honored
- [ ] No business logic in `views.py` or `models.py`
- [ ] No N+1 (use debug toolbar to verify)
- [ ] Form errors render correctly (test with bad input)
- [ ] HTMX endpoint returns partial; non-HTMX returns full page
- [ ] Permission boundary tested (anonymous, wrong user)
- [ ] Migration reversible
- [ ] No secrets, no `print()`, no `noqa`-without-reason

## Phase 5 — PR

Use `ai/templates/pr_description.md`. Include:

- What/Why/How/Test plan
- Screenshots for UI changes
- Migration notes (if any)
- Anything skipped or deferred

Push the branch, open the PR. Wait for CI to go green before requesting review.

## Phase 6 — Address feedback

- Resolve every comment, even if just to explain "intentional because X"
- Push fixes as new commits (don't force-push during review unless asked)
- Re-request review after addressing all comments

## Phase 7 — Merge

- Squash merge
- Delete branch
- Verify the change is live (staging or production, depending on your deploy flow)
- Close the issue (auto-closed if you wrote `Closes #N`)

## Output format for the user

After Phase 4, summarize:

```
**Implemented:** <feature>

**Files changed:**
- apps/orders/models.py
- apps/orders/migrations/0042_add_archived_at.py
- apps/orders/services.py
- apps/orders/views.py
- apps/orders/urls.py
- templates/orders/list.html
- templates/orders/partials/order_row.html
- apps/orders/tests/test_services.py
- apps/orders/tests/test_views.py

**Tests added:** 7 (services: 4, views: 3)

**Test results:** ✅ all pass; coverage on changed code: 91%
**Lint:** ✅ clean
**Type-check:** ✅ clean

**Migration:** orders.0042_add_archived_at — adds nullable timestamp, reversible, no backfill

**Deferred:**
- Sort by archived_at (filed as #N+1 for follow-up)

Ready to push and open PR. Suggested PR description in PR_DESCRIPTION.md.
```
