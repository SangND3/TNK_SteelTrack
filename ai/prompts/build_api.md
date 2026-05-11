# Prompt: Build API endpoint(s)

---

You are a senior engineer building an API endpoint. Follow `ai/rules/API_CONVENTION.md` and `ai/skills/api_design.md`.

**Default to HTMX** (HTML fragments). Use DRF (JSON) only if there's a non-browser consumer.

## Endpoint

**Resource:** <e.g., orders>

**Operation:** <list / create / detail / update / delete / action>

**Caller:** <browser (HTMX) / mobile / third-party (JSON)>

**Auth:** <session / token / public>

**Request shape:** <describe inputs>

**Response shape:** <describe what's returned>

**Permissions:** <who can do this — owner only? team members? public?>

## Process

### Phase 1 — Design

Output:

- URL pattern (per `API_CONVENTION` § Naming)
- HTTP method
- Request schema (form fields or serializer fields)
- Response schema (template partial structure or JSON shape)
- Error cases + status codes
- Permission check approach
- Pagination (if list)
- Rate limit (if expensive or sensitive)

**Stop. Wait for approval.**

### Phase 2 — Implement

Bottom-up:

1. Service / selector for the underlying operation
2. Form / serializer for input validation
3. View
4. URL pattern
5. Template partial (for HTMX) or schema docs (for DRF)
6. Tests:
   - Happy path
   - Anonymous → redirect / 401
   - Wrong user → 403 / 404
   - Invalid input → 400 / 422 with error shape
   - HTMX vs non-HTMX rendering (if HTMX)

Reference:

- HTMX: `ai/examples/frontend/htmx_form.html`, `ai/examples/backend/view_example.py`
- DRF: `ai/examples/api/rest_endpoint.py`

### Phase 3 — Self-review

Walk `ai/checklists/backend_checklist.md`. Key items:

- [ ] URL convention
- [ ] Permission scoped queryset (no IDOR)
- [ ] Input validated
- [ ] Errors consistent with `API_CONVENTION`
- [ ] No N+1
- [ ] Tests cover auth boundaries
- [ ] OpenAPI updated (if DRF)

### Phase 4 — Report

- Files added / changed
- Test results
- Sample request + response (for the PR description)
