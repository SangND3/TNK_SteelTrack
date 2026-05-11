# SECURITY_RULES.md

Security is non-negotiable. These rules are not "best practices" — they are requirements.

## Secrets

- **Never commit secrets.** Not API keys, tokens, passwords, certificates, database URLs with passwords, signing keys — nothing.
- Use `.env` (gitignored) locally; secret manager in production
- Rotate any secret that lands in git history, even if you immediately deleted it — git history is forever
- `pre-commit` includes `detect-secrets`; don't bypass it

If you accidentally commit a secret:

1. Rotate the secret immediately (the old one is compromised)
2. Don't waste time scrubbing git history first — rotation matters more
3. If history scrubbing is needed, use `git filter-repo` with care

## Authentication

- Use Django's auth framework. Don't roll your own.
- Passwords: never stored plain text, never logged, never sent in responses
- Hash with the default Argon2 or bcrypt — never SHA / MD5 alone
- Session cookies: `HttpOnly`, `Secure` (HTTPS), `SameSite=Lax` minimum
- Password reset tokens: single-use, short-lived (24h max), constant-time comparison

## Authorization

- Check permissions **server-side** on every request. Always.
- Don't trust hidden form fields, JS-disabled buttons, hidden URLs
- Use Django's `permission_required` / `LoginRequiredMixin` or custom decorators
- For object-level access, check in the selector or service:

```python
def order_get(*, public_id: str, user: User) -> Order:
    return get_object_or_404(
        Order.objects.filter(user=user),  # scope by user
        public_id=public_id,
    )
```

Never write `Order.objects.get(public_id=public_id)` in a view if orders belong to users.

## Input validation

- All user input goes through a Django Form or DRF Serializer
- Validate on the server. Client-side validation is convenience, not security.
- Validate types, ranges, lengths, formats
- Reject early; don't try to sanitize unsafe input — refuse it

## Output encoding

- Django templates auto-escape by default — don't disable with `|safe` casually
- For user-controlled HTML (rich text), sanitize with `bleach` or similar
- For SQL: ORM parameterization (never string-concatenate user input into SQL)
- For shell commands: don't shell out. If you must, use `subprocess` with a list of args, never `shell=True` with user input.
- For file paths: validate against a whitelist; never trust filenames from users

## CSRF

- Enabled globally; don't disable per-view without strong reason
- HTMX: set CSRF in `hx-headers` (see `ai/rules/HTMX_RULES.md`)
- JSON APIs: use token auth (CSRF not relevant for token auth), or include CSRF in session-auth API calls

## Headers (production)

Set in `config/settings/production.py`:

- `SECURE_SSL_REDIRECT = True`
- `SECURE_HSTS_SECONDS = 31536000` (1 year)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_HSTS_PRELOAD = True` (only after submitting to HSTS preload list)
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_CONTENT_TYPE_NOSNIFF = True`
- `X_FRAME_OPTIONS = "DENY"` (or set Content-Security-Policy frame-ancestors)
- `SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"`

Set a Content Security Policy. Start strict and loosen only with justification.

## Rate limiting

Apply on:

- Auth endpoints (login, signup, password reset) — tight: e.g., 5/min/IP, 20/hour/IP
- Search and other expensive endpoints
- Public APIs

Use `django-ratelimit` or DRF throttling.

## File uploads

- Validate type (don't trust `Content-Type`; check magic bytes)
- Validate size before reading into memory
- Validate filename — strip path components, reject suspicious extensions
- Store uploads outside the web root (object storage)
- Scan for malware if accepting from untrusted sources
- Serve via `Content-Disposition: attachment` to prevent inline rendering of HTML/SVG

## Logging

- **Never log:** passwords, full credit card numbers, SSNs, API tokens, OAuth bearer tokens, full PII
- **OK to log:** user IDs, request IDs, request paths, error types
- Use structured logging (JSON in production) so logs are queryable
- Configure Sentry / log aggregator to scrub known sensitive fields

## Errors

- In production: generic error page, no stack traces, with a request ID
- In dev: full stack trace OK
- Never echo back user input in error messages without escaping
- Don't expose internal IDs, table names, or schema details in errors

## Dependencies

- Track in `requirements/*.txt` (pinned)
- Run `pip-audit` or Dependabot weekly
- Update on security advisories; never sit on a CVE
- Vet new dependencies: maintenance, popularity, license

## Cryptography

- Use the standard library / Django's `signing` — don't write your own crypto
- For tokens: `secrets.token_urlsafe(32)` minimum
- For HMAC: `hmac.compare_digest` for constant-time comparison
- Never use MD5 or SHA-1 for anything security-related (passwords, signatures, tokens)

## SQL

- Use the ORM. Always.
- If raw SQL is absolutely necessary, use parameter substitution:

```python
# WRONG
Order.objects.raw(f"SELECT * FROM orders WHERE email = '{email}'")

# RIGHT
Order.objects.raw("SELECT * FROM orders WHERE email = %s", [email])
```

## SSRF

When the server makes outgoing HTTP requests on behalf of users:

- Validate destination URL against an allowlist or reject private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, fc00::/7)
- Don't follow redirects to other schemes
- Set timeouts (connect + read)
- Limit response size before reading into memory

## Webhooks (receiving)

- Verify signatures (HMAC or provider-specific)
- Use `hmac.compare_digest` for the signature check
- Reject duplicates by webhook ID (idempotency)
- Don't trust payload content — validate like any user input

## Code review for security

Every PR is reviewed for:

- New endpoints: permissions checked?
- New fields: PII? logged?
- New inputs: validated?
- New SQL: parameterized?
- New file uploads: type and size validated?
- New dependencies: vetted?
- New env vars: documented in `.env.example`?

See `ai/checklists/security_checklist.md`.

## Incident response

If you suspect a security issue:

1. Don't post details in public channels
2. Notify the project owner directly
3. Treat related secrets as compromised until proven otherwise
4. Write a postmortem after resolution (see `ai/skills/incident_analysis.md`)
