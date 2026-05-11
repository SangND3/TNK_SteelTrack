# Skill: Deployment preparation

How to get a change safely from `main` to production.

## Before you start

- Has the change merged to `main`?
- Is CI green on `main`?
- Are there pending migrations? Do they need special handling (see `MIGRATION_RULES`)?

## Pre-deploy checklist

Walk `ai/checklists/release_checklist.md`. Quick version:

- [ ] CI green on `main`
- [ ] No `DEBUG=True` / dev-only settings sneaking in
- [ ] New env vars added to production secret manager
- [ ] New env vars documented in `.env.example`
- [ ] Migrations reviewed (reversible, no long locks)
- [ ] Static files build runs in CI
- [ ] Smoke test path identified (what URL do you hit after deploy?)
- [ ] Rollback plan understood
- [ ] Stakeholders notified if user-visible change

## Migration ordering

If the release has a schema migration:

**Safe additions** (nullable column, new index via concurrent, new table):

→ Deploy code + migration together. Standard flow.

**Backward-incompatible** (drop column, rename, NOT NULL):

→ Use the expand → migrate → contract pattern. Multiple deploys. See `ai/rules/MIGRATION_RULES.md`.

If you're unsure: ask before deploying. Schema mistakes are the hardest to roll back.

## Deploy flow (template)

> Customize for your hosting platform; this is a generic template.

### Step 1 — Tag the release

```bash
git tag v0.4.2
git push origin v0.4.2
```

### Step 2 — CI builds & tests

CI runs full test suite + build on the tag. Don't deploy if CI is red.

### Step 3 — Deploy migrations (if any)

On the production database:

```bash
# Verify what will run
python manage.py showmigrations --plan

# Run
python manage.py migrate
```

If the migration uses `AddIndexConcurrently`, it can run before or alongside code deploy without blocking.

For backfills, run as a separate management command on the worker.

### Step 4 — Deploy code

Roll out new version. Depending on platform:

- **Render / Fly.io / Heroku:** push → auto-deploy
- **VPS / docker compose:** `docker compose pull && docker compose up -d`
- **Kubernetes:** `kubectl set image deploy/web web=<image>:<tag>` (or via your GitOps tool)

### Step 5 — Verify

After deploy completes:

1. Hit the health check endpoint (`/healthz` returns 200)
2. Hit the smoke test URL (typically: home page + a key feature)
3. Check error rate in Sentry — did errors spike?
4. Check response time in metrics — did latency degrade?
5. Tail logs for 2-5 minutes — any new errors?

### Step 6 — Monitor

Watch for the first 15-30 minutes after deploy:

- Sentry — new issues?
- Metrics — latency, error rate, throughput
- Worker queues — backed up?
- DB connections — exhausted?

## Rollback

If something is wrong:

### Code-only rollback

Deploy the previous version:

```bash
# Tag-based platforms
<your deploy command> --tag v0.4.1

# Or revert and redeploy
git revert <merge-commit-sha>
git push
```

### With migrations

If you rolled forward with a migration, rollback is harder:

- **Migration is reversible:** run `python manage.py migrate <app> <previous>` then deploy old code
- **Migration is one-way:** you cannot simply revert. Either fix forward (write a new migration to undo) or restore from backup (last resort, data loss for any writes after the migration)

This is why migrations must be reversible by default. See `MIGRATION_RULES`.

## Common pre-deploy issues

### Missing env var

Symptom: `KeyError` or `ImproperlyConfigured` on startup.

Fix: add to production secret manager. Verify `.env.example` was updated as a flag.

### Static files not collected

Symptom: 404 on CSS/JS in production.

Fix: ensure `collectstatic` runs in build / startup. Verify `STATIC_ROOT` and `STATICFILES_STORAGE` set.

### CORS / CSRF errors

Symptom: 403 on POST from frontend.

Fix: check `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`.

### Celery tasks not running

Symptom: tasks queued, never executed.

Fix: verify worker is running (`docker compose logs worker`); check it autodiscovered the task module; check broker URL.

### Migration timeout

Symptom: deploy hangs on migrate; eventually times out.

Fix: kill, check if locks; the migration is too long. Cancel via Postgres (`SELECT pg_cancel_backend(pid)`), retry with the migration split into smaller steps, or run out-of-band.

## Communication

For user-visible changes:

- Pre-deploy: notify stakeholders, mention timing
- Mid-deploy: announce maintenance if there's any visible degradation
- Post-deploy: confirm in the appropriate channel

For routine deploys: silent is fine.

## Post-deploy

- Close the deploy ticket
- Update `CHANGELOG.md` if you maintain one
- If a customer was waiting on this fix, let them know

## Anti-patterns

- ❌ Friday afternoon deploys
- ❌ Deploying without watching the result
- ❌ "Just one more change" stacked on a pending deploy
- ❌ Skipping the smoke test because "it worked in staging"
- ❌ Skipping the smoke test because there is no staging (set one up)
- ❌ Manual production-only changes that aren't in code
- ❌ Deploying without a rollback plan
