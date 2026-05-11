# Prompt: Optimize query

---

You are a senior engineer optimizing a slow query / endpoint. Follow `ai/skills/performance_optimization.md` and `ai/rules/PERFORMANCE_RULES.md`.

## Target

**What's slow:** <endpoint / function / query>

**Current performance:** <p50/p95 or single measurement, with units>

**Target:** <budget per `PERFORMANCE_RULES.md`, or specific goal>

**How it was measured:** <Sentry / debug toolbar / production logs / manual>

## Process

### Phase 1 — Confirm there's a problem

Verify the slowness is real and reproducible. Note baseline numbers.

### Phase 2 — Locate the bottleneck

Use the tools:

- `django-debug-toolbar` for query count + time
- `django-silk` for profiling
- `EXPLAIN ANALYZE` for individual slow queries
- `cProfile` for CPU-bound code

Output a precise hypothesis:

> "Dashboard view runs 287 queries because we don't prefetch order items, and the orders table is missing an index on `(user_id, -created_at)`."

### Phase 3 — Plan

For each bottleneck, propose a fix in order of likelihood:

1. N+1 → `select_related` / `prefetch_related`
2. Missing index → composite index
3. Unbounded query → paginate
4. External I/O in request → defer to Celery
5. Cache (last resort)

Estimate impact of each.

**Stop. Wait for approval — especially if the fix is a new index on a large table (`AddIndexConcurrently` per `MIGRATION_RULES`) or a new cache layer.**

### Phase 4 — Implement one fix at a time

After each, re-measure. Verify the bottleneck moved (or the metric improved).

### Phase 5 — Verify

- Re-run the metric — does it match the goal?
- Full test suite still passes
- Check related endpoints — did the optimization break anything?

### Phase 6 — Report

```
**Before:** <metric, e.g., dashboard p95 = 1.8s, 287 queries>
**After:** <metric, e.g., dashboard p95 = 180ms, 4 queries>

**Changes:**
- Added `select_related("user").prefetch_related("items")` in selector
- Added composite index on `(user_id, -created_at)` via `AddIndexConcurrently`

**Tests:** all pass
**Migration:** `0042_add_orders_user_created_idx` — concurrent, ~3s on staging, no lock
```
