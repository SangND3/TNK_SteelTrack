# BACKEND_RULES.md

Python / Django conventions. Applies to everything under `apps/` and `config/`.

## Python style

- Python 3.12. Use modern syntax: `str | None` over `Optional[str]`, `list[int]` over `List[int]`.
- Format with ruff (`make format`). Don't argue with the formatter.
- Lint clean. No `noqa` without inline justification.
- Type hints on public functions. Internal helpers — optional but encouraged.
- Docstrings on public functions/classes. One-line for trivial things, fuller for non-obvious.

## File layout (per app)

```
apps/<name>/
├── __init__.py
├── apps.py
├── admin.py
├── models.py        ← data shape, simple invariants, custom managers
├── selectors.py     ← read queries
├── services.py      ← write operations, business logic
├── views.py         ← HTTP/HTMX handlers
├── forms.py         ← input validation
├── urls.py
├── tasks.py         ← Celery tasks
├── signals.py       ← when needed (sparingly)
├── constants.py     ← when needed
├── migrations/
├── templatetags/    ← when needed
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    ├── test_selectors.py
    └── test_views.py
```

## Models

- Inherit from `apps.core.models.TimestampedModel` for `created_at` / `updated_at`
- Be explicit about `on_delete` for every `ForeignKey`
- Index columns used in `WHERE`, `ORDER BY`, `JOIN`
- **No business logic methods** on models — use services
- Custom managers go on the model; complex query *logic* goes in selectors
- See `ai/rules/DATABASE_RULES.md` for schema rules

```python
class Order(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=OrderStatus.choices, db_index=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)

    objects = OrderManager()  # custom manager for common filters

    class Meta:
        indexes = [models.Index(fields=["user", "-created_at"])]

    def __str__(self) -> str:
        return f"Order #{self.id} ({self.status})"
```

## Services

Write operations. Business logic. Transactions.

```python
# apps/orders/services.py
from django.db import transaction

@transaction.atomic
def order_create(*, user: User, items: list[dict]) -> Order:
    """Create an order for a user.

    Raises:
        InsufficientStockError: if any item lacks stock.
    """
    _validate_stock(items)
    order = Order.objects.create(user=user, total=_compute_total(items))
    OrderItem.objects.bulk_create([
        OrderItem(order=order, **item) for item in items
    ])
    notify_order_created.delay(order.id)
    return order
```

Rules:

- **Keyword-only arguments** (`*,`) for clarity at call sites
- **Return type hints** always
- `@transaction.atomic` when multi-step writes
- **No external calls** (HTTP, email, S3) inside the transaction — defer via Celery
- Raise specific exceptions defined in `apps/<app>/exceptions.py`
- Don't return querysets from services — those go in selectors

## Selectors

Read operations.

```python
# apps/orders/selectors.py
def order_list(
    *,
    user: User,
    status: str | None = None,
    since: datetime | None = None,
) -> QuerySet[Order]:
    qs = Order.objects.filter(user=user).select_related("user")
    if status:
        qs = qs.filter(status=status)
    if since:
        qs = qs.filter(created_at__gte=since)
    return qs.order_by("-created_at")


def order_get(*, public_id: str, user: User) -> Order:
    """Return order or raise Http404."""
    return get_object_or_404(
        Order.objects.select_related("user"),
        public_id=public_id,
        user=user,
    )
```

Rules:

- Return querysets when caller might paginate or chain
- Always include necessary `select_related` / `prefetch_related`
- Single-object getters raise 404 explicitly
- No side effects, no writes

## Views

Orchestration only. Parse input → call service/selector → render response.

```python
# apps/orders/views.py
@login_required
@require_http_methods(["GET", "POST"])
def order_create_view(request):
    form = OrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = order_create(user=request.user, **form.cleaned_data)
        if request.htmx:
            return render(request, "orders/partials/order_row.html", {"order": order})
        return redirect("orders:detail", public_id=order.public_id)
    return render(request, "orders/create.html", {"form": form})
```

Rules:

- Function-based views by default (CBVs only when DRF/admin requires)
- One view = one URL pattern
- Always declare allowed methods (`@require_http_methods`)
- HTMX-aware: return partial vs full page based on `request.htmx`
- No querysets built inside views — call selectors

## Forms

Input validation. Cleaning. Nothing else.

```python
class OrderForm(forms.Form):
    items = forms.JSONField()

    def clean_items(self):
        items = self.cleaned_data["items"]
        if not isinstance(items, list) or not items:
            raise ValidationError("At least one item required.")
        return items
```

## Celery tasks

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def notify_order_created(self, order_id: int) -> None:
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        return  # order was deleted; nothing to do
    try:
        send_order_email(order)
    except SMTPException as exc:
        raise self.retry(exc=exc)
```

Rules:

- Accept **IDs**, not model instances
- Idempotent — safe to run twice
- `max_retries` and `default_retry_delay` configured
- Never call other tasks synchronously inside a task
- See `ai/decisions/004-background-job-strategy.md`

## Signals

Use sparingly. Signals are spooky action at a distance. Prefer explicit service calls.

Acceptable:

- `post_migrate` for one-time setup
- `m2m_changed` when there's truly no service to put it in

Not acceptable:

- "Send email when user created" — put it in `user_create()` service

## Exceptions

Define app-specific exceptions in `apps/<app>/exceptions.py`:

```python
class OrderError(Exception):
    """Base for order errors."""

class InsufficientStockError(OrderError):
    pass
```

Catch specific exceptions. Never bare `except:`.

## Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.info("order_created", extra={"order_id": order.id, "user_id": user.id})
```

- `logger`, never `print()`
- Log structured fields (use `extra=`)
- Never log: passwords, tokens, full PII, payment data
- Levels: `debug` (dev), `info` (notable), `warning` (recoverable), `error` (needs attention), `critical` (page someone)

## Imports

```python
# 1. stdlib
import logging
from datetime import datetime, timezone

# 2. third-party
from django.db import models, transaction
from rest_framework import serializers

# 3. first-party
from apps.core.models import TimestampedModel
from apps.users.models import User

# 4. local
from .exceptions import OrderError
from .models import Order
```

Ruff isort enforces this.

## Configuration

- All config via env vars (loaded by `django-environ`)
- Never read env vars inside business logic — read once in settings, expose as `settings.X`
- Sensible defaults for non-secrets

## Performance

See `ai/rules/PERFORMANCE_RULES.md`. Key points:

- Always paginate user-facing lists
- Always use `select_related` / `prefetch_related` for related access
- Use `bulk_create` / `bulk_update` for mass writes
- Use `iterator()` for large reads in management commands
