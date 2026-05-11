# CSS_RULES.md

Tailwind CSS, utility-first. Custom CSS only when utilities truly can't express the design.

## Core rule

If you can do it with Tailwind utilities, use utilities. If you find yourself writing custom CSS for layout/spacing/color, you're probably missing a utility.

## Order

`prettier-plugin-tailwindcss` enforces utility order. Don't fight the formatter — run it, accept its sort.

## Design tokens

Brand and semantic colors live in `tailwind.config.js`, not as `text-[#3a3a3a]` arbitrary values:

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      primary:   { 50: '#...', 500: '#...', 700: '#...' },
      surface:   { DEFAULT: '#...', muted: '#...' },
      danger:    '#...',
      success:   '#...',
    },
    spacing: {
      // Stick to default 0.25rem scale; only add custom if truly needed
    },
  },
},
```

Use semantic names (`primary`, `surface`, `danger`) in templates. If you need a one-off color, ask whether the design system is missing something.

## Avoid arbitrary values

```html
<!-- WRONG -->
<div class="text-[#3a3a3a] p-[13px] w-[427px]">

<!-- RIGHT -->
<div class="text-gray-700 p-3 w-md">
```

Arbitrary values (`[...]`) are an escape hatch, not a default. They signal "the design system doesn't cover this" — which is sometimes true, but should be rare.

## Extracting repeating patterns

When the same group of utilities appears 3+ times, choose one:

### 1. Template partial (preferred)

```django
{# templates/components/button.html #}
<button class="px-4 py-2 rounded-md bg-primary-600 text-white hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 disabled:opacity-50">
  {{ label }}
</button>
```

```django
{% include "components/button.html" with label="Save" %}
```

### 2. Component class via @apply

```css
/* static/src/input.css */
@layer components {
  .btn {
    @apply inline-flex items-center px-4 py-2 rounded-md font-medium
           focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed;
  }
  .btn-primary {
    @apply btn bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500;
  }
  .btn-secondary {
    @apply btn bg-surface text-gray-700 hover:bg-surface-muted focus:ring-gray-400;
  }
}
```

```html
<button class="btn-primary">Save</button>
```

Use `@apply` for truly cross-cutting patterns (buttons, form inputs, cards). Don't over-apply — Tailwind's whole point is keeping styling local.

## Responsive

Mobile-first:

```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

Always design for mobile first; add breakpoint variants for larger screens.

Breakpoints:

- `sm:` ≥ 640px
- `md:` ≥ 768px
- `lg:` ≥ 1024px
- `xl:` ≥ 1280px
- `2xl:` ≥ 1536px

## Dark mode

If supported, use `dark:` variants from day one. Retrofitting is painful.

Strategy: `class` (toggle via JS, persist preference) rather than `media` (follows OS only).

```html
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
```

## State variants

```html
<button class="bg-primary-600 hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 active:bg-primary-800 disabled:opacity-50">
```

- `hover:` — pointer over
- `focus:` and `focus-visible:` — focus state; **always include**
- `active:` — being clicked
- `disabled:` — disabled state
- `group-hover:` / `peer-checked:` — parent/sibling state

Focus states are not optional. See `ai/rules/ACCESSIBILITY_RULES.md`.

## Spacing scale

Stick to Tailwind's `0.25rem` scale: `p-1` (4px), `p-2` (8px), `p-4` (16px), `p-8` (32px).

Don't invent half-step custom spacing without a design reason.

## Forbidden / discouraged

- ❌ `!important` — sign you're fighting the system
- ❌ Inline `style="..."` — except for truly dynamic values (e.g., `width: {{ progress }}%`)
- ❌ Mixing CSS frameworks (no Bootstrap on top of Tailwind)
- ❌ Custom resets (Tailwind's preflight is enough)
- ❌ Long arbitrary value lists — extract to component class instead

## Build & output

- Source: `static/src/input.css`
- Output: `static/css/output.css`
- Dev: `make tailwind` (watch mode)
- Production: built via CI, hashed via Django's `ManifestStaticFilesStorage`

## File structure

```
static/
├── src/
│   └── input.css            # @tailwind directives + component classes
└── css/
    └── output.css           # generated, .gitignored
```

`input.css` example:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  /* shared component classes */
}

@layer utilities {
  /* one-off utilities not in Tailwind */
}
```

## Performance

- Tailwind's JIT keeps output small — verify in CI (`output.css` ≤ 50 KB gzipped)
- Purge unused classes by listing all template paths in `tailwind.config.js` `content`:

```js
content: [
  './templates/**/*.html',
  './apps/**/templates/**/*.html',
  './static/js/**/*.js',
],
```

Missing paths = utilities silently stripped from production.

## Linting

`stylelint` is overkill for utility-first. Rely on:

- `prettier-plugin-tailwindcss` for ordering
- Manual review for `@apply` blocks
- CI check for bundle size
