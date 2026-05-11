# DATABASE_RULES.md

PostgreSQL 16. Django ORM. Schema lives in code via migrations.

For *changing* the schema safely, see `ai/rules/MIGRATION_RULES.md`.

## Naming

- **Tables:** snake_case, plural — `users`, `order_line_items`
- **Columns:** snake_case, singular — `created_at`, `email`, `is_active`
- **Booleans:** `is_*` / `has_*` — `is_active`, `has_verified_email`
- **Foreign keys:** `<model>_id` — `user_id`, `assigned_by_id`
- **Django models:** CamelCase singular — `User`, `OrderLineItem`

## Required base models

Every domain model inherits from `apps.core.models.TimestampedModel`:

```python
# apps/core/models.py
class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

For models exposed externally (URLs, APIs), also use a UUID public ID:

```python
class UUIDModel(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True
```

Internal `id` (auto-int) stays as PK. Expose `public_id` externally to avoid leaking row counts.

## Soft delete

Default: **hard delete**. Add soft delete only when business requires audit or undo.

If you add it:

```python
class SoftDeletableModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()       # excludes deleted
    all_objects = models.Manager()      # includes deleted

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    class Meta:
        abstract = True
```

## Foreign keys

Be explicit about `on_delete`:

| Use         | When                                                              |
| ----------- | ----------------------------------------------------------------- |
| `CASCADE`   | Child cannot exist without parent (comment → post)                |
| `PROTECT`   | Parent should not be deletable if children exist (user → orders)  |
| `SET_NULL`  | Reference informational; null acceptable (created_by)             |
| `RESTRICT`  | DB-level prevent (rare; prefer `PROTECT`)                         |
| `DO_NOTHING`| Never. You will get integrity errors.                             |

Document non-obvious choices in a model docstring.

`related_name` is required:

```python
user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
```

## Indexes

- Foreign keys are indexed by default (Django does this)
- Index columns in `WHERE`, `ORDER BY`, `JOIN ON`
- Composite indexes for queries with multiple filters in fixed order
- Partial indexes for filters like `WHERE deleted_at IS NULL`

```python
class Meta:
    indexes = [
        models.Index(fields=["user", "-created_at"]),
        models.Index(
            fields=["status"],
            condition=Q(deleted_at__isnull=True),
            name="active_status_idx",
        ),
    ]
```

Don't add indexes "just in case". Every index slows writes. Use `EXPLAIN ANALYZE` first.

## Constraints

Use database-level constraints where business rules allow:

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            check=Q(total__gte=0),
            name="order_total_non_negative",
        ),
        models.UniqueConstraint(
            fields=["user", "slug"],
            name="unique_user_slug",
        ),
    ]
```

Database constraints catch bugs that bypass application code (raw SQL, parallel writes, future code that forgets).

## Queries

### Always prevent N+1

```python
# WRONG
for order in Order.objects.all():
    user = order.user  # one query per row

# RIGHT
for order in Order.objects.select_related("user"):
    user = order.user
```

- `select_related` — for `ForeignKey` and `OneToOne` (SQL JOIN)
- `prefetch_related` — for reverse FK, M2M (separate query, joined in Python)

### Use `only()` / `defer()` carefully

For wide rows fetched for narrow uses:

```python
Order.objects.only("id", "status", "total").filter(user=user)
```

But it's easy to trigger refetch if you access deferred fields. Use sparingly.

### Bulk operations

```python
OrderItem.objects.bulk_create([...], batch_size=500)
Order.objects.filter(...).update(status="archived")
```

Caveats:

- Signals don't fire on bulk operations
- `bulk_create` skips `pk` assignment on some backends (Postgres returns IDs)
- `update()` skips `save()` and signals

### Iterating large querysets

```python
for order in Order.objects.filter(...).iterator(chunk_size=2000):
    ...
```

Don't load 1M rows into memory.

### Unbounded queries

Never return `Model.objects.all()` to a view without pagination or filter. Add a clear limit.

## Transactions

```python
from django.db import transaction

@transaction.atomic
def order_create(*, user, items):
    order = Order.objects.create(...)
    OrderItem.objects.bulk_create([...])
    return order
```

Rules:

- Wrap multi-step writes in `@transaction.atomic`
- **Never call external services inside a transaction** (HTTP, email, S3) — defer via Celery
- Keep transactions short — they hold locks
- Use `select_for_update()` only when truly needed (race conditions)
- Be aware: signal handlers run inside the same transaction unless `on_commit` is used

```python
transaction.on_commit(lambda: notify_user.delay(order.id))
```

## Connections

- Postgres connection pool via `CONN_MAX_AGE` (set in production settings)
- Don't open new connections inside loops
- Background tasks (Celery) get their own connections

## Sensitive data

- **Passwords:** only via Django's auth framework. Never store in any app table.
- **PII:** encrypted at rest if regulation demands
- **API tokens:** hash before storing (treat like passwords)
- **Audit logs:** append-only, separate table, never updated
- **PCI / payment data:** don't store at all — use a payment provider

## What does NOT belong in the database

- **Files / images** → object storage (S3 / R2 / MinIO), store URL/key in DB
- **Generated/derived data** expensive to recompute → Redis cache
- **Logs** → log aggregator, not DB
- **Sessions at scale** → Redis-backed session store
- **Search indexes** → Postgres FTS is fine to start; Meilisearch/Elasticsearch when needed

## Backups

- Daily automated backups
- Tested restore quarterly (untested backup = no backup)
- Retention: 30 days for daily, 12 months for monthly snapshots
- Encrypt at rest, encrypt in transit

## Testing the schema

Migrations are tested:

```bash
make migrate                        # forward
make migrate app=<name> step=<previous>   # backward
make test                           # full suite passes
```

If forward + backward + test pass, the migration is safe to ship.
