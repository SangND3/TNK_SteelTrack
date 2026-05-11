# ADR 004: Celery for background jobs

**Date:** 2026-05-11
**Status:** accepted

## Context

Many operations should not happen in the request/response cycle:

- Sending emails (200ms–2s of latency we don't want in the web request)
- Generating exports / reports
- Calling third-party APIs (variable latency, possible failures)
- Periodic jobs (cleanup, notifications, scheduled reports)
- Webhook delivery to external systems

We need a background-job system.

## Decision

**Use Celery with Redis as the broker.**

## Conventions

These are how we use Celery; they're stricter than Celery's defaults, but they prevent the common pitfalls.

### 1. Tasks accept IDs, not model instances

```python
# WRONG
@shared_task
def send_email(order):  # serialized = stale by the time it runs
    ...

# RIGHT
@shared_task
def send_email(order_id: int):
    order = Order.objects.get(pk=order_id)
    ...
```

Reasons: instances may be stale by execution time; FKs may have changed; Django ORM instances don't serialize cleanly.

### 2. Tasks are idempotent

A task may run twice (due to retry, broker redelivery, or human re-trigger). It must produce the same result.

Pattern: check before doing.

```python
@shared_task
def send_email(order_id):
    order = Order.objects.get(pk=order_id)
    if order.email_sent_at:
        return
    _send_email(order)
    order.email_sent_at = now()
    order.save(update_fields=["email_sent_at"])
```

### 3. Trigger via `transaction.on_commit`

Inside a service that writes:

```python
@transaction.atomic
def order_create(*, user, items):
    order = Order.objects.create(...)
    transaction.on_commit(lambda: notify_user.delay(order.id))
    return order
```

If the transaction rolls back, the task is never queued. Without `on_commit`, you might email the user about an order that was never persisted.

### 4. No external calls inside transactions

External calls (HTTP, email, S3) can hang for seconds or fail. Don't hold a DB transaction open during them. Move them to tasks instead.

### 5. Specific retry policy per task

```python
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def call_external_api(self, payload_id):
    ...
```

Tune per task. A "send welcome email" can retry 3× over 5 minutes. A "process payment" might retry differently (or not at all — payments are sensitive).

### 6. Periodic tasks via Celery beat

```python
# config/celery.py
app.conf.beat_schedule = {
    "expire_old_orders": {
        "task": "apps.orders.tasks.expire_old_orders",
        "schedule": crontab(hour=2, minute=0),  # daily 2am
    },
}
```

One source of truth for what runs when.

### 7. Hard timeouts

```python
@shared_task(time_limit=300, soft_time_limit=270)  # 5 min hard, 4.5 min soft
def generate_report(report_id):
    ...
```

Without timeouts, a hung task ties up a worker indefinitely.

### 8. Fan out instead of mega-tasks

Don't process 10,000 things in one task. Fan out: one task that schedules N child tasks.

```python
@shared_task
def send_weekly_digests():
    for user_id in User.objects.filter(digest_enabled=True).values_list("id", flat=True):
        send_user_digest.delay(user_id)
```

Failures isolate, retries don't restart the world.

## Alternatives considered

### RQ (Redis Queue)

Simpler than Celery, fewer features. Tempting for small projects. We chose Celery because:

- We expect periodic tasks (beat scheduler built-in)
- We expect retries with backoff
- The ecosystem (Flower for monitoring, integrations with Sentry/Django) is mature
- We can scale up without changing tools

### Dramatiq

Similar to Celery, simpler API. Reasonable alternative. We chose Celery for the larger community and Django integration.

### Django Q / Huey

Django-specific. Lighter weight. Less ergonomic for the patterns we need (per-task retry policies, beat schedule, monitoring).

### "Just do it in the view"

For things <50ms total, fine. For anything beyond that, blocks the request. Don't.

### Worker threads / async views

Django supports async views. Useful for I/O-bound work that doesn't need durability or retry — but for *those* requirements (which we have), you need a queue and a broker. Async views aren't a substitute for Celery.

## Consequences

### Positive

- Web requests stay fast
- Failures isolated to tasks, don't crash views
- Retry / backoff handled by the framework
- Periodic jobs in one place
- Monitoring via Flower / Sentry instrumentation

### Negative

- Operational complexity: workers + beat + broker = three more things to deploy and monitor
- Local dev requires Redis running (covered by docker-compose)
- Debugging tasks is less direct (no stack trace in the user's request)
- "Eventually consistent" UX in places — user submits, task runs later

### Compliance

- `ai/rules/BACKEND_RULES.md` § Celery tasks
- `ai/examples/backend/celery_task_example.py`
