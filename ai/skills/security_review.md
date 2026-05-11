# Skill: Security review

How to review code for security issues — yours or someone else's.

## Mindset

Assume:

- All user input is hostile
- All third-party data is hostile
- All "internal" services may be reached from outside someday
- Future developers won't read this code carefully
- The attacker has read the entire codebase (we open-source-by-default the *thinking*; only secrets are secret)

## Process

For any code change touching auth, input, storage, or output:

1. **Trace the data flow** — input → validation → storage → output. Where does it come from? Where does it go?
2. **Walk the threat checklist** below
3. **Check ownership** — who can access this? Is that checked server-side?
4. **Check the failure path** — what does this leak on error?

## Threat checklist

### Authentication

- [ ] New auth endpoint? Rate limited (e.g., 5/min)?
- [ ] Password storage uses Django's hasher (Argon2 / bcrypt)?
- [ ] Reset tokens single-use + short-lived?
- [ ] Session cookies `HttpOnly`, `Secure`, `SameSite=Lax`?
- [ ] No constant-time comparison bypass (use `hmac.compare_digest`)?

### Authorization

- [ ] Every protected view checks login (`@login_required` or middleware)?
- [ ] Object-level: queryset scoped by owner before `.get()`?

```python
# WRONG — any logged-in user can access any order
order = Order.objects.get(public_id=public_id)

# RIGHT
order = get_object_or_404(
    Order.objects.filter(user=request.user),
    public_id=public_id,
)
```

- [ ] Admin-only views check role?
- [ ] DRF: permission classes set on the viewset?
- [ ] No client-side authorization (hidden buttons don't count)?

### Input validation

- [ ] All input through Form / Serializer?
- [ ] Types validated (int, email, URL)?
- [ ] Length limits set?
- [ ] Range / value constraints?
- [ ] File uploads: type + size + filename validated?

### SQL injection

- [ ] All queries through ORM?
- [ ] If raw SQL, parameterized (`%s`), not f-string?
- [ ] No `extra(where=...)` with user input?

```python
# WRONG
Order.objects.raw(f"SELECT * FROM orders WHERE email = '{email}'")

# RIGHT
Order.objects.raw("SELECT * FROM orders WHERE email = %s", [email])
```

### XSS

- [ ] Template auto-escape on (Django default)?
- [ ] No `|safe` on user-controlled content?
- [ ] If rich text accepted, sanitized with `bleach`?
- [ ] User content not echoed in JS without JSON-encoding?

```django
{# WRONG — XSS #}
<script>
  var name = "{{ user.name }}";
</script>

{# RIGHT — json_script tag escapes safely #}
{{ user.name|json_script:"user-name" }}
<script>
  var name = JSON.parse(document.getElementById("user-name").textContent);
</script>
```

### CSRF

- [ ] CSRF middleware enabled?
- [ ] HTMX has CSRF in `hx-headers` (set in `base.html`)?
- [ ] No `@csrf_exempt` without justification?

### Secrets

- [ ] No hardcoded passwords, tokens, keys, URLs with credentials?
- [ ] New secrets added to `.env.example` (with placeholder values)?
- [ ] Production reads from secret manager, not `.env`?

### Logging

- [ ] No password / token / full PII / payment data logged?
- [ ] Stack traces only to Sentry / logs, never to user?
- [ ] Generic 500 page in production (no schema / path leaks)?

### File uploads

- [ ] File type validated by magic bytes (not just extension)?
- [ ] Size limit enforced before reading?
- [ ] Filename sanitized (no `../`, no special chars)?
- [ ] Stored in object storage, not web root?
- [ ] Served with `Content-Disposition: attachment` if user-uploaded?

### URL parameters

- [ ] No sensitive data in URL (logs, browser history, referer leak)?
- [ ] Open redirect prevented (validate redirect target)?

```python
# WRONG — open redirect
return redirect(request.GET.get("next"))

# RIGHT
from django.utils.http import url_has_allowed_host_and_scheme
next_url = request.GET.get("next")
if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
    return redirect(next_url)
return redirect("home")
```

### SSRF (server-side request forgery)

When the server fetches a URL on behalf of users:

- [ ] URL validated against allowlist?
- [ ] Private IPs blocked (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16, fc00::/7)?
- [ ] Timeout set (connect + read)?
- [ ] Max response size enforced?
- [ ] Redirects to other schemes blocked?

### Webhooks (incoming)

- [ ] Signature verified (`hmac.compare_digest`)?
- [ ] Idempotency: duplicate webhook IDs handled?
- [ ] Payload validated like any user input?

### Dependencies

- [ ] New dep: vetted, maintained, reasonable license?
- [ ] Pinned to specific version?
- [ ] `pip-audit` / Dependabot configured to alert on CVEs?

### Cryptography

- [ ] Using stdlib / Django, not custom?
- [ ] Tokens use `secrets.token_urlsafe(32)`?
- [ ] HMAC uses `hmac.compare_digest`?
- [ ] No MD5 / SHA-1 for security?

## Code patterns to flag

### Permission missing

```python
def order_detail_view(request, public_id):
    order = Order.objects.get(public_id=public_id)  # 🚨 no ownership check
    return render(request, "orders/detail.html", {"order": order})
```

### Mass assignment

```python
# 🚨 user can set is_admin=True
user.__dict__.update(request.POST)

# 🚨 ModelForm with `fields = "__all__"` lets user submit any field
class UserForm(ModelForm):
    class Meta:
        model = User
        fields = "__all__"  # includes is_admin, is_staff, ...
```

### Timing attack

```python
# 🚨 != is not constant-time
if token != stored_token:
    raise PermissionDenied()

# RIGHT
import hmac
if not hmac.compare_digest(token, stored_token):
    raise PermissionDenied()
```

### Insecure direct object reference (IDOR)

```python
# 🚨 user can fetch any document by guessing IDs
def doc_view(request, doc_id):
    doc = Document.objects.get(id=doc_id)
```

## Tools

- **bandit** — automated Python security linter (catches some patterns)
- **pip-audit** — checks deps against known CVEs
- **safety** — alternative to pip-audit
- **detect-secrets** — pre-commit hook to catch committed secrets
- **OWASP ZAP** — DAST scanning of running app (in CI on staging)

## When you find an issue

In code review:

```
[Blocker — Security] This endpoint doesn't check that the user owns the order.
Any authenticated user can read any order by guessing public_id.

Fix: scope the queryset by user before .get():

    order = get_object_or_404(
        Order.objects.filter(user=request.user),
        public_id=public_id,
    )
```

If already in production:

1. Don't post details in public channels
2. Patch + deploy ASAP
3. Assess blast radius (was it exploited? what data leaked?)
4. Rotate any potentially-compromised secrets
5. Postmortem (see `ai/skills/incident_analysis.md`)
