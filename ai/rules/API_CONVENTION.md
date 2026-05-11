# API_CONVENTION.md

Two kinds of endpoints in this project:

1. **HTMX endpoints** — return HTML fragments, called by `hx-*` attributes
2. **JSON APIs (DRF)** — return JSON, used only when needed (mobile, public API, third-party)

Default to HTMX. Add DRF only with concrete justification.

## URLs

### Naming

- Lowercase with hyphens: `/password-reset/` ✓, `/password_reset/` ✗
- Trailing slash always: `/orders/` ✓, `/orders` ✗
- Plural resource names: `/orders/`, `/users/`
- Verbs for actions, not resources: `/orders/<id>/complete/` (action), `/orders/<id>/` (resource)

### HTMX endpoints

Live alongside regular views in each app's `urls.py`.

Examples:

```
GET  /orders/                    list page (or partial if hx-get)
POST /orders/                    create
GET  /orders/<public_id>/        detail page (or partial)
POST /orders/<public_id>/complete/    action
GET  /orders/<public_id>/edit-form/   return inline edit form fragment
```

### JSON APIs (when added)

Mounted under `/api/v<n>/`. Versioned from day one.

```
GET    /api/v1/orders/                list
POST   /api/v1/orders/                create
GET    /api/v1/orders/<public_id>/    retrieve
PATCH  /api/v1/orders/<public_id>/    partial update
DELETE /api/v1/orders/<public_id>/    delete
```

## HTTP methods

| Method      | Use for                                       |
| ----------- | --------------------------------------------- |
| GET         | Read, render forms, return fragments          |
| POST        | Create, mutating actions, form submits        |
| PUT / PATCH | DRF only — full / partial update              |
| DELETE      | DRF only — delete                             |

HTMX uses GET and POST (browsers don't natively send PUT/DELETE without JS shims).

## Status codes

| Code | When                                                                |
| ---- | ------------------------------------------------------------------- |
| 200  | Successful read or HTMX render                                      |
| 201  | Resource created (DRF)                                              |
| 204  | Success with no content                                             |
| 302  | Redirect (after non-HTMX form submit)                               |
| 400  | Validation error (form errors → re-render with bound form)         |
| 401  | Not authenticated                                                   |
| 403  | Authenticated but not authorized                                    |
| 404  | Resource not found                                                  |
| 422  | DRF only — validation error                                         |
| 429  | Rate limited                                                        |
| 500  | Bug — log, alert, return generic error                              |

For HTMX, prefer 200 + a partial showing the error, or use `HX-Trigger` for toast.

## HTMX response patterns

See `ai/rules/HTMX_RULES.md` for the full set. Quick reference:

- Render partial for `request.htmx`, full page otherwise
- Return form partial (with errors) on 400 instead of JSON
- Use `HX-Trigger` for client events
- Use `HX-Redirect` to redirect after HTMX request

## DRF (when used)

### Response shape

Success:

```json
{
  "data": { "id": "...", "name": "..." },
  "meta": { "page": 1, "total": 42 }
}
```

Error:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Email is required",
    "fields": { "email": ["This field is required."] }
  }
}
```

`error.code` is a stable machine-readable string. Clients switch on it.

### Pagination

- **Cursor pagination** for large or frequently-changing lists
- **Page-number pagination** only for small / admin lists
- Default page size: 20, max: 100

```
GET /api/v1/orders/?cursor=eyJpZCI6MTIzfQ&limit=20
```

### Filtering and sorting

```
GET /api/v1/orders/?status=open&sort=-created_at
```

Use `django-filter` for filtering. Sort with `?sort=field` or `?sort=-field` for descending.

### Authentication

- Token or session
- Never API keys in URLs (use `Authorization: Bearer <token>` header)
- Document scheme in OpenAPI

### Versioning

- URL-based: `/api/v1/`, `/api/v2/`
- Never break v1 once published — add v2 instead
- See `ai/decisions/005-api-versioning.md`

### Idempotency

Mutating endpoints should tolerate retries. For critical operations (payments, charges), require an `Idempotency-Key` header.

### Rate limiting

- Auth endpoints: tight (login, signup, password reset)
- Search: moderate
- Read-heavy public endpoints: generous
- Use `django-ratelimit` or `drf-throttling`

### CORS

- Lock down to known origins in production
- Don't use `*` unless the endpoint is truly public

## Shared rules (both HTMX and DRF)

- **CSRF:** required on POST/PUT/PATCH/DELETE for session auth (HTMX sends it via header)
- **Permissions:** always checked server-side. Never trust client-side hiding.
- **Logging:** log every 4xx/5xx with request ID for tracing
- **Input validation:** form/serializer is the only place input is trusted
- **Output:** never leak internal IDs, stack traces, or DB error details
- **Timeouts:** every external call has a timeout; every long view sets a sensible budget

## OpenAPI

If DRF is in use, generate OpenAPI via `drf-spectacular`. Commit the schema to repo so clients can diff.

```bash
python manage.py spectacular --file schema.yml
```

## Webhooks (incoming)

- Verify signatures
- Idempotent processing (deduplicate by webhook ID)
- Respond quickly (≤ 5s); defer real work to Celery
- Return 200 even if you defer; return 4xx only for permanent failure (bad signature, malformed payload)

## Webhooks (outgoing)

- Retry with exponential backoff
- Signed payloads (HMAC) so recipients can verify
- Idempotency key in payload
- Configurable timeout (default 10s)
