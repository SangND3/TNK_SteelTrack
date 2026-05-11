# Skill: Schema migration

Rules in `ai/rules/MIGRATION_RULES.md`. This is the how-to.

## Decision tree

```
Need to change schema?
├── Dev/local only?
│   └── Single migration, ship it.
│
├── Production with tiny data (<1k rows)?
│   └── Single migration is fine. Test forward + backward locally.
│
└── Production with significant data (>1k rows or critical table)?
    └── Use zero-downtime pattern. Read on.
```

## Steps for any migration

1. **Understand current state** — what's the schema now? What queries hit this table?
2. **Define target state** — what's the schema after?
3. **Identify the safe path** — what's the sequence of changes that never breaks production?
4. **Write the plan** — share with user before coding
5. **Implement step by step** — one migration per logical change
6. **Test** — forward, backward, full suite
7. **Deploy** — in the planned order; verify after each step

## Zero-downtime patterns

### Adding a new field

**Nullable, no default required:**

One migration. Safe everywhere.

```python
# migrations/0042_add_archived_at.py
class Migration(migrations.Migration):
    dependencies = [...]
    operations = [
        migrations.AddField(
            model_name="order",
            name="archived_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
```

**Non-nullable with sensible default:**

If Postgres can fill it without rewriting the table (`DEFAULT` is constant, Postgres 11+), one migration is fine. Check the migration output for `ALTER TABLE` lock duration.

If a rewrite is required (older Postgres, computed default), split into three:

1. Add nullable
2. Backfill (data migration)
3. Add NOT NULL constraint

### Renaming a field

**Dev only or table is tiny:** `RenameField` is fine.

**Production, real data:**

Multi-deploy:

1. **Migration A:** add new field as nullable
2. **Code change:** services write both old and new
3. **Migration B (data):** backfill new from old
4. **Code change:** services read from new; stop writing old
5. **Migration C:** drop old field

This takes 3-5 deploys. Yes, really.

### Adding an index

```python
from django.contrib.postgres.operations import AddIndexConcurrently

class Migration(migrations.Migration):
    atomic = False  # CONCURRENTLY can't run in a transaction
    dependencies = [...]
    operations = [
        AddIndexConcurrently(
            model_name="order",
            index=models.Index(fields=["user", "-created_at"], name="order_user_created_idx"),
        ),
    ]
```

For small tables, `AddIndex` is fine (locks briefly).

### Changing a column type

**Compatible change** (e.g., `varchar(20)` → `varchar(50)`): one migration.

**Incompatible** (e.g., `int` → `bigint`, `varchar` → `text`): use the rename pattern.

### Dropping a field

1. **Code change:** stop reading + writing the field
2. **Deploy + verify:** no errors in prod
3. **Migration:** drop the field

Don't combine code change and drop in one release. In-flight requests on old code will crash.

### Splitting a table

1. Create new table(s)
2. Dual-write
3. Backfill
4. Switch reads
5. Stop writing old
6. Drop old (after a grace period — easier to revert if something breaks)

### Merging tables

Reverse of splitting; same multi-step pattern.

## Data migrations

```python
from django.db import migrations


def forwards(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    batch_size = 1000
    last_id = 0
    while True:
        batch = list(
            Order.objects.filter(id__gt=last_id, status__isnull=True)
            .order_by("id")[:batch_size]
        )
        if not batch:
            break
        for order in batch:
            order.status = "completed"  # whatever the backfill is
        Order.objects.bulk_update(batch, ["status"])
        last_id = batch[-1].id


def backwards(apps, schema_editor):
    # Either implement, or raise with a clear message
    raise NotImplementedError(
        "Cannot reverse: original null statuses were not preserved."
    )


class Migration(migrations.Migration):
    dependencies = [...]
    operations = [migrations.RunPython(forwards, backwards)]
```

Rules:

- Use `apps.get_model()`, never direct import
- Batch large updates
- Idempotent (safe to re-run)
- Reverse code or explicit raise

## Testing a migration

```bash
# Forward
make migrate

# Backward (to the migration before yours)
docker compose exec web python manage.py migrate orders <previous>

# Forward again
make migrate

# Full test suite
make test
```

If any of the above fail, the migration is not ready.

## CI verification

Configure CI to:

- Run `makemigrations --check --dry-run` — fails if a model change has no migration
- Apply all migrations on a clean DB
- Apply migrations on a copy of staging (if feasible)

## Deploying

Schema migration order matters:

1. **Expand** (backward-compatible additions) — deploy migration first
2. **Migrate** (data backfill) — deploy alongside or after
3. **Contract** (drops, renames complete) — deploy after code stops using the old

For the simple case (nullable add, no code dependency), schema + code deploy together is fine.

For complex changes, the **expand → migrate → contract** pattern takes multiple deploys but ensures zero downtime.

## Communicating in the PR

Every migration PR includes:

```markdown
## Migration

- **Table:** `orders`
- **Operation:** Add `archived_at` (nullable timestamp)
- **Lock acquired:** ACCESS EXCLUSIVE briefly (for ADD COLUMN with no rewrite)
- **Estimated duration:** <1s
- **Reversible:** yes
- **Backfill required:** no
- **Deploy order:** schema + code together; no special handling
```

Reviewers need this. Future you needs this.

## Anti-patterns

- ❌ Single migration that adds NOT NULL column to a 10M-row table
- ❌ `RenameField` on a production table
- ❌ Migration that runs `RunSQL` without `reverse_sql`
- ❌ Combining 5 unrelated schema changes in one migration
- ❌ Editing a shipped migration (write a new one instead)
- ❌ Skipping the test step "because the migration is simple"
