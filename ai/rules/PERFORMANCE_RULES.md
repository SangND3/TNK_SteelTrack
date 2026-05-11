# PERFORMANCE_RULES.md

Performance is a feature. These rules keep the app fast as it grows.

## Budgets

### Server response time

- p50 ≤ 100ms (page render, after warm cache)
- p95 ≤ 400ms
- p99 ≤ 1s

For HTMX partials, the budget is tighter (50/200/500ms).

### Database queries per request

- p50 ≤ 5 queries
- p95 ≤ 20 queries

If you're hitting 50+ queries per request, something is wrong — almost certainly N+1.

### Page weight

- CSS bundle ≤ 50 KB gzipped
- JS bundle ≤ 30 KB gzipped (HTMX itself is ~15 KB)
- HTML ≤ 100 KB gzipped per page
- LCP (Largest Contentful Paint) ≤ 2.5s on 4G
- CLS (Cumulative Layout Shift) ≤ 0.1

## N+1 — the #1 performance bug

Always check for N+1 in code review. Tools:

- `django-debug-toolbar` in dev — shows query count and timing
- `django-silk` for profiling (heavier but useful)
- `nplusone` package — raises an error in dev when N+1 detected

```python
# WRONG — N+1
for order in Order.objects.all():
    print(order.user.email)
    print(order.items.count())

# RIGHT
qs = Order.objects.select_related("user").prefetch_related("items")
for order in qs:
    print(order.user.email)
    print(order.items.count())  # uses prefetched, no extra query
```

## Database

- **Always paginate** user-facing lists. Never `Model.objects.all()` in a view.
- **Use `select_related` / `prefetch_related`** when you access related fields
- **Use `bulk_create` / `bulk_update`** for mass writes — not loops of `.save()`
- **Index** columns used in `WHERE`, `ORDER BY`, `JOIN`
- **`iterator(chunk_size=...)`** for large reads in management commands
- **Use `.only()` / `.defer()`** when fetching wide rows for narrow uses
- **EXPLAIN ANALYZE** any slow query before optimizing
- **Avoid `COUNT(*)`** on large tables in hot paths — use approximate counts or cached counts

## Caching

Three layers, in order of preference:

### 1. Database-level (no app code)

- Postgres query plan caching
- Connection pooling (`CONN_MAX_AGE`)

### 2. Application caching

- **Object cache:** `cache.get_or_set("key", fn, ttl)` for repeated lookups
- **Fragment cache:** `{% cache 600 sidebar request.user.id %}...{% endcache %}` for expensive partials
- **Page cache:** rarely; only fully public pages

```python
def get_dashboard_stats(user_id: int) -> dict:
    return cache.get_or_set(
        f"dashboard:{user_id}",
        lambda: _compute_dashboard_stats(user_id),
        timeout=300,
    )
```

Rules:

- Always set a TTL
- Invalidate via service methods or signals on write
- Cache keys include all variables (user, version, locale)
- Never cache user-specific data with a shared key

### 3. HTTP caching

- Static assets: long cache (1 year) with hashed filenames (`ManifestStaticFilesStorage`)
- API responses: `Cache-Control: private, max-age=...` for user-scoped, `public, max-age=...` for shared

## Background work

Anything ≥ 200ms that doesn't affect the response should be deferred to Celery.

- Email sending
- Webhook delivery
- Reports / exports
- Image processing
- Third-party API calls

Pattern:

```python
@transaction.atomic
def order_create(*, user, items):
    order = Order.objects.create(...)
    transaction.on_commit(lambda: notify_user.delay(order.id))
    return order
```

`on_commit` ensures the task only fires if the transaction succeeds.

## Asset delivery

- Tailwind: built once in CI, served with hashed filename and long cache
- HTMX: vendored, served with long cache
- Images: compressed (CI gate); `loading="lazy"` for below-fold
- Use `WhiteNoise` or Nginx for static — never Django for static in production

## Profiling

In dev:

- `django-debug-toolbar` for query count, time, template render
- `django-silk` for sampling profile
- Python `cProfile` + `snakeviz` for CPU-bound code

In production:

- Sentry performance monitoring
- Database slow query log (Postgres: `log_min_duration_statement = 1000`)

Don't optimize without measuring. "I think this is slow" is not data.

## Hot paths

Identify the 5-10 endpoints that account for 80% of traffic. Set tighter budgets on them. Optimize them first when something gets slow.

## Frontend

- Server-render the initial state — don't fetch after page load when the data is known
- HTMX swaps load only the changed fragment, not the whole page
- Avoid layout shift: set `width`/`height` on images, reserve space for ads/embeds
- Defer non-critical scripts: `<script defer>`
- Inline critical CSS for above-the-fold content (only if needed)

## Memory

- Watch memory in long-running processes (Celery workers leak via Django's cached querysets)
- Set worker recycle: `--max-tasks-per-child=1000` on Celery
- Set Gunicorn worker recycle: `--max-requests=1000 --max-requests-jitter=50`

## Concurrency

- Use `select_for_update()` only when truly needed (race conditions)
- Be aware of long transactions blocking concurrent writes
- For high-write tables, consider partitioning (PostgreSQL native)

## Don't optimize prematurely

The order of work when something is slow:

1. **Measure.** Numbers, not guesses.
2. **Identify the bottleneck.** Usually it's queries or external I/O.
3. **Fix the worst one.** Repeat from step 1.
4. **Only then** consider caching, denormalization, or rewrites.

Don't add Redis caching to a function that's slow because of an N+1 — fix the N+1.
