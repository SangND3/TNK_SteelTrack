# Prompt: Write tests

---

You are a senior engineer adding tests. Follow `ai/rules/TESTING_RULES.md` and `ai/skills/test_writing.md`.

## What needs tests

<target — file / function / feature>

**Context:** <why now — adding tests to a previously untested area, bug fix, new feature, coverage gap>

## Process

### Phase 1 — Map the surface

For the target area, list:

- Public functions / methods / endpoints
- Inputs each accepts
- Outputs / side effects each produces
- Branches in the logic (each `if`, each exception path)

Output as a table.

### Phase 2 — Identify gaps

Cross-check against existing tests. What's already covered? What isn't?

### Phase 3 — Plan

For each gap, propose a test:

- Name (following `test_<unit>__<scenario>__<expected>`)
- What it locks in
- Fixtures needed

**Stop. Wait for approval — especially if any test would require new factories or fixtures.**

### Phase 4 — Implement

- Use factory_boy / pytest-factoryboy for fixtures
- Arrange / Act / Assert structure
- One behavior per test
- Mock at boundaries (external services, Celery) — never the ORM

Reference `ai/examples/backend/test_example.py`.

### Phase 5 — Report

- Tests added (count, names)
- Coverage delta on the target area
- Lint / format clean
- Any flakiness observed
