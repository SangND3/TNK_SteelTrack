# Skill: Performance optimization

Rule from `ai/rules/PERFORMANCE_RULES.md`: **measure, don't guess.** This is the process.

## Phase 1 — Confirm there's a problem

Is it actually slow, or does it just feel slow?

- Pull metrics: p50/p95/p99 response time from Sentry, server logs, or `django-silk`
- Compare against budget (see `PERFORMANCE_RULES.md` § Budgets)
- Verify reproducibly — slow once isn't a pattern

If there's no metric, set one up. "Trust me bro it's slow" is not a baseline.

## Phase 2 — Locate the bottleneck

Order of likelihood, in this stack:

1. **N+1 queries** (~70% of perf bugs)
2. **Missing index** on a query that scans
3. **Unbounded query** loading too much
4. **External I/O in a hot path** (API call, file system)
5. **Template render time** (rare, but happens with deep loops)
6. **CPU-bound work** (image processing, parsing) — should already be in Celery

Tools:

- **django-debug-toolbar** in dev — query count + time per request, easy first look
- **django-silk** — sampling profiler with per-request breakdown
- **EXPLAIN ANALYZE** for individual slow queries
- **cProfile** + **snakeviz** for CPU-bound code
- **Sentry Performance** in production for real-traffic data

## Phase 3 — Form a hypothesis

State the hypothesis precisely:

> "The dashboard view runs 287 queries because we loop over orders without `prefetch_related('items')`."

Vague hypotheses lead to vague fixes:

> "The dashboard is slow because of the database." ← useless

## Phase 4 — Fix one thing

Change one thing at a time. Measure again. Repeat.

### Common fixes

**N+1:**

```python
# Before — 1 + N queries
orders = Order.objects.filter(user=user)
for order in orders:
    print(order.user.email)   # +1 query each
    print(order.items.count())  # +1 query each

# After — 2 queries
orders = (
    Order.objects.filter(user=user)
    .select_related("user")
    .prefetch_related("items")
    .annotate(item_count=Count("items"))
)
```

**Missing index:**

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE status = 'open' ORDER BY created_at DESC LIMIT 20;
-- "Seq Scan on orders" + sort = needs index
```

```python
class Meta:
    indexes = [
        models.Index(fields=["status", "-created_at"]),
    ]
```

Generate migration with `AddIndexConcurrently` for production safety.

**Unbounded query:**

```python
# Before
return Order.objects.all()  # what if 10M rows?

# After — paginate
paginator = Paginator(Order.objects.all(), per_page=20)
page = paginator.get_page(request.GET.get("page", 1))
```

**External I/O in request:**

```python
# Before
def order_create_view(request):
    order = order_create(...)
    send_email(order)        # blocks response for ~500ms
    push_to_warehouse(order) # blocks for ~1s
    return render(...)

# After
def order_create_view(request):
    order = order_create(...)  # service queues tasks via transaction.on_commit
    return render(...)

# In services.py
@transaction.atomic
def order_create(...):
    order = Order.objects.create(...)
    transaction.on_commit(lambda: notify_user.delay(order.id))
    transaction.on_commit(lambda: push_to_warehouse.delay(order.id))
    return order
```

**Slow query that can't be fixed by index:**

Sometimes you need:

- Denormalization (store computed total on the order)
- Materialized view (Postgres MV refreshed on schedule)
- Cache (Redis with TTL + explicit invalidation)
- Batch processing (precompute via Celery beat)

Pick the simplest that works.

## Phase 5 — Verify the fix

- Re-run the metric — does the number actually improve?
- Run full test suite — did you break anything?
- Check related endpoints — sometimes a "fix" pushes the bottleneck elsewhere

## Phase 6 — Document

In the PR:

```markdown
## Performance

**Before:** Dashboard p95 = 1.8s (287 queries per request)
**After:**  Dashboard p95 = 180ms (4 queries per request)

**Change:** Added `select_related("user").prefetch_related("items")` and a composite index on `(status, -created_at)`.

**Migration:** `0042_add_orders_status_created_idx` — uses `AddIndexConcurrently`, ~3s on staging, no lock.
```

## Caching

Last resort, not first. Caches add complexity (invalidation, staleness, race conditions).

Order to try:

1. Fix the query (index, select_related)
2. Reduce work (precompute, denormalize)
3. *Then* cache

When you do cache:

```python
def get_dashboard_stats(user_id: int) -> dict:
    return cache.get_or_set(
        f"dashboard:v1:{user_id}",
        lambda: _compute_dashboard_stats(user_id),
        timeout=300,
    )
```

- Always TTL
- Version in key (`v1`) — change to bust the whole namespace
- Invalidate on writes (in service methods)
- Don't cache user-specific data with a shared key

## Don't optimize what isn't slow

If a 50ms function gets called once per request, making it 10ms saves nothing visible. Move on.

The 80/20 rule: a small number of hot paths dominate. Find them, fix them, ignore the rest until they hurt.

## Anti-patterns

- ❌ Adding Redis caching without first checking the query plan
- ❌ "Optimizing" a function with 0.1% of total time
- ❌ Microbenchmarks for a slow web page (the web request has dozens of factors)
- ❌ Refactoring to "more efficient" code without measuring
- ❌ Caching with no invalidation strategy
- ❌ Reaching for async/await as a silver bullet (this isn't a perf fix; it's a concurrency model)
