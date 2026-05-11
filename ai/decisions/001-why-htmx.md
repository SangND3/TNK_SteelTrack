# ADR 001: Use HTMX instead of an SPA framework

**Date:** 2026-05-11
**Status:** accepted
**Deciders:** project owner

## Context

We need a way to build dynamic UI: forms that submit without full page reload, inline edit, live search, infinite scroll, modals. The mainstream answer is a single-page application (SPA): React/Vue/Svelte + a JSON API backend.

For this project — server-rendered Django, small team / solo dev, no mobile app, no public API consumer — the SPA approach has costs disproportionate to the benefits.

## Decision

**Use HTMX. The server renders HTML. There is no SPA.**

For interactivity beyond what plain HTML offers, HTMX swaps server-rendered fragments into the DOM. JavaScript is used sparingly for things HTML+HTMX cannot do (drag-drop, charts, clipboard).

## Alternatives considered

### React (or Vue / Svelte / etc.) + DRF

What we'd get:

- Industry-standard, deep ecosystem
- Hiring pool is huge
- Fast perceived navigation once loaded

What we'd pay:

- Two codebases to maintain (Django + frontend project)
- Two languages, two test stacks, two deploy pipelines
- Frontend build step (webpack/vite/etc.), node_modules, lockfiles
- Data fetching layer (TanStack Query, SWR, RTK), client state library if state grows
- Forms — re-implement validation client-side, must mirror server
- Re-implement permission UI on client (server still authoritative)
- Routing on the client AND on the server
- Auth flow across two systems

For our scope, this is several months of work that doesn't ship product features.

### Inertia.js / Livewire / Hotwire / Phoenix LiveView

Reasonable alternatives in this design space. We chose HTMX because:

- It's framework-agnostic (no Rails/Laravel/Phoenix lock-in)
- It's tiny (~15 KB)
- It works fine with Django out of the box (with `django-htmx`)
- It doesn't require a persistent connection (Livewire/LiveView do)
- It's simpler conceptually — no virtual DOM, no reactive scope

### Pure server-rendered with form submits (no HTMX)

What we'd get:

- Simplest possible architecture
- No JS at all

What we'd pay:

- Full page reload on every action
- Modern UX expectations not met
- Some interactions effectively impossible (live search, infinite scroll)

HTMX gives us 90% of the SPA UX with 10% of the complexity.

## Consequences

### Positive

- One codebase, one language, one test stack
- Forms and validation live in one place (server)
- Permission logic only on the server
- Page weight is small (no JS framework)
- New contributors don't need to learn a frontend framework
- Server-side rendering = good SEO out of the box

### Negative

- Each HTMX action is a server roundtrip (~50–200ms; acceptable on good infra)
- "Offline mode" and "rich client-side state" are hard. If we ever need either, we'd revisit.
- Some optimistic-update patterns from SPA-land are awkward
- Drag-and-drop, complex animations, real-time collab still need JS
- Smaller (but growing) ecosystem and Q&A pool than React

### Reversibility

If we ever need a true SPA (e.g., we add a mobile app and want shared codebase), we can introduce DRF endpoints for JSON consumers. The Django service/selector layers stay; we add an API layer on top.

We do **not** plan to migrate the web UI to an SPA. The cost of doing so should not be paid speculatively.

## Compliance

- All new browser-facing endpoints return HTML
- DRF endpoints exist only for documented JSON consumers (none yet)
- See `ai/rules/API_CONVENTION.md`, `ai/rules/HTMX_RULES.md`
