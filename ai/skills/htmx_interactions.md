# Skill: HTMX interactions

Rules in `ai/rules/HTMX_RULES.md`. This is the how-to for common patterns.

## Mental model

HTMX = server returns HTML fragments, browser swaps them into the DOM. No client-side state. No JSON between server and view.

Three things you control:

1. **Trigger** (`hx-trigger`) — what user action fires the request
2. **Request** (`hx-get` / `hx-post`) — where to send it
3. **Swap** (`hx-target` + `hx-swap`) — where the response lands

## Pattern: inline edit

User clicks a value → cell becomes a form → submit replaces with new value.

```html
<!-- templates/orders/partials/order_row.html (read-only state) -->
<tr id="order-{{ order.public_id }}">
  <td>{{ order.title }}</td>
  <td>
    <button
      hx-get="{% url 'orders:edit_form' order.public_id %}"
      hx-target="#order-{{ order.public_id }}"
      hx-swap="outerHTML"
      class="btn-secondary"
    >Edit</button>
  </td>
</tr>
```

```html
<!-- templates/orders/partials/order_edit_row.html (edit state) -->
<tr id="order-{{ order.public_id }}">
  <td>
    <form
      hx-post="{% url 'orders:update' order.public_id %}"
      hx-target="#order-{{ order.public_id }}"
      hx-swap="outerHTML"
    >
      <input type="text" name="title" value="{{ order.title }}" required>
    </form>
  </td>
  <td>
    <button type="submit" form="...">Save</button>
    <button
      hx-get="{% url 'orders:row' order.public_id %}"
      hx-target="#order-{{ order.public_id }}"
      hx-swap="outerHTML"
    >Cancel</button>
  </td>
</tr>
```

Views return the appropriate partial; same `id` on the wrapping `<tr>` so swaps line up.

## Pattern: form with errors

```html
<!-- templates/orders/partials/order_form.html -->
<form
  hx-post="{% url 'orders:create' %}"
  hx-target="this"
  hx-swap="outerHTML"
>
  <div>
    <label for="title">Title</label>
    <input type="text" id="title" name="title" value="{{ form.title.value|default:'' }}"
           {% if form.title.errors %}aria-invalid="true" aria-describedby="title-error"{% endif %}>
    {% if form.title.errors %}
      <p id="title-error" class="text-danger" role="alert">
        {{ form.title.errors|first }}
      </p>
    {% endif %}
  </div>
  <button type="submit">Create</button>
</form>
```

```python
def order_create_view(request):
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = order_create(user=request.user, **form.cleaned_data)
        response = render(request, "orders/partials/order_row.html", {"order": order})
        response["HX-Trigger"] = json.dumps({
            "orderCreated": {"id": order.id},
            "showToast": {"level": "success", "message": "Order created"},
        })
        return response
    return render(request, "orders/partials/order_form.html", {"form": form})
```

Re-render the form (with errors) when invalid. Replace with the row when valid.

## Pattern: delete with confirmation

```html
<button
  hx-delete="{% url 'orders:delete' order.public_id %}"
  hx-target="#order-{{ order.public_id }}"
  hx-swap="outerHTML swap:200ms"
  hx-confirm="Delete this order? This cannot be undone."
  class="btn-danger"
>Delete</button>
```

`swap:200ms` fades the row before removal (use `htmx-swapping` class for transition).

Alternative without browser confirm dialog — open a modal with HTMX:

```html
<button
  hx-get="{% url 'orders:delete_confirm' order.public_id %}"
  hx-target="#modal-container"
  hx-swap="innerHTML"
>Delete</button>
```

The view returns a modal partial with a real "Delete" button that does the actual DELETE.

## Pattern: infinite scroll

```html
{% for order in orders %}
  {% include "orders/partials/order_row.html" with order=order %}
{% endfor %}

{% if next_cursor %}
<tr
  hx-get="{% url 'orders:list' %}?cursor={{ next_cursor }}"
  hx-trigger="revealed"
  hx-swap="outerHTML"
  hx-target="this"
>
  <td colspan="3">Loading...</td>
</tr>
{% endif %}
```

