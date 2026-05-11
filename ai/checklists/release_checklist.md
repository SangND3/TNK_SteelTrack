# Release checklist

Walk before promoting `main` to production.

## Pre-deploy

### Code & CI

- [ ] All changes for this release merged to `main`
- [ ] CI green on `main` (lint, format, type, test, build)
- [ ] No `DEBUG=True` / dev-only settings sneaking into production
- [ ] No `print()`, no leftover debug code
- [ ] No commented-out code introduced
- [ ] CHANGELOG.md updated (if maintained)

### Configuration

- [ ] New env vars added to production secret manager
- [ ] New env vars documented in `.env.example` with placeholders
- [ ] Feature flags configured for any new features behind flags
- [ ] DNS / domain config verified if anything changed

### Migrations

- [ ] All migrations reviewed (see `migration_checklist.md`)
- [ ] Migrations tested forward + backward locally
- [ ] Long-running migrations flagged in release notes; plan to run out-of-band
- [ ] Backups verified within 24 hours

### Static assets

- [ ] Tailwind build runs in CI / build step
- [ ] Static files within size budget (CSS ≤ 50 KB gz, JS ≤ 30 KB gz)
- [ ] `collectstatic` runs successfully
- [ ] CDN / static host configured if used

### External dependencies

- [ ] No new dependencies that haven't been vetted
- [ ] Dependency security scan recent (`pip-audit` / Dependabot)
- [ ] Third-party integrations tested in staging (payment, email, SMS)

### Communication

- [ ] Stakeholders notified if release has user-visible changes
- [ ] Customer support team aware of any changes affecting their workflows
- [ ] Status page prepared for any planned maintenance

## Deploy

### Step 1 — Pre-deploy snapshot

- [ ] Database backup taken (or confirmed automated backup is recent)
- [ ] Current production version noted (for rollback reference)

### Step 2 — Migrations (if any)

- [ ] Migration plan reviewed: `python manage.py showmigrations --plan`
- [ ] Migration applied to production DB
- [ ] Migration completion verified
- [ ] If concurrent index: applied without blocking writes
- [ ] If data backfill: scheduled separately, not blocking the code deploy

### Step 3 — Code deploy

- [ ] New version deployed (matching the tested commit/tag)
- [ ] Workers restarted (Celery, Gunicorn)
- [ ] Celery beat restarted if periodic tasks changed
- [ ] Old containers / processes drained gracefully (in-flight requests complete)

### Step 4 — Verification

- [ ] Health check endpoint returns 200 (`/healthz` or equivalent)
- [ ] Home page loads correctly
- [ ] Login flow works (smoke test)
- [ ] One key feature smoke-tested
- [ ] Static assets loading (correct hashed filenames)
- [ ] HTTPS working, certificates valid
- [ ] Logs flowing to log aggregator

## Post-deploy

### Monitoring (first 30 minutes)

- [ ] Error rate in Sentry not spiking
- [ ] Response time (p50, p95) not degrading
- [ ] Worker queues not backing up
- [ ] DB connection count stable
- [ ] No new error types in logs

### Long tail (24 hours)

- [ ] Periodic tasks ran on schedule
- [ ] No spike in user-reported issues
- [ ] Email delivery normal (no bounce-rate spike)
- [ ] Background jobs completing

### Documentation

- [ ] Deploy noted in release log / changelog
- [ ] Issue tracker closed for completed items
- [ ] Tag created in git (`v0.X.Y`) and pushed
- [ ] Customers notified for completion (if applicable)

## Rollback plan

If something goes wrong:

- [ ] Identified the rollback procedure for this release
- [ ] Code-only rollback: re-deploy previous version
- [ ] With migrations: migration is reversible OR forward-fix planned
- [ ] Customer comms drafted for outage scenarios
- [ ] On-call has access and authority to roll back

## Special-case: critical release

If the release includes:

- Schema change on a critical table (users, orders, payments)
- Auth / permission changes
- Payment / billing changes
- First production deploy of a new major feature

…then also:

- [ ] Released during low-traffic window
- [ ] Second engineer monitoring alongside deploy
- [ ] Customer support team briefed on possible questions
- [ ] Sentry alert thresholds tightened for first 24h

## Anti-patterns

Stop and don't deploy if any of these are true:

- ❌ CI not green
- ❌ Migration not tested locally forward + backward
- ❌ Friday afternoon (US) / day before a holiday
- ❌ Anyone on the team is paged for an unrelated incident right now
- ❌ "I'll fix it in the next deploy" with no concrete plan
- ❌ Deploy that hasn't been tested in staging
