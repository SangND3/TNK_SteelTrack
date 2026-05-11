# Prompt: Schema migration

---

You are a senior full-stack engineer. Follow `ai/rules/MIGRATION_RULES.md` and `ai/skills/schema_migration.md`.

## Change

**What:** <table / column / index / constraint changing>

**Why:** <reason>

**Production data:** <yes / no>

**Estimated rows in affected table:** <number, even rough>

## Process

### Phase 1 — Plan

Output:

- Current schema → target schema
- Forward + reverse migration approach
- Locks acquired and duration
- Whether old code can read/write the new shape (and vice versa)
- Backfill plan (if needed): batch size, runtime estimate
- Zero-downtime strategy (single migration / expand-migrate-contract)
- Deploy ordering

**Stop. Wait for approval.**

### Phase 2 — Implement

- Schema migration (reversible — verify `migrate <previous>` works)
- Data migration (separate file, batched, idempotent)
- Code changes that read / write the new shape
- Tests for new behavior

### Phase 3 — Test

- Forward migration locally
- Backward migration locally
- Forward again
- Full test suite passes

### Phase 4 — Report

- Migration file(s) created
- Code changes
- Test results
- Deploy notes for the PR description:

```
## Migration

- **Table:** <name>
- **Operation:** <description>
- **Lock acquired:** <type, duration>
- **Estimated duration:** <time>
- **Reversible:** <yes / no with reason>
- **Backfill:** <none / batched, est. duration>
- **Deploy order:** <single / expand → migrate → contract>
```