The "loading" row triggers when scrolled into view. The response replaces it with more rows + a new loading row (or nothing if no more pages).

## Pattern: live search

```html
<input
  type="search"
  name="q"
  placeholder="Search orders"
  hx-get="{% url 'orders:list' %}"
  hx-trigger="input changed delay:300ms, search"
  hx-target="#order-results"
  hx-swap="innerHTML"
>

<div id="order-results">
  {% include "orders/partials/order_list.html" %}
</div>
```

`delay:300ms` debounces. `changed` only fires when value changes.

## Pattern: tabs

```html
<div role="tablist">
  <button
    role="tab"
    hx-get="{% url 'orders:tab' 'open' %}"
    hx-target="#tab-content"
    aria-selected="true"
  >Open</button>
  <button
    role="tab"
    hx-get="{% url 'orders:tab' 'closed' %}"
    hx-target="#tab-content"
    aria-selected="false"
  >Closed</button>
</div>

<div id="tab-content">
  {% include "orders/partials/orders_open.html" %}
</div>
```

Use `hx-on::after-request` to update the selected state, or include `aria-selected` in the response.

## Pattern: modal

```html
<!-- base.html somewhere -->
<dialog id="modal" hx-on::after-swap="this.showModal()"></dialog>

<button hx-get="{% url 'orders:edit_modal' order.public_id %}" hx-target="#modal">
  Edit
</button>
```

The view returns the modal contents (form, etc.). The `hx-on::after-swap` opens the `<dialog>`. Inside the modal, the save button posts and updates the page; close with `<form method="dialog">`.

## Pattern: out-of-band updates

When one action should update multiple regions:

```python
def order_create_view(request):
    # ...
    response = render(request, "orders/partials/order_row.html", {"order": order})
    # Also update the counter at the top of the page
    counter_html = render_to_string(
        "orders/partials/order_count.html",
        {"count": Order.objects.filter(user=request.user).count()},
    )
    response.content += counter_html.encode()
    return response
```

```html
<!-- order_count.html -->
<span id="order-count" hx-swap-oob="true">{{ count }}</span>
```

Use sparingly — easy to abuse, hard to reason about.

## Pattern: redirect after action

For non-HTMX form submit, return `redirect(...)`. For HTMX:

```python
response = HttpResponse(status=204)
response["HX-Redirect"] = reverse("orders:detail", args=[order.public_id])
return response
```

Or, if you want a soft redirect (don't reload the page):

```python
response["HX-Location"] = reverse("orders:detail", args=[order.public_id])
```

## Pattern: toast notification

```html
<!-- base.html -->
<div
  id="toast-container"
  hx-trigger="showToast from:body"
  hx-on::trigger="renderToast(event.detail)"
  aria-live="polite"
></div>

<script>
function renderToast(detail) {
  const div = document.createElement("div");
  div.className = `toast toast-${detail.level}`;
  div.textContent = detail.message;
  document.getElementById("toast-container").appendChild(div);
  setTimeout(() => div.remove(), 3000);
}
</script>
```

Server triggers via `HX-Trigger`:

```python
response["HX-Trigger"] = json.dumps({
    "showToast": {"level": "success", "message": "Saved"}
})
```

## Debugging

- Enable HTMX console logging in dev: `htmx.logAll()` in `app.js` (or only when `?debug=htmx` in URL)
- Network tab: every HTMX request is visible
- Watch for events: `htmx:beforeRequest`, `htmx:afterSwap`, `htmx:responseError`
- Common gotcha: forgetting to set CSRF token → silent 403 (returns no body, no visible error)

## Anti-patterns

- ❌ Returning JSON to an `hx-*` attribute
- ❌ Forgetting `hx-target` (default behavior surprises)
- ❌ Using HTMX for what `<details>`, `<dialog>`, `<form>` already handle
- ❌ Reaching for Alpine.js when HTMX would do
- ❌ Multiple OOB swaps in one response (hard to reason about)
