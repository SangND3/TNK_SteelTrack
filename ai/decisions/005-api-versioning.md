# ADR 005: URL-based API versioning

**Date:** 2026-05-11
**Status:** accepted

## Context

If/when we add a JSON API (DRF), we need a versioning strategy. The options:

1. **URL-based:** `/api/v1/orders/`, `/api/v2/orders/`
2. **Header-based:** `Accept: application/vnd.project.v1+json`
3. **Query parameter:** `/api/orders/?version=1`
4. **No versioning** — break clients on every change

## Decision

**URL-based versioning, starting at `v1` from the first JSON endpoint we ship.**

```
/api/v1/orders/
/api/v1/users/
```

## Rules

### 1. Start with `v1`, not `v0`

If we ship under `v0` "because it's beta", we'll regret it. Once anyone integrates, "beta" is just a label — breaking the contract still breaks them.

### 2. Never break a shipped version

Once `v1` is publicly documented and used:

- Don't change response shapes
- Don't remove fields
- Don't change validation rules to be stricter
- Don't change HTTP status codes for existing scenarios
- Don't change URL paths

Adding new optional fields, new optional query params, new endpoints — fine.

### 3. Breaking changes go into a new version

Need to rename `total` to `total_cents` and clarify units? That's a breaking change. Add `v2` with the new shape; keep `v1` running. Deprecate `v1` on a published schedule (typically 6–12 months).

### 4. Both versions run side-by-side during deprecation

Same data, possibly different views/serializers. Tests cover both.

### 5. Don't proliferate versions

Resist `v2`, `v3`, `v4` over time. The point of versioning is to allow a clean break when needed — not to ship a new version every quarter. If you need to break things twice a year, the problem is the API design.

## Why URL-based

### Pros

- Easy to inspect in logs, curl, browser
- Easy to route in nginx/Django URL conf
- No "what version did this request use?" mystery
- Clients pin to a version explicitly

### Cons

- Path looks "non-RESTful" to purists who think the same resource shouldn't have multiple URLs (we are not purists)
- Major breaks duplicate URL space

## Why not header-based

### Pros

- The URL stays "clean" / version-free
- Considered more RESTful

### Cons

- Invisible in browser address bar, harder to debug
- Caching gets fiddly (Vary: Accept header)
- Clients forget to set the header → mystery breakage when default changes
- Tooling (curl examples, OpenAPI docs, copy-paste-able URLs) is awkward
- Discovery is harder

The downside list is longer for us than the upside, so we stick with URL.

## Why not query param

Same downside as headers (cache fiddliness, accidental omission) without the upside (no "cleaner" URL).

## Why not no-versioning

For an API with one internal client (our SPA, if we had one), no-versioning is tempting — we control both sides, deploy together.

We rejected this approach because:

- The cost of being wrong about "internal-only forever" is much higher than the cost of versioning from day one
- If we ever expose the API to third parties or a mobile app, retrofitting versioning is painful
- The cost of versioning at this scale is low (1 segment in the URL)

## Consequences

### Positive

- Clients see versioning explicitly; no surprise breakage
- Can iterate freely on `v2` without affecting `v1` users
- Clean URL routing in Django

### Negative

- Slight duplication during deprecation windows (`v1` and `v2` running side by side)
- More test surface (test against both versions)

### Compliance

- All JSON APIs mounted under `/api/v1/`
- See `ai/rules/API_CONVENTION.md`
- OpenAPI schema committed at `schema.yml` per version

## When this is relevant

Currently: not at all. We have no JSON API yet — HTMX returns HTML.

This ADR exists so that **when** we add JSON APIs, we don't think about this from scratch and accidentally pick "no versioning" because "it's just one internal client".
