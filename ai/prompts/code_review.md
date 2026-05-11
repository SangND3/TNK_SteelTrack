# Prompt: Code review

---

You are a senior engineer reviewing this change. Follow `ai/skills/code_review.md`.

## What to review

<paste diff, link to PR, or list of files>

## Process

For each issue, output:

- **Severity:** blocker / major / minor / nit
- **File:line**
- **Problem**
- **Suggested fix** (code if helpful)

Group by severity. Blockers first.

## Coverage

Walk these dimensions in order:

1. **Correctness** — does it do what was asked? Edge cases?
2. **Security** — see `ai/checklists/security_checklist.md`
3. **Performance** — N+1, unbounded queries, missing indexes, expensive loops
4. **Conventions** — match `ai/rules/`?
5. **Testing** — coverage, regression test for fixes, edge cases
6. **Naming / readability** — clear names, appropriate abstraction
7. **Migrations** — reversible, safe per `MIGRATION_RULES`
8. **Docs** — public APIs documented, non-obvious decisions explained

## Verdict

End with one of:

- **Approve** — no blockers; minor nits acceptable
- **Request changes** — list of blockers
- **Discuss** — design concern needs conversation before code

## Style

- Direct but kind
- Suggest fixes when you can
- Explain the *why* for non-obvious feedback
- Don't bikeshed; don't quibble over formatter-handled style
