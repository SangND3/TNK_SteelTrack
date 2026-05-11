# Feature map: Reporting

> **Status:** template. Fill in actual file paths and decisions as you build the reporting feature.

## Scope

This feature covers:

- Pre-built reports (dashboards) for common questions
- Export to CSV / Excel for users to take offline
- Scheduled reports emailed on a cadence
- Read-only analytics views (no writes)

Not in scope:

- Real-time streaming analytics
- Ad-hoc SQL queries by users (we'd hand off to a BI tool for that)
- ETL into a data warehouse (separate concern; out of MVP)

## Where it lives

| Concern             | Location                                                     |
| ------------------- | ------------------------------------------------------------ |
| Report selectors    | `apps/reporting/selectors.py` — read-heavy queries           |
| Dashboard views     | `apps/reporting/views.py`                                    |
| Export services     | `apps/reporting/exports.py` — CSV / XLSX generation          |
| Scheduled reports   | `apps/reporting/tasks.py` — Celery beat                      |
| Templates           | `templates/reporting/`                                       |
| URLs                | `apps/reporting/urls.py` — under `/reports/`                 |

## Design principles

- **Reporting reads, never writes.** No service in `reporting` mutates state.
- **Aggregations are precomputed** when expensive. Don't recompute on every dashboard load.
- **Exports run async** when large. Generate in Celery, store in object storage, email a link.
- **Permissions enforced server-side.** Reports show only data the user can see.

## Key patterns

### Cheap dashboards (synchronous)

For small data sets or simple aggregations:

```python
def dashboard_view(request):
    stats = order_stats_for_user(user=request.user)  # 1-2 queries
    return render(request, "reporting/dashboard.html", {"stats": stats})
```

Budget: <100ms per dashboard. If you can't hit that, precompute.

### Expensive dashboards (precomputed)

For aggregations over millions of rows:

1. Nightly Celery task computes per-user/per-org aggregates
2. Stored in a `ReportSnapshot` table (or Redis with longer TTL)
3. Dashboard reads from snapshot
4. Show "last updated: X ago" timestamp

### Exports (async)

```python
@require_http_methods(["POST"])
@login_required
def request_export(request):
    export = export_create(
        user=request.user,
        type="orders_csv",
        filters=request.POST,
    )
    return redirect("reporting:export_status", export.public_id)
```

```python
@shared_task
def generate_export(export_id):
    export = Export.objects.get(pk=export_id)
    file_url = _generate_csv(export)
    export.status = "ready"
    export.file_url = file_url
    export.save()
    send_export_ready_email.delay(export.id)
```

User sees a "preparing" page; HTMX polls for status; download link appears when ready.

### Scheduled reports

```python
# config/celery.py
beat_schedule = {
    "weekly_orders_report": {
        "task": "apps.reporting.tasks.send_weekly_orders_report",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Mon 8am
    },
}
```

Task body:

```python
@shared_task
def send_weekly_orders_report():
    for user in User.objects.filter(reports_enabled=True):
        send_user_weekly_report.delay(user.id)
```

Don't send all reports in one task — fan out so failures isolate.

## Performance notes

- Reporting queries hit hot indexes; profile before adding new dashboards
- Use materialized views (Postgres MV) for stable aggregations refreshed nightly
- Cache results in Redis with TTL matching the data freshness need
- Avoid joins across many large tables — denormalize aggregates instead

## Tests

- `apps/reporting/tests/test_selectors.py` — query correctness, filter combinations
- `apps/reporting/tests/test_exports.py` — CSV/XLSX format, large dataset chunks
- `apps/reporting/tests/test_permissions.py` — user can't see another's data

## Security

- Every report scopes queries by `request.user` (or org)
- Exports stored with signed URLs that expire (use Django's signing or pre-signed S3 URLs)
- Don't email raw data — link to the app where auth applies

## Open items / known issues

- [ ] Some dashboards still run live and exceed budget at scale
- [ ] No "shareable" reports (always per-user); future feature
- [ ] Localization of date formats not yet handled

## When to update this file

- New dashboard added
- New export type added
- Scheduled report changes cadence
- Caching strategy changes
