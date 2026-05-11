# Feature map: Notifications

> **Status:** template. Fill in actual file paths and decisions as you build the notifications feature.

## Scope

This feature covers:

- Transactional emails (account, billing, order confirmations)
- In-app notifications (bell icon, notification list)
- User preferences (which channels for which events)
- Digest emails (daily / weekly summary)

Not in scope (separate features):

- Marketing emails / newsletters → external tool
- SMS / push (planned but not in MVP)
- Webhooks for third-parties → see `webhooks.md` (TBD)

## Where it lives

| Concern              | Location                                                     |
| -------------------- | ------------------------------------------------------------ |
| Notification model   | `apps/notifications/models.py` — `Notification`, `Preference`|
| Service              | `apps/notifications/services.py`                             |
| Selectors            | `apps/notifications/selectors.py`                            |
| Tasks                | `apps/notifications/tasks.py` — Celery senders               |
| Email templates      | `templates/notifications/emails/<event>/`                    |
| In-app templates     | `templates/notifications/partials/`                          |
| Views                | `apps/notifications/views.py`                                |
| URLs                 | `apps/notifications/urls.py`                                 |

## Architecture

One service interface, many channels:

```
service.notify(user, event, **context)
        │
        ├── reads user preferences for this event
        ├── if email enabled: queue send_email_task
        ├── if in-app enabled: create Notification row
        └── if (future) push/sms enabled: queue respective task
```

Other apps **never** call email/push directly. They call `notify()`.

```python
# WRONG — in apps/orders/services.py
from django.core.mail import send_mail
send_mail("Your order", "...", ...)

# RIGHT
from apps.notifications.services import notify
notify(user, event="order.confirmed", order=order)
```

This means we can centralize:

- User preferences (one place to opt out)
- Throttling (don't email the same person 50x in an hour)
- Translation
- A/B testing template variants

## Key models

```
Notification (in-app)
├── user (FK, indexed)
├── event (str, e.g., "order.confirmed")
├── payload (JSONField)  # rendered context
├── read_at (nullable, db_index)
├── created_at
└── ...

NotificationPreference
├── user (FK)
├── event (str)
├── channels (list[str], e.g., ["email", "in_app"])
└── (unique together: user + event)
```

## Key business rules

- Default preferences apply if no row exists (define in `apps/notifications/defaults.py`)
- Each event has a known set of channels; user can disable but not add unsupported channels
- Critical events (security alerts) cannot be opted out of
- Email respects unsubscribe; in-app respects "muted" status
- Throttling: max N notifications per user per event per hour (configurable per event)

## Events

Centralized registry in `apps/notifications/events.py`:

```python
EVENTS = {
    "order.confirmed":       {"channels": ["email", "in_app"], "throttle": "10/hour"},
    "order.shipped":         {"channels": ["email", "in_app"], "throttle": "5/hour"},
    "billing.payment_failed":{"channels": ["email"], "critical": True},
    "security.password_changed": {"channels": ["email"], "critical": True},
    ...
}
```

When you add a new event:

1. Register in `EVENTS`
2. Add email template under `templates/notifications/emails/<event>/`
3. Add in-app template under `templates/notifications/partials/<event>.html`
4. Document in this file under § Events

## In-app delivery

HTMX-driven bell icon polls every 30 seconds:

```html
<div
  id="notification-bell"
  hx-get="{% url 'notifications:badge' %}"
  hx-trigger="every 30s"
  hx-swap="outerHTML"
>
  {% include "notifications/partials/badge.html" %}
</div>
```

On click, opens the notification panel (HTMX swap).

## Email delivery

- Send via Celery task — never block a view
- Use a transactional email provider (SendGrid / Postmark / SES); never direct SMTP from app
- Bounces/complaints handled via webhooks (`apps/notifications/webhooks.py`) → mark email as bouncing → stop sending until verified

## Tests

- `apps/notifications/tests/test_services.py` — notify() routes correctly per preferences
- `apps/notifications/tests/test_tasks.py` — email task renders templates, retries on failure
- `apps/notifications/tests/test_views.py` — list, mark-read, preferences UI

## Open items / known issues

- [ ] Push notifications planned for v2
- [ ] Digest emails not yet implemented (collect over 24h, send once)
- [ ] No localization yet — all templates in English

## Related ADRs

- `ai/decisions/00X-notifications-architecture.md` — why single `notify()` over per-channel callers

## When to update this file

- New event added
- New channel added
- Preference model changes
- Throttling strategy changes
