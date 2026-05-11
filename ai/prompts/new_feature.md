# Prompt: New feature

Use this to kick off a new feature. Fill in the blanks, paste into Claude.

---

You are a senior full-stack engineer on this project. Follow `ai/CLAUDE.md` and the relevant rule files. Use the workflow in `ai/skills/feature_implementation.md`.

## Feature

**Goal (one line):** <e.g., let users archive orders they no longer need to see>

**User story:** As a <role>, I want to <action>, so that <outcome>.

**Acceptance criteria:**

- [ ] <criterion 1>
- [ ] <criterion 2>
- [ ] <criterion 3>

**Out of scope:**

- <thing not to build now>

**Related feature_map (if any):** `ai/feature_maps/<area>.md`

## Process

Work in phases. Stop and confirm between them.

### Phase 1 — Plan

Output:

- Affected files
- Schema changes (if any) + migration approach
- Service / selector signatures
- View + URL + template changes
- HTMX interactions
- Background tasks (if any)
- Test plan
- Risks / open questions

**Stop. Wait for my approval.**

### Phase 2 — Implement

Bottom-up: models → migrations → services → selectors → forms → views → templates → tests.

After each layer, run `make lint && make test path=apps/<app>` and report.

### Phase 3 — Self-review

Walk `ai/checklists/feature_checklist.md`. Output:

- Files changed
- Tests added
- Lint / format / type-check / test results
- Anything skipped (with reason)
- Suggested PR description (using `ai/templates/pr_description.md`)
