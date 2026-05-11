# Migration checklist

For every PR with a database migration. The cost of getting this wrong is high — schema mistakes can cause downtime or data loss.

## File-level

- [ ] Migration file committed alongside model change (same PR)
- [ ] Migration filename meaningful (e.g., `0042_backfill_order_status.py` for data migrations)
- [ ] No editing migrations that have shipped to production (write a new one instead)
- [ ] One logical change per migration (split schema + data into separate files)

## Generated migration review

- [ ] Operations match what was intended (no surprise renames, no extra `AlterField`)
- [ ] No unintended changes from `help_text` / `verbose_name` / `default=...` edits
- [ ] If field was renamed, the migration uses `RenameField` (not drop + add)

## Reversibility

- [ ] Migration is reversible (`migrate <app> <previous_migration>` works)
- [ ] If irreversible: `raise NotImplementedError(...)` in `reverse_code` with a reason
- [ ] No `RunSQL` / `RunPython` without `reverse_sql` / `reverse_code` (or explicit raise)

## Data migrations specifically

- [ ] Uses `apps.get_model(...)` — never direct model import
- [ ] Batched (chunks of 500–5000 for large tables)
- [ ] Idempotent (safe to re-run after partial failure)
- [ ] Separate from schema migration
- [ ] Logs progress (for long-running ones)

## Production safety

- [ ] Estimated row count of affected table noted
- [ ] Estimated lock duration noted
- [ ] If table has > ~100k rows AND change is non-trivial:
  - [ ] Uses `AddIndexConcurrently` for indexes (set `atomic = False`)
  - [ ] Uses expand → migrate → contract pattern for renames / drops
  - [ ] NOT NULL adds are split (add nullable → backfill → add constraint)

## Zero-downtime patterns

For schema changes that affect running code:

- [ ] **Adding NOT NULL column:** Three-step (nullable → backfill → constraint)
- [ ] **Renaming column:** Multi-deploy (add new → dual-write → backfill → switch → drop old)
- [ ] **Dropping column:** Stop using in code first → deploy → drop in next migration
- [ ] **Changing type incompatibly:** Use rename pattern

## Constraints

- [ ] `CheckConstraint` / `UniqueConstraint` added where business rules allow
- [ ] Foreign keys have explicit `on_delete`
- [ ] FK has `related_name` (avoid Django default)

## Performance

- [ ] Indexes added for columns used in WHERE/ORDER BY/JOIN
- [ ] No index added "just in case" (every index slows writes)
- [ ] Composite indexes use the right column order (most selective first)

## Testing

- [ ] Migration runs forward locally without error
- [ ] Migration runs backward locally without error
- [ ] Migration runs forward again locally without error
- [ ] Full test suite passes after migration
- [ ] CI's `makemigrations --check --dry-run` passes (no missing migrations)

## Multi-app coordination

- [ ] If migration depends on another app's migration, dependency declared in `dependencies = [...]`
- [ ] No circular dependencies between migrations

## PR description includes

```markdown
## Migration

- **Table:** <name>
- **Operation:** <description>
- **Lock acquired:** <type, duration>
- **Estimated duration:** <time>
- **Reversible:** yes / no (reason)
- **Backfill required:** none / batched, est. duration
- **Deploy ordering:** single deploy / expand-migrate-contract
```

## Special-case checks

If migrating a **critical table** (users, orders, payments, audit_log):

- [ ] Reviewed by a second pair of eyes
- [ ] Backup verified within last 24h
- [ ] Rollback plan documented in PR
- [ ] Maintenance window planned (if non-trivial)

If migration is **>5 minutes estimated**:

- [ ] Marked in PR description
- [ ] Plan to run out-of-band (not during code deploy)
- [ ] CI timeout extended if needed

If migration uses **`RunSQL` raw SQL**:

- [ ] Reviewed for SQL injection (parameterized if user-derived)
- [ ] Both `sql` and `reverse_sql` provided
- [ ] Documented why ORM wasn't sufficient

## Final

- [ ] I would be comfortable running this migration on production right now
- [ ] If something goes wrong, I know how to roll back
