# Skill: Test writing

Rules in `ai/rules/TESTING_RULES.md`. This is the how-to.

## Before you write a test

Ask:

1. **What behavior am I locking in?** (Not "what code am I covering")
2. **Is this the right layer?** (Unit, integration, e2e?)
3. **What's the minimum setup needed?**

If you can't answer #1 in one sentence, you're testing implementation, not behavior.

## Test structure

Use Arrange / Act / Assert. Separate with blank lines (not comments).

```python
def test_order_create__when_user_has_credit__creates_pending_order(
    user_factory, item_factory
):
    user = user_factory(credit=Decimal("100"))
    items = [{"sku": item_factory().sku, "qty": 1, "price": Decimal("50")}]

    order = order_create(user=user, items=items)

    assert order.user == user
    assert order.status == "pending"
    assert order.total == Decimal("50")
```

## Naming

`test_<unit>__<scenario>__<expected>`

```python
def test_order_create__when_stock_insufficient__raises_insufficient_stock_error():
def test_order_list_view__when_anonymous__redirects_to_login():
def test_password_reset__when_token_expired__shows_error_message():
```

Long names are fine — they show up in CI failure output.

## What to test for each layer

### Services

- Happy path
- Each business rule branch
- Each exception path
- Side effects (Celery tasks queued, related rows created)
- Idempotency where claimed

```python
def test_order_create__triggers_notification(mocker, user_factory):
    mock_notify = mocker.patch("apps.orders.services.notify_user.delay")
    user = user_factory()

    order_create(user=user, items=[{"sku": "ABC", "qty": 1, "price": Decimal("10")}])

    mock_notify.assert_called_once()
    assert mock_notify.call_args.kwargs["order_id"]
```

### Selectors

- Filter behavior (each filter individually + in combination)
- Ordering
- Edge cases: empty, large, unicode
- Excluded items (soft-deleted, hidden)

```python
def test_order_list__filters_by_status(user_factory, order_factory):
    user = user_factory()
    order_factory(user=user, status="open")
    order_factory(user=user, status="closed")

    result = order_list(user=user, status="open")

    assert result.count() == 1
    assert result.first().status == "open"
```

### Views

- HTTP method allowed / not allowed
- Anonymous access (redirect or 403)
- Authenticated but wrong user (403 or 404)
- HTMX vs non-HTMX (partial vs full page)
- Form errors render

```python
def test_order_detail__when_not_owner__returns_404(client, user_factory, order_factory):
    owner = user_factory()
    other = user_factory()
    order = order_factory(user=owner)
    client.force_login(other)

    response = client.get(f"/orders/{order.public_id}/")

    assert response.status_code == 404
```

### Forms

- Valid input passes
- Each `clean_*` method's failure case
- `clean()` cross-field validation

### Templates / HTMX

- Rendered output contains expected element
- HTMX request returns partial; non-HTMX returns full page

```python
def test_order_create__htmx_returns_partial(client, user_factory):
    user = user_factory()
    client.force_login(user)

    response = client.post(
        "/orders/",
        {"items": "..."},
        HTTP_HX_REQUEST="true",
    )

    assert response.status_code == 200
    assert b"<tr" in response.content       # partial
    assert b"<html" not in response.content  # not a full page
```

### Celery tasks

- Idempotency: run twice, same result
- Retry behavior on transient failure
- Failure on permanent failure

## Fixtures

Use `factory_boy` for model fixtures. Register as pytest fixtures via `pytest-factoryboy`:

```python
# apps/orders/tests/factories.py
class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = "pending"
    total = Decimal("0")
```

```python
# apps/orders/tests/conftest.py
from pytest_factoryboy import register
from .factories import OrderFactory

register(OrderFactory)
```

Then `order_factory` is auto-available as a fixture.

## Mocking

Mock at boundaries — never the ORM, never your own services unless they cross app boundaries.

```python
# Mock external services (HTTP, email, third-party)
def test_x(mocker):
    mocker.patch("apps.orders.services.stripe.Charge.create", return_value={...})
    ...

# Mock Celery to verify scheduling without executing
def test_x(mocker):
    mock_task = mocker.patch("apps.orders.services.send_email.delay")
    order_create(...)
    mock_task.assert_called_once()
```

Don't:

```python
# WRONG — mocking the ORM is brittle and tests nothing meaningful
mocker.patch("apps.orders.services.Order.objects.create", return_value=Order(...))
```

## Time-sensitive tests

Use `freezegun`:

```python
from freezegun import freeze_time

@freeze_time("2026-05-11 10:00:00")
def test_expires_after_24_hours():
    token = token_create()
    with freeze_time("2026-05-12 10:00:01"):
        assert token_is_expired(token)
```

Never `sleep()` in tests.

## Parameterized tests

For "same logic, different inputs":

```python
@pytest.mark.parametrize("status,expected", [
    ("open", True),
    ("closed", False),
    ("pending", True),
])
def test_can_edit__by_status(status, expected, order_factory):
    order = order_factory(status=status)
    assert order_can_edit(order) is expected
```

## Database

- `@pytest.mark.django_db` enables DB access (or set globally in conftest)
- `--reuse-db` flag (configured in `pyproject.toml`) skips schema recreation
- Each test runs in a transaction that rolls back at the end

## When to use snapshots

Sparingly. Snapshots are tempting but brittle — a small render change updates 50 snapshots, hiding real changes in noise. Use only for stable rendered output (e.g., email HTML).

## Anti-patterns

See `ANTI_PATTERNS.md` § Tests. Most common:

- ❌ Tests without assertions
- ❌ Mocking the thing under test
- ❌ Testing implementation details (mock counts, method ordering)
- ❌ One giant test that exercises 10 behaviors
- ❌ Tests that depend on execution order
- ❌ Skipping a test because "it's flaky"
- ❌ `time.sleep()` for synchronization

## Coverage

Aim for `fail_under = 70` (set in `pyproject.toml`). Don't chase 100%. Test behavior worth testing; mark unreachable lines with `# pragma: no cover` (and a comment).
