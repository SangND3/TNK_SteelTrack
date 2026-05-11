# Skill: API design

Rules in `ai/rules/API_CONVENTION.md`. This is the how-to for designing a new endpoint.

## Before you design anything

Ask:

1. **Who calls this?** Browser via HTMX → return HTML. Mobile / third-party / external → JSON via DRF.
2. **Is this a resource or an action?** Resources get RESTful URLs; actions get named endpoints.
3. **What's the data shape?** Sketch the request and response on paper first.
4. **What can go wrong?** Validation, auth, conflict, not-found, rate limit.

If you can't answer #1, **default to HTMX**. Adding DRF speculatively is technical debt.

## Step 1 — Choose the URL

### Resources

| Action          | Method | URL                              |
| --------------- | ------ | -------------------------------- |
| List            | GET    | `/orders/`                       |
| Create          | POST   | `/orders/`                       |
| Retrieve        | GET    | `/orders/<id>/`                  |
| Update (full)   | PUT    | `/api/v1/orders/<id>/`           |
| Update (partial)| PATCH  | `/api/v1/orders/<id>/`           |
| Delete          | DELETE | `/api/v1/orders/<id>/`           |

For HTMX, use GET and POST (browsers don't natively send PUT/DELETE).

### Actions

Named verbs on the resource:

```
POST /orders/<id>/complete/
POST /orders/<id>/archive/
POST /orders/<id>/refund/
```

Not:

```
POST /complete-order/<id>/    ✗ — verb at root
POST /orders/complete/<id>/   ✗ — id at end
```

### IDs

- Expose `public_id` (UUID), not the internal int `id`
- Avoids leaking row counts; avoids accidental enumeration

## Step 2 — Design the request

### HTMX (form)

A real `<form>` posted via HTMX:

```html
<form hx-post="{% url 'orders:create' %}">
  <input type="text" name="title" required>
  <input type="number" name="quantity" min="1">
  <button type="submit">Create</button>
</form>
```

Server reads from `request.POST`. Validate with a Django Form.

### JSON (DRF)

```http
POST /api/v1/orders/
Content-Type: application/json

{
  "title": "Widget",
  "items": [{"sku": "ABC", "quantity": 1}]
}
```

Validate with a DRF Serializer.

## Step 3 — Design the response

### HTMX

Return HTML — partial of the changed region.

```python
def order_create_view(request):
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = order_create(user=request.user, **form.cleaned_data)
        return render(request, "orders/partials/order_row.html", {"order": order})
    return render(request, "orders/partials/order_form.html", {"form": form})
```

### JSON

```json
{
  "data": {
    "public_id": "01J...",
    "title": "Widget",
    "status": "pending",
    "total": "10.00",
    "created_at": "2026-05-11T10:00:00Z"
  }
}
```

Wrap in `data` (success) or `error` (failure). Consistent shape across endpoints.

## Step 4 — Define errors

| Code | When                                          | Response                                                 |
| ---- | --------------------------------------------- | -------------------------------------------------------- |
| 400  | Bad input (malformed JSON)                   | `{"error": {"code": "bad_request", "message": "..."}}`   |
| 401  | No auth                                       | `{"error": {"code": "unauthenticated"}}`                 |
| 403  | Authenticated but not allowed                 | `{"error": {"code": "forbidden"}}`                       |
| 404  | Resource not found                            | `{"error": {"code": "not_found"}}`                       |
| 409  | Conflict (e.g., duplicate)                    | `{"error": {"code": "conflict", "message": "..."}}`      |
| 422  | Validation error                              | `{"error": {"code": "validation_error", "fields": {...}}}` |
| 429  | Rate limited                                  | `{"error": {"code": "rate_limited", "retry_after": 60}}` |

`code` is a stable machine-readable string. Clients switch on it.

For HTMX, errors are usually re-rendered partials with form errors visible, not status codes.

## Step 5 — Pagination (lists only)

### Cursor (default for large/changing lists)

```http
GET /api/v1/orders/?cursor=eyJpZCI6MTIzfQ&limit=20

{
  "data": [...],
  "meta": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true
  }
}
```

### Page (small/admin)

```http
GET /api/v1/orders/?page=2&page_size=20

{
  "data": [...],
  "meta": {
    "page": 2,
    "page_size": 20,
    "total": 142,
    "total_pages": 8
  }
}
```

Default page size 20, max 100.

## Step 6 — Filtering and sorting

```
GET /api/v1/orders/?status=open&customer_id=<id>&sort=-created_at
```

- Filter via query params; `django-filter` makes this easy
- Sort with `?sort=field` ascending, `?sort=-field` descending
- Allow only whitelisted fields for both

## Step 7 — Permissions

Always check server-side. Two layers:

1. **Authentication** — who are you?
2. **Authorization** — can you do this to this object?

```python
def order_detail_view(request, public_id):
    # Scope by user — never just .get(public_id=...)
    order = get_object_or_404(
        Order.objects.filter(user=request.user),
        public_id=public_id,
    )
    ...
```

For DRF, use permission classes:

```python
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)
```

## Step 8 — Rate limiting

For auth endpoints, search, anything expensive:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key="user_or_ip", rate="60/m", block=True)
def search_view(request):
    ...
```

## Step 9 — Idempotency

For critical operations (payments, charges), require an `Idempotency-Key` header. Store the key + result; return the same result on retry.

## Step 10 — Versioning (DRF only)

URL-based: `/api/v1/`, `/api/v2/`. Once v1 ships, **never break it**. Add v2 for breaking changes; deprecate v1 on a timeline.

See `ai/decisions/005-api-versioning.md`.

## Step 11 — Document

For DRF, generate OpenAPI via `drf-spectacular`:

```bash
python manage.py spectacular --file schema.yml
```

Commit `schema.yml` so clients can diff between versions.

For HTMX endpoints, document in code (docstring on the view).

## Checklist before merging

- [ ] URL follows conventions (plural, trailing slash, hyphens)
- [ ] Method matches semantics (GET safe, POST mutates)
- [ ] Permissions checked
- [ ] Input validated (form or serializer)
- [ ] Errors return consistent shape
- [ ] Lists paginated
- [ ] Tests cover happy path + auth + validation + permission edge cases
- [ ] No secrets in URL params
- [ ] OpenAPI schema updated (if DRF)
