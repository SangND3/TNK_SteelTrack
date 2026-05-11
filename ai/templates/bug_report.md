# Bug report template

Use this when filing a bug in the issue tracker, or when communicating one to the AI to fix.

```markdown
## Summary

<One-line description of what's wrong.>

## Severity

<Pick one:>

- **S1 — Outage:** Production down, payments broken, data loss/leak
- **S2 — Degraded:** Major feature broken, latency >10× normal, error rate >5%
- **S3 — Minor:** Small feature broken, one customer affected, easy workaround

## Reproduction steps

Exact steps a reviewer can follow:

1. <step>
2. <step>
3. <step>

Expected: <what should happen>
Actual: <what does happen>

## Environment

- **Browser / device:** <e.g., Chrome 124 on macOS, Safari iOS 17, Firefox on Ubuntu>
- **URL / page:** <full URL where the bug occurs>
- **User account:** <role/permissions if relevant; do NOT paste passwords/tokens>
- **Time of occurrence:** <if intermittent>
- **Environment:** local / staging / production
- **Version:** <commit SHA or release tag if known>

## Evidence

### Error message / stack trace

```
<paste exact error message — full traceback if available>
```

### Log lines

```
<paste relevant log lines with timestamps>
```

### Screenshots / video

<attach or link>

### Sentry issue

<link if there's a Sentry issue>

## Impact

- **Users affected:** <one user / a subset / everyone>
- **Frequency:** <every time / intermittently — what %>
- **Workaround:** <is there one? what is it?>
- **First seen:** <date / time>

## Suspected cause

<Optional. If you have a hunch, share it. Don't speculate wildly — concrete observations are more useful than guesses.>

## Notes

<Anything else that might help the person fixing it.>
```

---

## Tips for good bug reports

### Reproduction is everything

A bug you can't reproduce is a bug you can't fix. If reproduction is flaky:

- Note the frequency (1 in 10? 1 in 100?)
- Note conditions that might matter (time of day, after specific actions)
- Try to reproduce in a clean session (incognito browser, different user)

### Don't paraphrase errors

Copy the **exact** error message. "Something about a null user" is useless; the actual `AttributeError: 'NoneType' object has no attribute 'email'` is gold.

### Don't include secrets

Don't paste session cookies, tokens, passwords, or full PII into bug reports. Use placeholders like `<USER_EMAIL>` or `<TOKEN>` instead.

### Provide the URL

The full URL (without secrets in query params) helps narrow the search.

### One bug per report

If you found three bugs while testing, file three reports. Combined reports get partially fixed and partially forgotten.
