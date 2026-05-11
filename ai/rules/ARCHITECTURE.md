# ARCHITECTURE.md

How the system is organized. The rule files describe conventions; this file describes the structure those conventions live inside.

## High-level diagram

```
┌────────────┐    ┌─────────────┐    ┌──────────────┐
│  Browser   │───▶│    Nginx    │───▶│   Gunicorn   │
│  (HTMX)    │    │             │    │   (Django)   │
└────────────┘    └─────────────┘    └──────┬───────┘
                                            │
              ┌─────────────────────────────┼─────────────────┐
              ▼                             ▼                 ▼
       ┌──────────────┐            ┌──────────────┐   ┌─────────────┐
       │  PostgreSQL  │            │    Redis     │◀──│   Celery    │
       └──────────────┘            │ cache+broker │   │   workers   │
                                   └──────────────┘   └─────────────┘
```

## Layered architecture (per app)

Inside every Django app, code is split by responsibility (HackSoft Django Styleguide):

| Layer     | File           | Responsibility                                      |
| --------- | -------------- | --------------------------------------------------- |
| Models    | `models.py`    | Data shape, simple invariants, custom managers      |
| Selectors | `selectors.py` | Read queries, complex lookups                       |
| Services  | `services.py`  | Write operations, business logic, transactions      |
| Views     | `views.py`     | HTTP/HTMX handling, orchestration only              |
| Tasks     | `tasks.py`     | Async background work                               |
| Forms     | `forms.py`     | Input validation                                    |
| URLs      | `urls.py`      | URL routing                                         |
| Admin     | `admin.py`     | Django admin config                                 |

**Rule:** if `views.py` does more than parse input, call services/selectors, and render — the logic belongs elsewhere.

Why this layout: see `ai/decisions/002-service-layer.md`.

## Request lifecycle

### Standard request

1. Nginx receives, proxies to Gunicorn
2. Django middleware (auth, CSRF, htmx detection) runs
3. URL router dispatches to view
4. View calls selector(s) to read, service(s) to write
5. View renders template, returns response

### HTMX request

Same, but:

- View detects `request.htmx`
- Returns **template partial** (just the changed fragment)
- Partials live in `templates/<app>/partials/` or `templates/components/`

See `ai/rules/HTMX_RULES.md`.

## Background jobs

- Celery worker handles async tasks (email, exports, integrations)
- Trigger from services: `send_welcome_email.delay(user_id)`
- Tasks must be **idempotent**
- Tasks accept **IDs**, not model instances
- Long-running tasks have a hard timeout
- Periodic tasks defined in `config/celery.py` via `beat_schedule`

See `ai/decisions/004-background-job-strategy.md`.

## Caching

- **Page cache:** rarely. Only for fully public, read-heavy pages.
- **Fragment cache:** for expensive partials that don't change per-user
- **Object cache:** for repeated DB lookups within a request
- Always set a TTL. Never cache forever.
- Invalidate in services or signal handlers, not in views.

## Templates

```
templates/
├── base.html                    # <html>, <head>, layout
├── components/                  # Reusable partials (cross-app)
├── pages/                       # Static-ish pages
└── <app_name>/
    ├── <view>.html              # Full pages
    └── partials/                # App-specific HTMX fragments
```

## Static files

- Tailwind: `static/src/input.css` → built to `static/css/output.css`
- HTMX: `static/js/vendor/htmx.min.js`
- Custom JS: `static/js/app.js` (entry point, kept small)
- Production: `collectstatic` → served by Nginx with hashed filenames

## Settings layout

```
config/settings/
├── base.py          # Shared
├── local.py         # Dev
├── production.py    # Prod (security, Sentry)
└── test.py          # Test (fast hasher, in-memory cache)
```

Selected via `DJANGO_SETTINGS_MODULE`. Default `config.settings.local` in dev.

## Project folder layout

```
.
├── ai/                  # AI operating manual (this folder)
├── config/              # Django project (settings, urls, wsgi, celery)
├── apps/                # Django apps, one per domain
│   ├── core/            # Shared base models, mixins, utils
│   └── <domain>/
├── templates/           # Server-rendered templates
├── static/              # CSS, JS, images
├── media/               # User uploads (gitignored)
├── compose/             # Dockerfiles per environment
├── requirements/        # base.txt, local.txt, production.txt
├── scripts/             # Helper scripts
├── docs/                # Operational docs (dev, deploy, runbooks)
├── docker-compose.yml
├── docker-compose.prod.yml
├── manage.py
├── pyproject.toml
└── README.md
```

## Environment variables

Loaded via `django-environ` from `.env`. Required keys:

- `DJANGO_SETTINGS_MODULE`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `ALLOWED_HOSTS`
- `SENTRY_DSN` (prod)

See `.env.example` for the full list. Never commit `.env`.

## What lives where (decision aid)

| If you're tempted to put...           | Put it here instead                                      |
| ------------------------------------- | -------------------------------------------------------- |
| Business logic in a view              | A service                                                |
| Complex query in a view               | A selector                                               |
| Helper method on a model              | A service or a custom manager (read-only)                |
| Long-running task in a view           | A Celery task                                            |
| Constants in random files             | App-level `constants.py` or settings                     |
| Shared abstract model                 | `apps/core/models.py`                                    |
| Custom template logic                 | `apps/<app>/templatetags/`                               |
| Cross-cutting middleware              | `apps/core/middleware.py`                                |
