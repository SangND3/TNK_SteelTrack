# Security checklist

Walk this for every PR that touches auth, input, storage, or output. For purely cosmetic changes, the relevant subset (output encoding) still applies.

## Authentication

- [ ] No custom password handling (Django auth only)
- [ ] Passwords hashed with default (Argon2)
- [ ] Auth endpoint rate-limited (`@ratelimit`)
- [ ] Sessions: `HttpOnly` + `Secure` + `SameSite=Lax` minimum
- [ ] Login does not reveal whether email exists (constant response shape)
- [ ] Password reset tokens single-use, ≤ 24h TTL, hashed at rest
- [ ] Constant-time comparison (`hmac.compare_digest`) for tokens
- [ ] Sessions invalidated on password change

## Authorization

- [ ] `@login_required` on every protected view
- [ ] Object-level: queryset scoped by user/owner before `.get()`
- [ ] Admin actions require staff/superuser
- [ ] DRF: `permission_classes` set on viewset
- [ ] Returns 404 (not 403) for ownership mismatch (avoid leaking existence)
- [ ] No "hidden" authorization (relying on JS-hidden buttons)

## Input validation

- [ ] All input through Form or Serializer
- [ ] Types validated (int, email, URL, date)
- [ ] Length / range limits
- [ ] File uploads: type (magic bytes), size, filename sanitized
- [ ] No mass assignment (no `Meta.fields = "__all__"` on user-input forms)

## Injection

- [ ] All queries via ORM, or raw SQL with parameter substitution
- [ ] No string concatenation into SQL / shell / HTML
- [ ] Template auto-escape on (no `|safe` on user content)
- [ ] User content in JS via `json_script` filter (or equivalent escape)
- [ ] No `subprocess.run(..., shell=True)` with user input

## XSS

- [ ] Output auto-escaped (Django template default)
- [ ] User-supplied HTML (rich text) sanitized via `bleach`
- [ ] User-supplied URLs validated against allowed schemes (`http`, `https`)
- [ ] SVG uploads sanitized (SVG can carry script)

## CSRF

- [ ] CSRF middleware enabled
- [ ] No `@csrf_exempt` without justification (webhook with signature check is an OK case)
- [ ] HTMX has CSRF token in `hx-headers` globally
- [ ] JSON API uses token auth (not session) where CSRF doesn't apply, OR includes CSRF for session-auth callers

## Open redirect

- [ ] Redirect targets validated via `url_has_allowed_host_and_scheme(...)` or allowlist
- [ ] `?next=` / `?return_to=` not redirected to without validation

## SSRF (for endpoints that fetch user-supplied URLs)

- [ ] URL validated against allowlist
- [ ] Private IPs blocked (10.0.0.0/8, 172.16/12, 192.168/16, 127/8, 169.254/16, fc00::/7)
- [ ] Timeout set (connect + read)
- [ ] Max response size enforced
- [ ] Redirects to other schemes blocked

## Headers (production)

- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SECURE_HSTS_SECONDS = 31536000`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF = True`
- [ ] `X_FRAME_OPTIONS = "DENY"` (or CSP `frame-ancestors`)
- [ ] `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"`
- [ ] Content-Security-Policy set (strict; loosen with justification)

## Secrets

- [ ] No hardcoded secrets in code (passwords, tokens, keys, signing secrets)
- [ ] New secrets added to production secret manager
- [ ] New env vars documented in `.env.example` (with placeholder values)
- [ ] No secrets in error pages / logs / commit messages
- [ ] `detect-secrets` pre-commit hook passes

## Logging

- [ ] No passwords / tokens / full PII / payment data logged
- [ ] Structured logging (JSON in prod)
- [ ] Stack traces only to Sentry, not user
- [ ] Generic 500 page in production with a request ID

## File uploads

- [ ] Type checked via magic bytes (not just extension)
- [ ] Size limit enforced before reading into memory
- [ ] Filename sanitized (no `../`, no special chars, no leading dots)
- [ ] Stored in object storage (S3/R2/MinIO), not local FS
- [ ] Served with `Content-Disposition: attachment` (prevent inline HTML/SVG render)
- [ ] Scanned for malware if from untrusted source

## Cryptography

- [ ] Stdlib / Django `signing` — no custom crypto
- [ ] Tokens via `secrets.token_urlsafe(32)`
- [ ] HMAC via `hmac.compare_digest`
- [ ] No MD5 / SHA-1 for security-sensitive uses (passwords, signatures)

## Webhooks (incoming)

- [ ] Signature verified before processing
- [ ] Idempotency by webhook ID (deduplicate)
- [ ] Payload validated like any user input
- [ ] No CSRF exemption without signature check

## Dependencies

- [ ] New dep: maintained, popular enough, license OK
- [ ] Pinned version in `requirements/*.txt`
- [ ] `pip-audit` / Dependabot configured and recent run is green

## Error handling

- [ ] No detailed error messages to user in production
- [ ] No DB schema / column names / paths in error messages
- [ ] Errors logged with enough context for debugging

## Audit

- [ ] Critical actions (password change, permission change, payment) leave an audit trail
- [ ] Audit log is append-only (no UPDATE / DELETE on audit table)
