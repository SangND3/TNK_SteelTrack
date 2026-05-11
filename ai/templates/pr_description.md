# PR description template

Copy this when opening a PR. Fill in the sections; delete what doesn't apply.

```markdown
## What

<One paragraph: what this PR changes. Plain English. Reader skims this and knows what the PR does.>

## Why

<Why this change is needed. Link the issue if there is one. If solving a bug, link the bug report.>

Closes #<issue-number>

## How

<Approach taken — only if non-obvious. Mention any design choice that wasn't the obvious one and why.>

## Test plan

How to verify this works:

- [ ] Automated: run `make test path=apps/<app>` — N new tests added, all pass
- [ ] Manual: <steps a reviewer can follow>
- [ ] Edge cases verified: <list>

## Migrations

<Only if this PR has a migration. Delete the section otherwise.>

- **Table:** <name>
- **Operation:** <description>
- **Lock acquired:** <type, duration>
- **Estimated duration:** <time>
- **Reversible:** yes / no (reason)
- **Backfill required:** none / batched, est. <duration>
- **Deploy ordering:** single deploy / expand-migrate-contract

## Screenshots

<For UI changes. Before / after if possible. Include mobile + desktop if both affected.>

## Risks

<What could go wrong? What are you uncertain about? Where should the reviewer look hardest?>

## Notes for the reviewer

<Anything specific to call attention to: pattern to apply elsewhere, decision to discuss, follow-up items.>

## Deferred / out of scope

<Things you noticed but didn't fix in this PR (with issue numbers if filed):>

- <item>
- <item>

## Self-review

- [ ] Walked the relevant checklist (`ai/checklists/<...>.md`)
- [ ] Lint, format, type-check, test all pass
- [ ] No secrets, no debug code, no dead code
- [ ] PR is appropriately sized (< 500 lines or justified)
```

---

## Notes on writing good PR descriptions

### "What" should be a summary, not a diff dump

Reviewers can see the diff. Tell them the *story*: "Adds an inline-edit form for order titles, accessible from the order list and detail page."

Not: "Modified `OrderForm`, added `OrderInlineForm`, updated `OrderListView.get_queryset()`..."

### "Why" matters more than "what"

Future-you reading the git log six months from now will want to know *why*. The code shows what.

### "Test plan" must be specific

Bad: "Tested locally."
Good: "Created an order, clicked edit, changed title to '...', verified new title appears in list and detail. Tried with empty title and verified error. Logged in as another user and verified I can't edit their order."

### Keep risks honest

Underplaying risk to avoid scrutiny is how outages happen. Reviewers can help most when they know where to look.

### Size matters

A 1500-line PR doesn't get reviewed carefully. If you can't split it, justify clearly why not.
