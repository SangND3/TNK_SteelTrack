# HTMX_RULES.md

HTMX is the primary interactivity layer. These rules keep usage consistent and debuggable.

## Core idea

HTMX endpoints return **HTML fragments**, not JSON. The server stays in control of rendering. The browser swaps fragments into the DOM.

If you ever feel the need to return JSON to an `hx-*` attribute, you've taken a wrong turn — see `ai/rules/API_CONVENTION.md` for when JSON is appropriate.

## Attributes — always be explicit

```html
<button
  hx-post="/orders/{{ order.public_id }}/complete/"
  hx-target="#order-{{ order.public_id }}"
  hx-swap="outerHTML"
>
  Complete
</button>
```

- **`hx-target`** — always specify. The default (`closest`) surprises people.
- **`hx-swap`** — default is `innerHTML`; use `outerHTML` to replace the element itself.
- **`hx-indicator`** — show loading state.
- **`hx-confirm`** — for destructive actions.
- **`hx-disabled-elt`** — disable the trigger while in-flight (prevents double-submit).

## CSRF

Set globally in `base.html`:

```html
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'>
```

Don't sprinkle `{% csrf_token %}` inside HTMX forms — the header is enough.

## Detecting HTMX requests

Install `django-htmx` middleware. In views:

```python
def order_detail(request, public_id):
    order = order_get(public_id=public_id, user=request.user)
    if request.htmx:
        return render(request, "orders/partials/order_card.html", {"order": order})
    return render(request, "orders/detail.html", {"order": order})
```

Pattern: same data, different template (full page vs partial).

## Returning partials with form errors

```python
def order_create_view(request):
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = order_create(user=request.user, **form.cleaned_data)
        response = render(request, "orders/partials/order_row.html", {"order": order})
        response["HX-Trigger"] = "orderCreated"
        return response
    # GET, or POST with errors — re-render the form partial
    return render(request, "orders/partials/order_form.html", {"form": form})
```

## Triggering client-side events (HX-Trigger)

Use response headers, not custom JS:

```python
response["HX-Trigger"] = "orderCreated"
```

Multiple events with payloads:

```python
import json
response["HX-Trigger"] = json.dumps({
    "orderCreated": {"id": order.id},
    "showToast": {"level": "success", "message": "Order created"},
})
```

Listen on the client:

```html
<div hx-get="/orders/count/"
     hx-trigger="orderCreated from:body"
     hx-target="this">
  {{ count }}
</div>
```

## Out-of-band swaps

Update multiple regions in one response with `hx-swap-oob`:

```django
{# Main response: replaces the trigger element #}
<tr id="order-{{ order.public_id }}">...</tr>

{# Also updates the counter elsewhere on the page #}
<span id="order-count" hx-swap-oob="true">{{ count }}</span>
```

Use sparingly — easy to abuse, hard to reason about.

## Boosting

For instant transitions on regular links:

```html
<body hx-boost="true">
```

This converts internal `<a>` clicks and form submits into HTMX requests. Add `hx-boost="false"` on specific links to opt out (downloads, external links, etc.).

## Loading states

Default pattern:

```html
<button hx-post="/orders/" hx-indicator="#spinner">
  Save
  <span id="spinner" class="htmx-indicator">…</span>
</button>
```

CSS:

```css
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
.htmx-request.htmx-indicator { display: inline; }
```

Use `hx-disabled-elt="this"` to prevent double-clicks:

```html
<button hx-post="/orders/" hx-disabled-elt="this">Submit</button>
```

## Polling and SSE

Polling for live updates:

```html
<div hx-get="/notifications/" hx-trigger="every 30s" hx-target="this" hx-swap="innerHTML">
  ...
</div>
```

Don't poll faster than every 5s without good reason. Above 5/min, consider SSE or WebSockets.

## URLs

HTMX endpoints follow `ai/rules/API_CONVENTION.md`:

- Live alongside regular views in each app's `urls.py`
- Action endpoints: `/orders/<id>/complete/`, not `/orders/complete/<id>/`
- Fragment endpoints: `/orders/<id>/edit-form/`, `/orders/<id>/row/`

## Common patterns

### Inline edit

```html
<tr id="order-{{ order.public_id }}">
  <td>{{ order.title }}</td>
  <td>
    <button hx-get="/orders/{{ order.public_id }}/edit-form/"
            hx-target="#order-{{ order.public_id }}"
            hx-swap="outerHTML">
      Edit
    </button>
  </td>
</tr>
```

The `edit-form/` endpoint returns the same `<tr>` shape but with form inputs. Saving returns the read-only row again.

### Infinite scroll

```html
<tr hx-get="/orders/?cursor={{ next_cursor }}"
    hx-trigger="revealed"
    hx-swap="outerHTML"
    hx-target="this">
  Loading...
</tr>
```

### Delete with confirmation

```html
<button hx-delete="/orders/{{ order.public_id }}/"
        hx-target="#order-{{ order.public_id }}"
        hx-swap="outerHTML swap:200ms"
        hx-confirm="Delete this order?">
  Delete
</button>
```

(Use POST to a delete URL if you don't want to deal with method override middleware.)

## Anti-patterns

See also `ai/rules/ANTI_PATTERNS.md`. HTMX-specific:

- ❌ Returning JSON from HTMX endpoints
- ❌ Default `hx-target` and `hx-swap` (be explicit)
- ❌ Forgetting CSRF — leads to silent 403s in dev
- ❌ Polling every second
- ❌ Stacking many OOB swaps in one response — readability nightmare
- ❌ Using HTMX for what `<details>` / `<dialog>` / native form handles
