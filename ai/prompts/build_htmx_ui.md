# Prompt: Build HTMX UI

---

You are a senior engineer building an HTMX-driven UI. Follow `ai/rules/HTMX_RULES.md`, `ai/rules/CSS_RULES.md`, `ai/rules/ACCESSIBILITY_RULES.md`, and `ai/skills/htmx_interactions.md`.

## What to build

**Feature:** <e.g., inline edit of order title>

**Where it lives:** <page / section>

**Interaction sketch:** <describe step by step what the user does and sees>

**Existing components to reuse:** <list anything in `templates/components/` that fits>

## Process

### Phase 1 — Plan

Output:

- HTML structure (semantic elements)
- HTMX attributes on each interactive element (`hx-get`/`post`, `hx-target`, `hx-swap`)
- New endpoint(s) needed (URL, method, returns)
- Existing components used vs new components built
- Accessibility considerations (labels, focus management, aria-live)
- Loading state (`hx-indicator`)
- Error state (form errors, network error)

**Stop. Wait for approval.**

### Phase 2 — Implement

1. Backend endpoint(s) — view + URL returning the partial
2. Template partial(s) — both states (e.g., read-only + edit) with same wrapper id
3. Trigger element in the parent template
4. Component CSS via `@apply` (only if utility group repeats 3+)
5. Tests:
   - View returns partial on `request.htmx`
   - View returns full page when no HTMX header
   - Form errors render
   - Permission boundary

Reference: `ai/examples/frontend/htmx_form.html`, `ai/examples/frontend/table_partial.html`.

### Phase 3 — Manual verification

- [ ] Tab through every interactive element
- [ ] Focus states visible
- [ ] Works without JavaScript (form submits to URL, even if HTMX swap fails)
- [ ] HTMX request returns expected partial (check DevTools Network)
- [ ] No layout shift on swap
- [ ] aria-live announces dynamic updates if appropriate

### Phase 4 — Self-review

Walk `ai/checklists/frontend_checklist.md`.

### Phase 5 — Report

- Files added / changed
- Test results
- Screenshots (read-only + edit + error state) for the PR
