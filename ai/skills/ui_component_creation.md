# Skill: UI component creation

How to build a reusable UI element that ships consistent design and accessibility.

## Decision: where does it live?

| What it is                                | Where                                          |
| ----------------------------------------- | ---------------------------------------------- |
| Single-use chunk of one page              | Inline in the page template                    |
| Reused across an app                      | `templates/<app>/partials/<name>.html`         |
| Reused across multiple apps               | `templates/components/<name>.html`             |
| Repeating utility class group (3+ uses)   | `@apply` in `static/src/input.css`             |
| Logic-heavy template snippet              | Custom template tag in `apps/<app>/templatetags/` |

## Step 1 — Find what exists

Before building anything, grep:

```bash
grep -r "btn" templates/        # is there already a button component?
grep -r "modal" templates/      # is there a modal pattern?
```

Don't build a third "primary button" — extend the existing one.

## Step 2 — Design the API

A component has inputs (context variables) and behavior (CSS classes, JS hooks). Sketch:

```
button.html
  inputs:
    - label       (required)
    - variant     (primary | secondary | danger, default primary)
    - size        (sm | md | lg, default md)
    - disabled    (bool, default False)
    - type        (button | submit, default button)
    - hx_attrs    (dict of HTMX attributes, optional)
  outputs:
    - <button> with appropriate classes
```

If your component takes 8+ inputs, it's probably doing too much. Split.

## Step 3 — Build the template

```django
{# templates/components/button.html #}
{# Usage: {% include "components/button.html" with label="Save" variant="primary" %} #}

<button
  type="{{ type|default:'button' }}"
  class="btn btn-{{ variant|default:'primary' }} btn-{{ size|default:'md' }}"
  {% if disabled %}disabled{% endif %}
  {% for k, v in hx_attrs.items %}{{ k }}="{{ v }}" {% endfor %}
>
  {{ label }}
</button>
```

With component CSS (in `static/src/input.css`):

```css
@layer components {
  .btn {
    @apply inline-flex items-center justify-center font-medium rounded-md
           focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed
           transition-colors;
  }
  .btn-sm { @apply px-2.5 py-1.5 text-sm; }
  .btn-md { @apply px-4 py-2 text-base; }
  .btn-lg { @apply px-6 py-3 text-lg; }

  .btn-primary   { @apply bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500; }
  .btn-secondary { @apply bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-gray-400; }
  .btn-danger    { @apply bg-danger text-white hover:bg-red-700 focus:ring-red-500; }
}
```

## Step 4 — Accessibility (per `ACCESSIBILITY_RULES.md`)

- Use the right element (`<button>` for buttons, `<a>` for links)
- Focus state visible (the `focus:ring-2` above does this)
- Color contrast meets AA
- If icon-only, include `aria-label`
- Don't disable submit during typing
- Keyboard support (Tab, Enter, Space — `<button>` does this natively)

## Step 5 — Document inline

Add a usage comment at the top:

```django
{#
  components/button.html

  Reusable button component.

  Usage:
    {% include "components/button.html" with label="Save" variant="primary" %}

  Inputs:
    - label    (str, required)
    - variant  (str: primary | secondary | danger; default primary)
    - size     (str: sm | md | lg; default md)
    - disabled (bool; default False)
    - type     (str: button | submit; default button)
    - hx_attrs (dict of HTMX attributes, optional)
#}
```

## Step 6 — Test

Components don't usually have unit tests, but verify:

- [ ] Renders correctly with default inputs
- [ ] Renders correctly with each variant
- [ ] Keyboard navigable
- [ ] Focus visible
- [ ] Screen reader announces correctly (use VoiceOver / NVDA)
- [ ] Works at zoom 200%
- [ ] Works on touch (tap target ≥ 44×44px for mobile)

A Storybook-like preview page can help for visual testing:

```django
{# templates/dev/component_preview.html — dev-only URL #}
<h2>Buttons</h2>
{% include "components/button.html" with label="Primary" variant="primary" %}
{% include "components/button.html" with label="Secondary" variant="secondary" %}
{% include "components/button.html" with label="Danger" variant="danger" %}
{% include "components/button.html" with label="Disabled" disabled=True %}
```

## Patterns

### Modal

Use native `<dialog>` when possible:

```django
{# components/modal.html #}
<dialog id="{{ id }}" class="rounded-lg p-0 backdrop:bg-black/40">
  <div class="p-6">
    <h2 class="text-lg font-medium">{{ title }}</h2>
    <div class="mt-4">{{ body|safe }}</div>
    <form method="dialog" class="mt-6 flex justify-end gap-2">
      <button class="btn-secondary">Cancel</button>
    </form>
  </div>
</dialog>
```

Open with JS or HTMX after-swap.

### Form field

```django
{# components/form_field.html #}
<div class="mb-4">
  <label for="{{ field.id_for_label }}" class="block text-sm font-medium">
    {{ field.label }}
    {% if field.field.required %}<span class="text-danger" aria-hidden="true">*</span>{% endif %}
  </label>
  {{ field }}
  {% if field.help_text %}
    <p class="mt-1 text-sm text-gray-500" id="{{ field.id_for_label }}-help">{{ field.help_text }}</p>
  {% endif %}
  {% if field.errors %}
    <p class="mt-1 text-sm text-danger" role="alert" id="{{ field.id_for_label }}-error">
      {{ field.errors|first }}
    </p>
  {% endif %}
</div>
```

### Toast

See `ai/skills/htmx_interactions.md` § Pattern: toast notification.

## When to use Alpine.js

Reach for Alpine **only** when:

- The interaction is purely client-side (no server data needed)
- HTMX would require a roundtrip for something that doesn't need one
- The state is non-trivial (multiple toggles, conditional UI)

Example (a dropdown that just opens/closes):

```html
<div x-data="{ open: false }">
  <button @click="open = !open" :aria-expanded="open">Menu</button>
  <div x-show="open" @click.away="open = false" x-cloak>
    <a href="...">Item 1</a>
  </div>
</div>
```

For simple show/hide, prefer `<details>` / `<summary>` — no JS at all.

## Anti-patterns

- ❌ A "component" that's a giant template with 15 conditional branches
- ❌ Inventing a new button style instead of using the existing one
- ❌ Inline styles or `!important`
- ❌ Custom JS for a feature HTMX or `<details>` handles
- ❌ Disabling focus outlines without replacement
- ❌ Icon buttons with no `aria-label`
- ❌ Building a "design system" before you have repeating components — extract from real use
