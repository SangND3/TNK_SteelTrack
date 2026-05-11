# TESTING_RULES.md

Tests are not optional. They are how we know the code works and stays working.

## Toolkit

- **pytest** with `pytest-django`
- **factory_boy** for fixtures (not raw `Model.objects.create()`)
- **pytest-cov** for coverage
- **freezegun** for time
- **responses** for HTTP mocking (when needed)

## Test pyramid

```
        ┌──────────────────┐
        │  E2E / smoke     │   few (5-10)
        ├──────────────────┤
        │  Integration     │   some (per feature)
        ├──────────────────┤
        │  Unit (service/  │   many (per behavior)
        │  selector)       │
        └──────────────────┘
```

- **Unit:** test services, selectors, pure functions. Fast (no I/O when possible). The bulk of tests.
- **Integration:** test views end-to-end (request → response, with real DB). One per happy path + key error paths.
- **E2E / smoke:** a handful of critical user journeys (login → core action → logout).

## What to test

- **Services:** every public service has tests for happy path + key edge cases + error paths
- **Selectors:** test filtering, ordering, edge cases (empty, unicode, large)
- **Views:** test permission boundaries, redirects, HTMX vs full-page rendering, form errors
- **Forms:** test validation rules, especially `clean_*` and `clean()`
- **Celery tasks:** test idempotency (run twice, same result) and error handling
- **Bug fixes:** **always** write a regression test that fails before the fix

## What NOT to test

- Django framework itself (the ORM works, trust it)
- Third-party libraries (test your integration, not their code)
- Implementation details (mock internals → test becomes brittle)
- Trivial getters / setters

## Structure

```
apps/<name>/tests/
├── __init__.py
├── conftest.py         # fixtures for this app
├── factories.py        # factory_boy factories
├── test_models.py
├── test_services.py
├── test_selectors.py
├── test_views.py
├── test_forms.py
└── test_tasks.py
```

## Naming

- `test_<unit>__<scenario>__<expected>` (long but searchable)

```python
def test_order_create__when_stock_sufficient__creates_order_and_decrements_stock():
    ...

def test_order_create__when_stock_insufficient__raises_insufficient_stock_error():
    ...
```

Avoid `test_order_create_1`, `test_order_create_2`. They tell you nothing in failure output.

## Style

### One behavior per test

```python
# WRONG — multiple unrelated checks
def test_order():
    order = order_create(user=user, items=items)
    assert order.total == 100
    assert order.status == "pending"
    assert order.items.count() == 3
    assert notify_task.delay.called

# RIGHT — focused tests
def test_order_create__computes_total():
    order = order_create(user=user, items=items)
    assert order.total == 100

def test_order_create__defaults_to_pending_status():
    order = order_create(user=user, items=items)
    assert order.status == "pending"

def test_order_create__triggers_notification():
    with patch("apps.orders.services.notify_task.delay") as mock_notify:
        order_create(user=user, items=items)
        mock_notify.assert_called_once_with(...)
```

### Arrange / Act / Assert

```python
def test_order_create__triggers_notification(user_factory, item_factory):
    # Arrange
    user = user_factory()
    items = [item_factory() for _ in range(3)]

    # Act
    order = order_create(user=user, items=items)

    # Assert
    assert order.status == "pending"
    assert order.items.count() == 3
```

Blank lines separate the sections; don't add `# Arrange` comments unless the test is long.

### Mocking

- Mock at **service boundaries**, not deep internals
- Mock external calls (HTTP, email, Celery) — never the ORM
- Use `mocker` fixture from `pytest-mock` over manual `patch`

```python
def test_order_create__sends_email(mocker, user_factory):
    mock_send = mocker.patch("apps.orders.services.send_order_email.delay")
    user = user_factory()
    order_create(user=user, items=[...])
    mock_send.assert_called_once_with(order_id=order.id)
```

## Factories

`factory_boy` for fixtures. Default to *minimum viable* objects; override only what the test cares about.

```python
# apps/orders/tests/factories.py
class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = "pending"
    total = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
```

Usage:

```python
def test_x(order_factory):
    order = order_factory(status="completed")  # override only what matters
```

Don't put business logic in factories; that's the service's job.

## Fixtures

`conftest.py` per app. Reusable factories register as pytest fixtures via `pytest-factoryboy`.

```python
# conftest.py
from pytest_factoryboy import register
from .factories import UserFactory, OrderFactory

register(UserFactory)
register(OrderFactory)
```

Then `user_factory` and `order_factory` are auto-available.

## Speed

- Test suite must run in **under 60 seconds** locally for the common case
- Use `--reuse-db` (configured) to skip recreating schema
- Use MD5 password hasher in test settings:

```python
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
```

- Avoid I/O in unit tests. Use `tmp_path` for file ops.
- Mark slow tests with `@pytest.mark.slow`; CI runs them separately

```python
@pytest.mark.slow
def test_complex_report_generation():
    ...
```

## Flakiness

Zero tolerance for flaky tests. If a test fails intermittently:

1. Mark with `@pytest.mark.flaky` (xfail) immediately to unblock
2. Open a ticket
3. Root-cause within a week or delete the test

Common causes: ordering (use `pytest -p no:randomly` to confirm), time (use `freezegun`), DB transaction leak.

## Coverage

- Coverage gate: **70%** for new code (set in `pyproject.toml`)
- 100% is not the goal. Test value matters more than line count.
- `pragma: no cover` for genuinely unreachable code, with a comment

## Running tests

```bash
make test                            # full
make test path=apps/orders           # one app
make test args="-k create"           # filter by name
make test args="-m 'not slow'"       # skip slow
make test args="-x"                  # stop on first failure
make test args="--lf"                # only re-run last failures
```

## CI

Every PR runs:

- Lint (ruff)
- Type-check (mypy)
- Tests (pytest with coverage)
- Migration check (no missing migrations)

Failing CI = blocked PR. No "merge anyway".
