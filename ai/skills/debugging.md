# Skill: Debugging

The art of figuring out *why* something is doing what it's doing. Distinct from `bug_fixing.md` (which assumes you already know what to fix).

## Mindset

- **Trust nothing.** Your mental model is wrong somewhere. That's why there's a bug.
- **Slow down.** The bug is patient. Rushing leads to wrong hypotheses.
- **Be specific.** "It's not working" is not a starting point. "POST /orders/ returns 500 when items is empty" is.

## The loop

1. **Observe.** What's the actual behavior? What were you expecting?
2. **Hypothesize.** What might explain the gap?
3. **Predict.** If hypothesis is true, then X. If false, then Y.
4. **Test.** Make the cheapest probe to differentiate.
5. **Update model.** Either accept the hypothesis or generate a new one.
6. Repeat until cause is identified.

Don't write the fix until step 5 produces "I understand."

## Tools

### Stack trace

Read it twice — top to bottom (what happened), bottom to top (what code triggered it). The line with *your code* is usually where you start; framework frames are usually fine.

### pdb / ipdb

```python
import ipdb; ipdb.set_trace()
```

When hit:

- `l` — show context
- `n` — next line
- `s` — step into function
- `c` — continue
- `p variable` — print variable
- `pp variable` — pretty-print
- `w` — where (stack)
- `u` / `d` — up / down the stack
- `q` — quit

### Print debugging

Fine *while debugging*. Don't commit. Prefix with something searchable:

```python
print(f"DBG order={order!r} items={items!r}")
```

`!r` calls `repr()` — shows types, escape chars, etc. More useful than `str()`.

Remove all `DBG` prints before committing (grep for "DBG").

### Logging

For bugs that only happen in production or staging, add `logger.debug` / `logger.info` with structured fields, deploy, observe, remove.

### Django shell

```bash
make shell
```

Reproduce in REPL — often faster than rerunning the full view.

```python
from apps.orders.services import order_create
user = User.objects.get(email="...")
order_create(user=user, items=[])  # boom — see what happens
```

### Django Debug Toolbar (dev only)

- Query count and slowest queries
- Settings dump
- Headers, session, signals
- Templates rendered with their context

Excellent for "why is this page slow" and "why is this query returning weird data".

### git bisect

When "it used to work":

```bash
git bisect start
git bisect bad                  # current state is broken
git bisect good v0.5.0          # this version worked

# git checks out a middle commit
# you test it
git bisect good   # or bad

# repeat until git finds the culprit
git bisect reset
```

You can automate with `git bisect run <script>` — `<script>` exits 0 if good, non-0 if bad.

### git log / blame

```bash
git log -p apps/orders/services.py     # all commits touching the file
git log -S "specific_string"            # commits adding/removing a string
git blame apps/orders/services.py       # who last changed each line
```

Helps when "this code looks weird" — see the context it was added in.

### Browser DevTools

- **Network tab:** request URL, method, headers, payload, response. The 404 / 500 status comes with the response body.
- **Console:** JS errors, HTMX events (`htmx:beforeRequest`, `htmx:afterSwap`)
- **Elements:** check the actual DOM after HTMX swap (vs the template you expected)

Enable HTMX logging in dev:

```js
htmx.logAll();
```

Logs every HTMX event to console.

## Common bug patterns

### "It works locally but not in staging/prod"

Likely:

- Env var difference (`DEBUG`, `ALLOWED_HOSTS`, feature flag)
- Data difference (your dev DB has 10 rows, prod has 10M)
- Migration order
- Cache state
- File system difference (case-sensitive in prod, not on Mac)

### "It used to work"

Likely:

- Recent merge changed something — `git bisect`
- Dependency update — check `requirements/*.txt` history
- DB migration changed schema

### "It works sometimes"

Likely:

- Race condition
- Time / timezone bug
- Random ordering (test that relies on insertion order, but DB returns rows differently)
- Cache stale

### "404 but the URL is right"

Likely:

- Trailing slash (`APPEND_SLASH` setting)
- URL captured with wrong type (`<int:pk>` vs `<uuid:public_id>`)
- App not in `INSTALLED_APPS`
- URL `include`d under wrong prefix

### "Form errors silent"

Likely:

- `form.is_valid()` not called
- Returning JSON to HTMX (HTMX expects HTML)
- 302 redirect on POST without `messages` framework
- Form bound with `request.POST` vs `request.GET`

### "Celery task not running"

Likely:

- Worker not consuming the right queue
- Task module not imported (Celery autodiscovery missed it)
- Result discarded because no broker URL
- Task name mismatched after rename

### "Migration won't apply"

Likely:

- Out of order (your migration depends on one not yet applied)
- Data conflict (new constraint violated by existing data)
- Migration locks a table for too long

## When you're truly stuck

- Take a break. Walk. Make tea. Brains solve problems offline.
- Explain the bug out loud (rubber duck debugging — really works)
- Write a minimal reproduction in a fresh file/notebook
- Search the error message exactly (with quotes); strip your codebase identifiers first
- Ask. Be specific: "I have X, I expected Y, I get Z, I've tried A and B."

## Anti-patterns

- ❌ Changing 3 things at once
- ❌ "Let me just add a `try/except`"
- ❌ Restarting / clearing cache as the first move (sometimes correct; should not be the default)
- ❌ Blaming the framework / library before checking your own code
- ❌ Assuming the bug is rare; if you saw it once, it'll happen again
