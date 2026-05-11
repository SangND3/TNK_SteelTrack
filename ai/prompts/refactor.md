# Prompt: Refactor

---

You are a senior full-stack engineer. Follow `ai/skills/refactoring.md`.

## Refactor

**Target:** <area / file / pattern>

**Why now:** <reason — readability, perf, duplication, blocking a feature>

**Behavior change:** **None.** This is a pure refactor. Tests must pass before and after with no test changes.

## Process

### Phase 1 — Lock behavior

- Identify tests covering the area
- Note any gaps
- Add missing tests in a **separate commit** before refactoring

### Phase 2 — Plan

Output the plan, including:

- Files affected
- Old structure → new structure
- Step-by-step sequence (each step leaves tests green)

**Stop. Wait for approval.**

### Phase 3 — Refactor in small steps

Each commit: compiles, tests pass, code coherent. Use the patterns in `ai/skills/refactoring.md` § Refactoring patterns.

### Phase 4 — Diff review

- Verify no behavior changed
- Test count not reduced
- No leftover dead code
- Imports clean

### Phase 5 — Report

- Files changed
- Lines added / removed
- Tests run: pass count before and after
- PR description (using `ai/templates/pr_description.md`)

## Stop conditions

Stop and ask if you hit any of these:

- A bug is uncovered → list it as follow-up; don't fix
- Scope creep ("while we're here...") → list it
- Behavior change required to make refactor work → escalate; this isn't a pure refactor anymore
