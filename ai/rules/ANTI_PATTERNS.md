# ANTI_PATTERNS.md

Things never to do in this codebase. Read once, internalize, refer back when tempted.

If you find yourself doing any of these, **stop**. Either you've misread the situation or there's a better way.

## Architecture

### ❌ Business logic in `views.py`

```python
# WRONG
def create_order(request):
    if request.method == "POST":
        items = request.POST.getlist("items")
        total = sum(get_item_price(i) for i in items)
        if request.user.credit < total:
            return JsonResponse({"error": "insufficient"})
        order = Order.objects.create(user=request.user, total=total)
        for item in items:
            OrderItem.objects.create(order=order, item_id=item)
        request.user.credit -= total
        request.user.save()
        send_order_email(order)
        return redirect("order_detail", order.id)
```

```python
# RIGHT
def create_order(request):
    form = OrderForm(request.POST)
    if not form.is_valid():
        return render(request, "orders/partials/form.html", {"form": form})
    order = order_create(user=request.user, items=form.cleaned_data["items"])
    return redirect("order_detail", order.public_id)
```

The logic lives in `order_create()` in `services.py`.

### ❌ "Fat models" with business logic

```python
# WRONG
class Order(models.Model):
    def complete(self):
        self.status = "completed"
        self.completed_at = timezone.now()
        self.save()
        for item in self.items.all():
            item.product.stock -= item.quantity
            item.product.save()
        send_completion_email(self)
        Notification.objects.create(...)
```

Models hold data shape and trivial invariants. Multi-entity orchestration belongs in services.

### ❌ Repository pattern

We use Django's ORM directly via managers, selectors, and services. Don't add a repository layer that wraps the ORM "for testability". It adds indirection without value. See `ai/decisions/003-no-repository-pattern.md`.

### ❌ Cross-app imports of internal modules

```python
# WRONG
from apps.billing.services import invoice_finalize
from apps.billing.models import InvoiceLineItem
```

If `apps/orders` needs to talk to billing, go through a defined service interface (`apps/billing/services.py`), not internal models. If you need to import another app's models for FK declaration, that's fine — but logic invocation goes through services.

## Database

### ❌ Querying inside loops (N+1)

```python
# WRONG
for order in Order.objects.all():
    print(order.user.email)  # one query per order
```

```python
# RIGHT
for order in Order.objects.select_related("user"):
    print(order.user.email)
```

### ❌ Unbounded `.all()` in views

```python
# WRONG
def list_orders(request):
    orders = Order.objects.all()  # what if there are 10 million?
    return render(...)
```

Always paginate or filter to a known bound.

### ❌ Raw SQL when ORM suffices

Raw SQL is acceptable only for things ORM truly can't do (complex window functions, CTEs in some cases). Document why.

### ❌ Editing applied migrations

A migration that's been applied to production is **frozen**. Adjust by writing a new migration.

### ❌ Long-running migrations inside a transaction

A migration locking a 10M-row table for 30s = downtime. Use `AddIndexConcurrently`, separate data migrations with batching.

### ❌ `on_delete=models.DO_NOTHING`

You will get integrity errors at the worst moment. Pick an explicit, correct behavior.

## Code style

### ❌ `print()` for debugging in committed code

Use `logger.debug(...)`. `print()` in production hits stdout uncontrolled.

### ❌ Bare `except:` or `except Exception:`

Catch specific exceptions. If you must catch broadly, log and re-raise.

```python
# WRONG
try:
    do_thing()
except:
    pass

# WRONG
try:
    do_thing()
except Exception:
    pass

# RIGHT
try:
    do_thing()
except SpecificError as e:
    logger.warning("do_thing failed: %s", e)
    raise
```

### ❌ `# noqa` / `# type: ignore` without a comment

```python
# WRONG
result = compute(x)  # type: ignore

# RIGHT
result = compute(x)  # type: ignore[arg-type]  # third-party lib has wrong stub
```

### ❌ Mutable default arguments

```python
# WRONG
def add_tag(tags=[]):
    tags.append("new")
    return tags

# RIGHT
def add_tag(tags=None):
    tags = tags or []
    tags.append("new")
    return tags
```

### ❌ "Cleverness" over clarity

```python
# WRONG
return [*filter(None, [x.get("k") for x in items if x])][:5]

# RIGHT
result = []
for item in items:
    if item is None:
        continue
    value = item.get("k")
    if value:
        result.append(value)
return result[:5]
```

The "wrong" version is a one-liner. It will be misread by every reviewer.

## Tests

### ❌ Disabling a failing test to make CI green

Either fix the test (if it's wrong) or fix the code (if the test is right). Skipping is **never** the answer.

### ❌ Tests with no assertions

```python
# WRONG
def test_create_user():
    user_create(email="a@b.com")  # didn't crash = pass?
```

A test without an assertion isn't a test.

### ❌ Testing implementation details

```python
# WRONG
def test_service_calls_helper():
    with mock.patch("apps.orders.services._build_total") as m:
        order_create(...)
        m.assert_called_once()  # who cares?
```

Test behavior (inputs → outputs / side effects), not implementation.

### ❌ Sharing state between tests

If test order matters, you've already failed. Use fixtures; reset state.

## Security

### ❌ Trusting client-side anything

Hidden inputs, JS-disabled buttons, "we don't show the URL in the UI" — none of these are security. Check permissions server-side.

### ❌ String concatenation into SQL/HTML

```python
# WRONG
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

Always parameterize. Always escape (Django templates do this by default — don't use `|safe` unless you really mean it).

### ❌ Logging sensitive data

Passwords, tokens, full PII, payment data — never log.

### ❌ Returning detailed errors to users in production

A 500 page should say "something went wrong" and a request ID. Stack traces are for Sentry, not browsers.

## Frontend

### ❌ JSON APIs called from HTMX

HTMX endpoints return **HTML**. If you find yourself returning JSON to an `hx-*` attribute, you've taken the wrong route.

### ❌ JavaScript for things HTMX/HTML handle

- `fetch()` to render — use `hx-get`
- Client-side form validation as the only validation — server still validates
- Show/hide based on click — use `<details>` or `hx-trigger="click"`

### ❌ `!important` and inline styles

If Tailwind utilities can't express it, add a component class. `!important` is a sign you're fighting the system.

### ❌ Custom CSS reset / framework on top of Tailwind

Tailwind is the framework. Don't layer Bootstrap, Bulma, or your own utilities on top.

## Git

### ❌ Force-pushing `main`

Ever. Never. Not even once.

### ❌ Mega-commits ("Friday afternoon: lots of fixes")

One logical change per commit. Squash-merge a feature branch is fine; a single commit with 47 unrelated changes is not.

### ❌ Skipping the PR even when working solo

The PR is where CI runs and where you self-review. Skipping it skips the discipline.

## When you spot one of these

If you encounter an existing anti-pattern in the codebase:

1. Don't fix it in an unrelated PR (scope creep)
2. Note it in the PR description as a follow-up
3. Open an issue with the `tech-debt` label

Drive-by fixes turn 1-file PRs into 30-file PRs and make review hard.
