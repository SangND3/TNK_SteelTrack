# ADR 002: Service / selector / view layering (HackSoft style)

**Date:** 2026-05-11
**Status:** accepted

## Context

Django doesn't prescribe how to organize business logic. The two common approaches are:

1. **Fat models** — every behavior lives as a method on the relevant model. `order.complete()`, `user.send_welcome_email()`, etc.
2. **Fat views** — business logic written inline in the view that handles the request.

Both work for small projects. Both fall apart as the codebase grows because:

- **Fat models** make models behave differently across contexts (admin vs API vs form), tangle persistence with workflow, and resist reuse because methods can't be called without an instance
- **Fat views** spread business rules across HTTP handlers, making the same logic hard to call from a Celery task, management command, or another view

## Decision

Adopt the **HackSoft Django Styleguide** layered approach:

- `models.py` — data shape and trivial invariants only
- `selectors.py` — read queries
- `services.py` — write operations and business logic
- `views.py` — HTTP/HTMX orchestration only (parse → call service/selector → render)
- `tasks.py` — Celery background work
- `forms.py` — input validation

Cross-app calls go through services, not direct model imports.

## Why this style specifically

- **Functions over classes** for services and selectors — easier to test, fewer hidden dependencies
- **Keyword-only arguments** — call sites are self-documenting
- **One service / selector per concern** — no `OrderManagerService` god class
- **Transactions in services** — explicit `@transaction.atomic` where multi-step writes happen
- **External calls outside transactions** — defer email/HTTP/etc. via Celery (`transaction.on_commit`)

## Alternatives considered

### Django defaults (no enforced layering)

Status quo for many Django projects. Works until it doesn't. We've seen this become unmanageable in projects we want to learn from.

### Domain-Driven Design (DDD) with aggregates, value objects, etc.

More structure than we need. Overhead for a small project. The benefits don't pay off until you have a complex domain model with multiple bounded contexts.

### Repository pattern (covered in ADR 003)

Considered and rejected — see `003-no-repository-pattern.md`.

### Class-based views with all logic in the view class

Same problem as fat views. CBVs add inheritance complexity without solving organization.

## Consequences

### Positive

- Each layer has one clear responsibility
- Services callable from any context (view, task, command, test)
- Tests can target the service directly, no HTTP needed
- New contributors find the right file by intuition (models/services/views/etc.)
- ORM patterns stay vanilla — no custom abstraction to learn

### Negative

- More files than the "everything in views" approach
- "Where does X go?" questions in edge cases — answered by `ai/rules/BACKEND_RULES.md`
- Risk of services becoming a dumping ground if discipline slips

### Compliance

- `ai/rules/BACKEND_RULES.md` — full convention
- `ai/rules/ANTI_PATTERNS.md` — what not to do
- `ai/examples/backend/service_example.py`, `selector_example.py`, `view_example.py`

## Reference

- [HackSoft Django Styleguide](https://github.com/HackSoftware/Django-Styleguide)
