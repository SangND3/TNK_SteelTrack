# MIGRATION_RULES.md

Schema changes are the highest-risk thing this codebase does. These rules keep them safe.

## Hard rules

- **Never edit a migration that has been applied to production.** Adjust by writing a new one.
- **Always commit migrations alongside the model change.** A model without its migration is broken.
- **Always review the generated migration.** Django sometimes generates more than expected.
- **Migrations must be reversible** unless explicitly one-way (drop table after data migrated). Write `reverse_code` for `RunPython`.
- **Test forward + backward locally** before pushing.

## Generated vs hand-written

- `makemigrations` for schema (table/column/index/constraint changes)
- Hand-write `RunPython` migrations for data changes
- Don't mix schema and data changes in one migration — separate them so each is fast and reviewable

## Reviewing a generated migration

Before committing, open the migration file and verify:

- The operations match what you intended (no surprise renames, no extra fields)
- `null=True` / `default=` chosen correctly for new fields
- No unintended `AlterField` for fields you didn't touch (often comes from `help_text` or `verbose_name` updates)
- Reverse direction makes sense

If Django generated an unintended rename (e.g., dropping + recreating instead of renaming), edit the migration to use `RenameField`.

## Zero-downtime patterns

Production has data. Production has uptime. A migration that locks a big table = outage.

### Adding a NOT NULL column with no sensible default

**Wrong:** add as NOT NULL in one migration. Postgres will rewrite the table → minutes of lock.

**Right:** three-step:

1. **Migration A:** Add column as **nullable** with a server-side default if helpful
2. **Migration B (data):** Backfill in batches (`RunPython`)
3. **Migration C:** Add `NOT NULL` constraint (after backfill is complete in prod)

Deploy A+B together, B+C after verifying.

### Renaming a column

Don't use `RenameField` on production tables. Instead:

1. Add new column, dual-write in code (services write both)
2. Backfill old → new
3. Switch reads to new column
4. Stop writing old column
5. Drop old column

Five deploys. Yes, really.

### Dropping a column

1. Stop reading and writing the column in code (deploy)
2. Drop in migration (next deploy)

If you drop in the same release that stops using it, in-flight requests on the old code will crash.

### Adding an index on a large table

Use `AddIndexConcurrently` from `django.contrib.postgres.operations`:

```python
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    atomic = False  # CONCURRENTLY cannot run in a transaction

    dependencies = [...]
    operations = [
        AddIndexConcurrently(
            model_name="order",
            index=models.Index(fields=["status", "-created_at"], name="order_status_created_idx"),
        ),
    ]
```

Set `atomic = False` on the migration class.

### Changing column type

If lossless and fast (e.g., `varchar(10)` → `varchar(20)`): one migration is fine.

If lossy or slow (e.g., changing integer width, encoding): use the rename pattern (add new column, dual-write, backfill, switch, drop).

## Data migrations

Always batched. Always idempotent.

```python
def forwards(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    batch_size = 1000
    qs = Order.objects.filter(legacy_status__isnull=False)
    last_id = 0
    while True:
        batch = list(qs.filter(id__gt=last_id).order_by("id")[:batch_size])
        if not batch:
            break
        for order in batch:
            order.status = MAPPING[order.legacy_status]
        Order.objects.bulk_update(batch, ["status"])
        last_id = batch[-1].id


def backwards(apps, schema_editor):
    # Either implement reverse or document why it's irreversible
    raise NotImplementedError("This migration cannot be reversed.")


class Migration(migrations.Migration):
    dependencies = [...]
    operations = [migrations.RunPython(forwards, backwards)]
```

Rules:

- Use `apps.get_model(...)` — never import models directly (the model state can be different from current code)
- Batch large updates
- Make idempotent — safe to re-run after a partial failure
- Provide a meaningful reverse (or raise with a message)

## Long migrations and CI

CI should run migrations against a fresh DB and verify they don't time out. For migrations expected to take >5 minutes in production, mark them in the PR description and run separately (out of band) from code deployment.

## Multi-environment

Migrations run on every environment in order. Before merging:

- [ ] Migration runs cleanly on a copy of staging
- [ ] Forward + backward both work locally
- [ ] No `RunPython` without `reverse_code` (or explicit raise)
- [ ] Data migration includes batching for tables >100k rows
- [ ] Index on large table uses `AddIndexConcurrently`
- [ ] Squashed if you have >20 migrations in one app and CI runs are slow

## Squashing

When a Django app has 50+ migrations:

```bash
python manage.py squashmigrations <app> 0001 0050
```

Test the squashed migration in CI before merging. Keep the originals for one release cycle in case of rollback.

## Naming

Default migration filenames (`0042_alter_user_email.py`) are fine. For data migrations, rename for clarity:

```
0043_backfill_order_status.py
```

## What goes in the PR description

For any PR with a migration:

```
## Migration

- **Table:** orders
- **Operation:** Add `archived_at` column (nullable timestamp)
- **Lock:** AccessExclusiveLock briefly (Postgres acquires for ADD COLUMN)
- **Estimated duration:** <1s (no default → no rewrite)
- **Reversible:** yes
- **Backfill required:** no
```

Reviewers need this. Future-you needs this.
