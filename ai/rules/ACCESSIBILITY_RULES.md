# ACCESSIBILITY_RULES.md

Target: WCAG 2.1 Level AA. These are not optional.

## Why this matters

- Legally required in many jurisdictions
- 15-20% of users have some form of disability
- Accessible designs are better designs (clearer hierarchy, more semantic structure)
- HTMX and Tailwind don't make sites accessible — *we* do

## Semantic HTML

- Use the right element for the job: `<button>` for buttons, `<a>` for links, `<input>` for inputs
- One `<h1>` per page; don't skip heading levels (no `<h1>` → `<h3>`)
- Landmark elements: `<header>`, `<nav>`, `<main>`, `<aside>`, `<footer>` — once each
- `<button type="button">` unless it submits a form (default `type="submit"` inside forms causes accidental submits)
- Lists: `<ul>` / `<ol>` / `<li>` for actual lists, not divs

## Keyboard

- **Everything is keyboard accessible** — Tab, Shift+Tab, Enter, Space, Esc, arrow keys where appropriate
- **Tab order matches visual order** (DOM order = visual order, by default)
- **Focus visible always** — use `focus:` and `focus-visible:` Tailwind utilities, never `outline: none` without replacement
- Skip-to-content link at the top of every page

```html
<a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2">
  Skip to content
</a>
```

- Modal dialogs trap focus (use `<dialog>` element or `inert` on background)
- Escape closes modals and dropdowns

## Forms

- Every input has a `<label>`. Always.

```html
<!-- WRONG -->
<input type="email" placeholder="Email">

<!-- RIGHT -->
<label for="email">Email</label>
<input type="email" id="email" name="email">
```

- Placeholder is **not** a label — it disappears when typing
- Required fields marked with `required` attribute and visually (don't rely on color alone)
- Errors linked to inputs with `aria-describedby`:

```html
<label for="email">Email</label>
<input type="email" id="email" name="email" aria-describedby="email-error" aria-invalid="true">
<p id="email-error" class="text-danger">Please enter a valid email.</p>
```

- Group related inputs with `<fieldset>` + `<legend>`
- Don't disable submit buttons during typing — confusing for screen reader users

## Images

- Every `<img>` has `alt`:
  - Descriptive `alt` for informative images
  - Empty `alt=""` for purely decorative images
  - Skip `alt` only when the image is in a `<figure>` with `<figcaption>` describing it
- Don't use `alt="image"` or `alt="picture"` — useless
- Icons that convey meaning need accessible labels:

```html
<button aria-label="Delete order">
  <svg aria-hidden="true">...</svg>
</button>
```

`aria-hidden="true"` on the SVG prevents double-announcement.

## Color and contrast

- Text: contrast ratio ≥ 4.5:1 (AA), ≥ 7:1 (AAA)
- Large text (18pt+ or 14pt+ bold): ≥ 3:1
- UI components (form borders, focus rings): ≥ 3:1
- **Never convey information by color alone** — pair color with text, icon, or pattern
  - Red error → also has an error icon and "Error:" prefix
  - Green success → also has a checkmark
  - Required field → asterisk, not just red label

Tools: browser DevTools color picker, axe DevTools, WAVE.

## HTMX-specific

When HTMX swaps content, screen readers may not announce the change. Use ARIA live regions for important updates:

```html
<div id="toast-region" aria-live="polite" aria-atomic="true">
  <!-- toast appears here via HX-Trigger -->
</div>

<div id="error-region" aria-live="assertive">
  <!-- urgent errors -->
</div>
```

- `polite` — announce when idle (most cases)
- `assertive` — announce immediately (errors, critical alerts only)

For forms re-rendered with errors via HTMX, ensure focus moves to the first error (or the form, with the error announced).

## Motion

- Respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Tailwind supports this with `motion-reduce:` variant:

```html
<div class="transition-all duration-300 motion-reduce:transition-none">
```

- No auto-playing video with sound
- No flashing > 3 times per second (seizure risk)

## Page structure

- Page title (`<title>`) describes the page, unique per URL
- `<html lang="...">` set correctly
- Logical heading hierarchy
- ARIA landmarks correspond to semantic elements (don't add `role="navigation"` to a `<nav>` — redundant)

## Tables

- Use `<table>` for tabular data only (not layout)
- `<th>` with `scope="col"` or `scope="row"`
- `<caption>` for the table title
- Don't merge cells in ways that confuse linearization

## Testing

### Automated (catches ~30% of issues)

- **axe-core** in CI (via `playwright` or `pytest-playwright`)
- **lighthouse** for production audits
- ESLint `eslint-plugin-jsx-a11y` if you write JS

### Manual (catches the rest)

- Tab through every interactive element — can you reach everything?
- Use a screen reader for critical flows (VoiceOver on Mac, NVDA on Windows — free)
- Zoom to 200% — does layout still work?
- Disable CSS — is the page still usable?
- Use keyboard only for one full day per quarter

### Checklist per PR

See `ai/checklists/frontend_checklist.md`. Quick version:

- [ ] Tab navigation works for all new interactive elements
- [ ] Focus states are visible
- [ ] All inputs have labels
- [ ] All images have alt text
- [ ] Color contrast meets AA
- [ ] No info conveyed by color alone
- [ ] HTMX swaps with important updates have aria-live regions

## Resources

- [WCAG Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [The A11y Project Checklist](https://www.a11yproject.com/checklist/)
- [Inclusive Components](https://inclusive-components.design/) by Heydon Pickering
