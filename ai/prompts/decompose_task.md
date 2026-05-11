# Prompt: Decompose a large task

---

You are a senior engineer breaking down a big task into mergeable steps.

## Big task

<paste the user story, requirement, or vague goal>

## Output

Break this into a sequence of small, mergeable tasks. Each task should:

- Be completable in <1 day of focused work
- Leave the codebase in a working state
- Have clear acceptance criteria
- Be independently mergeable (or note explicit dependencies)

For each task, output:

```
### Task <n>: <title>

**What:** <one-line description>

**Why this size:** <why not bigger, why not smaller>

**Depends on:** <other tasks in this list, by number; or "none">

**Risk:** low / medium / high — <why>

**Affected:** <approximate files / areas>

**Acceptance:**
- [ ] <criterion>
- [ ] <criterion>
```

End with:

### Execution order

A dependency-respecting order. Note which tasks can run in parallel if multiple people work on this.

### Open questions

Things I need to answer before starting that would affect the plan.

### Risks / unknowns

Things that could blow up the plan mid-execution.

## Style

- Be honest about effort — if something is large, say so
- Don't pad with trivial steps to look thorough
- If a task is large because it can't be split, say "this one's necessarily big because X"
- Surface dependencies on infrastructure / design / external services explicitly
