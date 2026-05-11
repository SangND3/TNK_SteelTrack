# Frontend checklist

Use this for template / CSS / JS / HTMX changes.

## HTML structure

- [ ] Semantic elements (`<button>`, `<header>`, `<nav>`, `<main>`, `<form>`)
- [ ] One `<h1>` per page; heading levels in order
- [ ] Real `<form>` for form submits (even when HTMX-enhanced)
- [ ] `<button type="button">` unless inside a form for submit
- [ ] Lists use `<ul>` / `<ol>` / `<li>`
- [ ] Tables use `<table>` only for tabular data; with `<th scope="...">` and `<caption>`

## Accessibility

- [ ] Every `<input>` has a `<label>` (placeholder is not a label)
- [ ] Every `<img>` has `alt` (empty `alt=""` for decorative)
- [ ] Icon-only buttons have `aria-label`
- [ ] Keyboard navigation works (Tab through all interactive elements)
- [ ] Focus states visible (Tailwind `focus:` and `focus-visible:`)
- [ ] Tab order matches visual order
- [ ] Color contrast ≥ 4.5:1 (text), ≥ 3:1 (UI)
- [ ] No information conveyed by color alone
- [ ] Form errors linked via `aria-describedby`, `aria-invalid`
- [ ] HTMX swaps with dynamic content use `aria-live="polite"` (or `assertive` for errors)
- [ ] Modals trap focus (use `<dialog>` or `inert`)
- [ ] Skip-to-content link present and visible on focus
- [ ] Respects `prefers-reduced-motion` for animations
- [ ] Works at 200% zoom without horizontal scroll

## Tailwind

- [ ] Utilities sorted (formatter)
- [ ] No arbitrary values (`text-[#...]`) without justification
- [ ] No `!important`
- [ ] No inline `style="..."` (except for truly dynamic values)
- [ ] Repeating utility groups (3+ uses) extracted to component class or partial
- [ ] Brand colors from design tokens, not raw hex
- [ ] Responsive variants (`sm:`, `md:`, `lg:`) mobile-first
- [ ] Dark-mode variants (`dark:`) if dark mode supported

## HTMX

- [ ] `hx-target` explicit (don't rely on defaults)
- [ ] `hx-swap` explicit (default `innerHTML` not always what you want)
- [ ] CSRF token configured globally in `base.html` via `hx-headers`
- [ ] Loading indicator (`hx-indicator`) for slow actions
- [ ] `hx-disabled-elt` on submit buttons to prevent double-submit
- [ ] `hx-confirm` for destructive actions
- [ ] Returns HTML fragment (not JSON) from HTMX endpoint
- [ ] Form errors re-render the form partial with bound `form`
- [ ] `HX-Trigger` for client-side events (toast, refresh)
- [ ] Stable IDs on swap targets (e.g., `#order-{{ public_id }}`)

## Templates

- [ ] Full-page templates extend `base.html`
- [ ] Partials never extend a layout
- [ ] `{% include %}` uses explicit `with var=val`
- [ ] No business logic in templates (no `{% if user.orders.filter(...) %}`)
- [ ] Strings wrapped in `{% trans %}` / `gettext()` (or noted as English-only for now)
- [ ] Custom template tags in `apps/<app>/templatetags/`

## JavaScript

- [ ] Vanilla / Alpine.js — no React/Vue
- [ ] Only used for what HTMX/HTML can't do
- [ ] Entry point `static/js/app.js`
- [ ] No external scripts not vendored or from a CDN with SRI hash
- [ ] Re-init on `htmx:afterSwap` for dynamically-inserted nodes
- [ ] `defer` attribute on non-critical scripts
- [ ] No console.log left in committed code

## Images & assets

- [ ] Compressed (CI size gate)
- [ ] `loading="lazy"` for below-the-fold
- [ ] `width` and `height` attributes (prevent layout shift)
- [ ] SVG for icons
- [ ] Hashed filename via `ManifestStaticFilesStorage` in production

## Performance

- [ ] CSS output ≤ 50 KB gzipped
- [ ] JS bundle ≤ 30 KB gzipped (HTMX ~15 KB)
- [ ] No layout shift on swap (set min-heights where needed)
- [ ] Critical above-the-fold loads without JS

## Visual check

- [ ] Looks correct at mobile width (375px)
- [ ] Looks correct at desktop (1280px+)
- [ ] Looks correct in dark mode (if supported)
- [ ] No visible layout shift on load
- [ ] No console errors in DevTools
- [ ] HTMX requests visible and returning expected partials (DevTools Network)
