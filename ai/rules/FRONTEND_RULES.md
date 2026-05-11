# FRONTEND_RULES.md

The high-level philosophy. For specifics, see:

- `ai/rules/HTMX_RULES.md` — HTMX patterns
- `ai/rules/CSS_RULES.md` — Tailwind conventions
- `ai/rules/ACCESSIBILITY_RULES.md` — a11y requirements

## Philosophy

1. **HTML first.** Every feature should work without JavaScript when feasible.
2. **HTMX for interactivity.** Server-driven; no client-side state.
3. **Tailwind for styling.** Utility-first; custom CSS only when utilities run out.
4. **JS for what HTML/HTMX can't do.** Date pickers, charts, drag-drop. Keep it tiny.

If you reach for React, Vue, or a build pipeline beyond Tailwind: stop. Reconsider. This project does not have an SPA. See `ai/decisions/001-why-htmx.md`.

## HTML

- Use semantic elements: `<header>`, `<main>`, `<nav>`, `<article>`, `<section>`, `<button>` — not `<div onclick>`
- Real `<form>` with `action` and `method`, even when HTMX-enhanced
- Don't nest `<button>` inside `<a>` or vice versa
- Use `<dialog>` for modals when browser support is sufficient (it is for our targets)
- Use `<details>` / `<summary>` for show/hide instead of JS

## Templates

```
templates/
├── base.html                    # <html>, <head>, layout
├── components/                  # Reusable cross-app partials
│   ├── navbar.html
│   ├── modal.html
│   └── toast.html
├── pages/                       # Static-ish pages (about, terms)
└── <app>/
    ├── list.html                # Full-page views
    ├── detail.html
    └── partials/                # App-specific HTMX fragments
        ├── order_row.html
        └── order_form.html
```

### Conventions

- Full-page templates extend `base.html`
- Partials never extend a layout — they render into an `hx-target`
- Pass everything via context (avoid template-tag tricks)
- Use `{% include %}` with explicit `with`:

```django
{% include "orders/partials/order_row.html" with order=order editable=True %}
```

### Block structure of `base.html`

```django
<!DOCTYPE html>
<html lang="{{ LANGUAGE_CODE|default:'en' }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}{{ site_name }}{% endblock %}</title>
  <link rel="stylesheet" href="{% static 'css/output.css' %}">
  {% block extra_head %}{% endblock %}
</head>
<body hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}' hx-boost="true">
  {% include "components/navbar.html" %}
  <main id="main" class="...">
    {% block content %}{% endblock %}
  </main>
  {% include "components/toast_container.html" %}
  <script defer src="{% static 'js/vendor/htmx.min.js' %}"></script>
  <script defer src="{% static 'js/app.js' %}"></script>
  {% block extra_js %}{% endblock %}
</body>
</html>
```

## JavaScript

### When to write JS

- Browser API features: clipboard, geolocation, file picker, intersection observer
- Pure client interactions: tooltips, dropdowns (if HTML's `<details>` doesn't fit), drag-and-drop
- Input formatting: phone, currency masks

### When NOT to write JS

- Fetching data → use HTMX
- Anything depending on server state → use HTMX
- "Just to make it feel snappy" → HTMX with optimistic swaps does this

### How to write it

- Vanilla first. Alpine.js *only* if state grows complex enough to justify it.
- One entry point: `static/js/app.js`. Modules via native ES modules.
- No build step (no webpack, no esbuild) unless absolutely necessary.
- Listen for `htmx:afterSwap` to bind dynamically inserted content:

```js
document.body.addEventListener("htmx:afterSwap", (e) => {
  initWidgets(e.detail.target);
});
```

## Forms

- Use Django's `Form` and `ModelForm` — they integrate with HTMX cleanly
- Server-side validation is the source of truth; client-side is convenience only
- Show errors inline next to each field
- Use the `aria-describedby` attribute linking input to its error message

## Component reuse

If a chunk of markup repeats 3+ times, extract:

1. **Template partial** — preferred. `{% include "components/x.html" with ... %}`
2. **Template tag** — for parameterized partials with logic
3. **Tailwind component class** via `@apply` in `static/src/input.css` — for utility groupings

## Images and assets

- Compress before commit (CI checks size)
- Use `<img loading="lazy">` for below-the-fold images
- Always include `alt` (empty `alt=""` for purely decorative)
- Use `width` and `height` attributes to prevent layout shift
- SVG for icons (inline or via `<svg>` includes)

## Performance budgets

- CSS bundle: ≤ 50 KB gzipped
- JS bundle: ≤ 30 KB gzipped (HTMX itself is ~15 KB)
- Largest contentful paint: ≤ 2.5s on 4G
- Cumulative layout shift: ≤ 0.1

See `ai/rules/PERFORMANCE_RULES.md`.

## Internationalization

- Wrap user-facing strings in `{% trans %}` or `gettext()` from day one
- Don't concatenate translated strings (word order varies by language)
- Use `{% blocktrans %}` for strings with variables
