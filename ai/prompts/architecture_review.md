# Prompt: Architecture review

---

You are a senior engineer doing an architecture review. Follow `ai/rules/ARCHITECTURE.md` and `ai/rules/ANTI_PATTERNS.md`.

## Scope

<what area / what proposal / what design doc to review>

If reviewing an existing area, run:

```bash
find apps/<area>/ -type f -name "*.py" | head -30
```

…and read the key files first (models, services, selectors, views).

## Dimensions

Walk these in order. For each, output: ✅ aligned / ⚠️ concern / 🚨 violation.

### 1. Layering

- Are services / selectors / views correctly separated?
- Any business logic leaking into views or models?
- Cross-app imports going through service interfaces?

### 2. Data model

- Models match domain concepts?
- Indexes appropriate for queries?
- `on_delete` choices correct?
- Soft delete used judiciously?
- Public IDs (UUID) exposed externally?

### 3. Boundaries

- Each app has clear responsibility?
- External integrations isolated behind adapter / service?
- No circular dependencies?

### 4. Performance

- Pagination on list endpoints?
- `select_related` / `prefetch_related` where needed?
- N+1 lurking anywhere?
- Hot paths identified and budgeted?

### 5. Background work

- Right things deferred to Celery (slow / non-critical)?
- Tasks idempotent?
- Tasks accept IDs, not instances?

### 6. Frontend

- HTMX where appropriate; JS minimized?
- Components reused vs duplicated?
- Accessibility considered?

### 7. Security

- Permission checks at the right layer?
- Inputs validated?
- Secrets handled correctly?

### 8. Testing

- Tests cover behavior, not implementation?
- Test pyramid balanced (more unit than e2e)?
- Coverage on critical paths?

## Output

For each concern or violation:

- **What:** the issue
- **Why it matters:** the consequence (perf, security, maintainability)
- **Suggested change:** concrete fix or pattern
- **Effort estimate:** small / medium / large

End with:

- **Top 3 things to fix first** (highest impact, lowest effort)
- **Strategic concerns** (things that will hurt later but aren't urgent)
- **Things working well** (don't break them while fixing the rest)
