# Prompt: Bug fix

---

You are a senior full-stack engineer. Follow `ai/skills/bug_fixing.md`.

## Bug

**Symptoms:** <what the user sees>

**Expected:** <what should happen>

**Reproduction:**

1. <step>
2. <step>
3. <step>

**Error / log:**

```
<paste exact error message or log line>
```

**Suspected area:** <file / function / feature, if you have a hunch>

**Severity:** <S1 outage / S2 degraded / S3 minor>

## Process

1. **Diagnose.** Find the root cause. Explain it. **Do not propose a fix yet.**
2. **Confirm.** Wait for me to acknowledge or correct the diagnosis.
3. **Failing test.** Write a regression test that fails on `main`.
4. **Fix.** Smallest change that makes the test pass without breaking others.
5. **Verify.** Full test suite + linter. Report results.
6. **Self-review.** Walk `ai/checklists/backend_checklist.md` or `frontend_checklist.md` as applicable.
7. **PR description.** Using `ai/templates/pr_description.md`. Include the regression test name.

## Constraints

- Don't refactor unrelated code
- Don't change tests that aren't related to this bug
- If the fix uncovers other bugs, list them — don't fix them in the same PR
