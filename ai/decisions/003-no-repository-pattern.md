# ADR 003: Use the Django ORM directly — no repository pattern

**Date:** 2026-05-11
**Status:** accepted

## Context

In some architectural styles (DDD, Clean Architecture, hexagonal), data access goes through a "repository" — an abstraction that wraps the ORM behind methods like `OrderRepository.get_by_id()`, `OrderRepository.list_for_user()`. The repository layer is justified on three grounds:

1. **Testability** — fake the repository in tests instead of using a real DB
2. **Persistence ignorance** — domain code doesn't know it's talking to Postgres
3. **Swappable backend** — could change ORM or DB without touching domain logic

## Decision

**Do not introduce a repository pattern.** Use Django's ORM directly via managers, selectors, and services.

## Why we reject the three justifications

### 1. Testability

In Django, you don't need to fake the ORM for tests. `pytest-django` runs each test in a transaction that rolls back. A test with a few rows created via `factory_boy` is fast (a few milliseconds) and verifies actual behavior, including SQL.

Mocking the ORM would test that our code calls `Order.objects.filter().first()` — not that orders are actually found. That's brittle and tests nothing useful.

### 2. Persistence ignorance

Django is the framework we picked. Pretending the ORM doesn't exist costs us most of Django's value (admin, forms, signals, managers, querysets are all ORM-coupled). Persistence ignorance is a design ideal for projects that *might* swap stacks. We won't.

### 3. Swappable backend

We are not going to swap Django for SQLAlchemy. We are not going to swap PostgreSQL for MongoDB. If we did, the repository wouldn't save us — the difference between ORMs is in the *details* (joins, lazy loading, signals), all of which would still need rewriting.

The "swappable backend" argument optimizes for an event that won't happen, at the cost of complexity every day.

## What we use instead

- **Custom managers** for common queryset filters (`Order.objects.active()`)
- **Selectors** (`apps/orders/selectors.py`) for read functions with parameters
- **Services** (`apps/orders/services.py`) for writes

```python
# Direct ORM use, organized into purposeful layers
def order_list(*, user, status=None):
    qs = Order.objects.filter(user=user).select_related("user")
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-created_at")
```

Tests:

```python
def test_order_list__filters_by_status(user_factory, order_factory):
    user = user_factory()
    order_factory(user=user, status="open")
    order_factory(user=user, status="closed")
    assert order_list(user=user, status="open").count() == 1
```

Real ORM. Real DB. Real behavior. Fast and meaningful.

## Alternatives considered

### Full repository pattern

Rejected for reasons above.

### Lightweight "queries" module (read-only repository)

What our selectors already are. We don't call them repositories because we're not pretending to abstract the ORM — they just *organize* read functions.

### Domain models separate from ORM models

Possible but heavy. Domain model + ORM model + mapper between them = 3× the code for marginal benefit at our scale.

## Consequences

### Positive

- Less code, less indirection
- Tests verify actual SQL behavior
- New contributors don't learn an extra abstraction
- Full use of Django ORM features (annotations, F expressions, prefetch_related, etc.)

### Negative

- Domain code "knows" Django. We're fine with that — Django is the project.
- If we ever did need to swap ORMs (we won't), the refactor would touch many files. Reversibility cost is real.

## When to revisit

If we ever:

- Add a second persistence backend (e.g., Postgres + Cassandra)
- Carve out a piece of the codebase that genuinely needs persistence ignorance (e.g., a pure domain library reused across products)
- Move to a microservice architecture with internal data ownership

…then revisit. Until then: ORM directly, organized via selectors/services.
