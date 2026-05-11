# Backend checklist

Use this for backend-only changes (Python / Django). For full-stack changes, use `feature_checklist.md`.

## Layering

- [ ] Business logic in `services.py`, not `views.py` or `models.py`
- [ ] Read queries in `selectors.py` (or model managers for trivial cases)
- [ ] Views only orchestrate (parse → call → render)
- [ ] Cross-app calls through service interfaces, not direct model imports

## Models

- [ ] Inherits from `apps.core.models.TimestampedModel` (created_at / updated_at)
- [ ] `public_id` (UUID) if model is exposed externally
- [ ] Every FK has explicit `on_delete`
- [ ] Every FK has `related_name`
- [ ] Indexes on columns used in WHERE / ORDER BY / JOIN
- [ ] `Meta.constraints` used for DB-level invariants where possible
- [ ] `__str__` defined
- [ ] No business logic methods

## Services

- [ ] Keyword-only arguments (`def foo(*, user, ...)`)
- [ ] Return type hints
- [ ] `@transaction.atomic` for multi-step writes
- [ ] No external calls (HTTP, email) inside transaction — use `transaction.on_commit`
- [ ] Specific exceptions raised (from `apps/<app>/exceptions.py`), not bare `Exception`
- [ ] Idempotent where claimed
- [ ] Logging at appropriate level with structured context

## Selectors

- [ ] Keyword-only arguments
- [ ] Return type hints (QuerySet[...] or Model)
- [ ] `select_related` / `prefetch_related` for related access
- [ ] Single-object getters raise 404 explicitly
- [ ] Read-only — no `.save()`, no `.delete()`, no `.update()`

## Views

- [ ] `@login_required` (or middleware equivalent) on protected views
- [ ] `@require_http_methods([...])` declaring allowed methods
- [ ] Permission scoped queryset (`.filter(user=request.user).get(...)`) — never bare `.get(pk=...)`
- [ ] HTMX path: `request.htmx` returns partial; non-HTMX returns full page
- [ ] Function-based (CBV only for DRF / admin)
- [ ] No business logic — calls services/selectors only

## Forms

- [ ] Validates types, ranges, lengths
- [ ] `clean_<field>` for field-level rules
- [ ] `clean()` for cross-field rules
- [ ] Errors human-readable

## Celery tasks

- [ ] Accepts IDs, not model instances
- [ ] Idempotent (safe to run twice)
- [ ] `max_retries` and retry policy set
- [ ] `time_limit` / `soft_time_limit` if duration is bounded
- [ ] Specific exceptions in `autoretry_for`
- [ ] Logging on start and on result/error
- [ ] No synchronous calls to other tasks

## Migrations

- [ ] Migration file committed alongside model change
- [ ] Reviewed for unintended ops
- [ ] Reversible (or explicit `raise` with reason)
- [ ] Tested forward + backward locally
- [ ] If touching a large prod table: `AddIndexConcurrently` / expand-migrate-contract
- [ ] No `RunPython` without `reverse_code`
- [ ] Data migration uses `apps.get_model(...)`, batched, idempotent

## Queries / performance

- [ ] No N+1 (verify with debug toolbar)
- [ ] No unbounded `.all()` in user-facing views
- [ ] Pagination on list endpoints
- [ ] `bulk_create` / `bulk_update` for mass writes
- [ ] No raw SQL when ORM suffices; if raw, parameterized

## Tests

- [ ] Service has happy-path + error-path tests
- [ ] Selector has filter/edge-case tests
- [ ] View has permission boundary tests (anonymous, wrong user)
- [ ] HTMX vs non-HTMX rendering tested
- [ ] Factories used (no raw `Model.objects.create` chains)
- [ ] Mocks at boundaries (external services, Celery .delay)
- [ ] Coverage gate passes (`fail_under = 70`)

## Security

- [ ] User input validated
- [ ] Queryset scoped to user before `.get()` (no IDOR)
- [ ] No secrets logged
- [ ] No sensitive data in error responses (production)
- [ ] CSRF not exempted without justification

## Quality

- [ ] Ruff lint passes
- [ ] Ruff format applied
- [ ] Mypy passes
- [ ] No `print()`
- [ ] No commented-out code
- [ ] Docstrings on public functions
