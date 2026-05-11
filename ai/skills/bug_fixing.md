# Skill: Bug fixing

Bugs are not solved by "trying things until it works". They are solved by understanding.

## Phase 1 — Reproduce

A bug you cannot reproduce is a bug you cannot fix. Before any code change:

1. Get exact reproduction steps from the reporter
2. Reproduce locally
3. If you cannot reproduce, **stop**. Ask for more info: env, browser, exact inputs, screenshots, logs.

If reproducing requires production data, work from a sanitized snapshot in staging.

## Phase 2 — Diagnose

**Root cause, not symptom.** A traceback shows where things blew up — not always why.

Tools:

- `pdb` / `ipdb` — drop a breakpoint, inspect state
- `print()` is fine *while debugging*, just don't commit it
- Django Debug Toolbar — query count, settings, request info
- `git blame` / `git log -p <file>` — when did this change?
- `git bisect` — when "it used to work"

Steps:

1. Read the stack trace top to bottom and bottom to top
2. Form a hypothesis ("X causes Y because Z")
3. Test the hypothesis with the smallest possible probe
4. Iterate until you have the actual cause, not a coincidence

Common antipatterns to avoid:

- **Cargo culting** — "I'll add a `try/except` because that fixed it last time"
- **Symptom suppression** — `if x is None: return` without understanding why x is None
- **Shotgun debugging** — changing 5 things at once; you won't know which fixed it

## Phase 3 — Communicate

Before writing the fix, share the diagnosis:

```
**Root cause:** When user has no avatar, `user.avatar.url` raises AttributeError
because `avatar` is a nullable FileField. The view template accesses `.url`
unconditionally.

**Impact:** Crashes on profile view for all users without an avatar (~12% of users
per our DB).

**Proposed fix:** Update the template to check for avatar presence; provide a
default avatar URL in the view context as a fallback.

**Test plan:**
1. Regression test: profile view renders for a user with avatar=None
2. Regression test: shown default avatar URL when avatar is None
```

Wait for ack before writing the fix. The user might say "actually, we want a different default" or "let's just block users from having no avatar".

## Phase 4 — Write a failing test first

```python
def test_profile_view__when_user_has_no_avatar__renders_default():
    user = UserFactory(avatar=None)
    client.force_login(user)

    response = client.get(f"/users/{user.public_id}/")

    assert response.status_code == 200
    assert b'src="/static/images/default-avatar.png"' in response.content
```

Run it. It should fail with the bug.

This test is the **regression test**. It stays in the suite forever. If the bug ever comes back, this fails.

## Phase 5 — Smallest fix

Change the minimum needed to make the failing test pass.

```python
# templates/users/profile.html
<img src="{{ user.avatar.url|default:'/static/images/default-avatar.png' }}" alt="...">
```

Resist refactoring while you're here. If you see other issues, file them; don't fix them in this PR. Scope creep turns a 1-file PR into 30-file PR and dilutes review.

## Phase 6 — Verify

- The regression test passes
- The full test suite passes
- The original reproduction steps no longer reproduce the bug
- The fix doesn't break any related feature (manual smoke test the area)

## Phase 7 — PR

Use `ai/templates/pr_description.md`. Specifically for bugs:

```markdown
## What

Fix profile view crash for users without an avatar.

## Why

`user.avatar.url` raises AttributeError when avatar is None.
Reported by user @X in #287. Affects ~12% of users.

## How

Template now uses Django's `default` filter to fall back to a default
avatar URL when `avatar` is None.

## Test plan

Regression test added: `test_profile_view__when_user_has_no_avatar__renders_default`.

Manually verified: profile page loads for user without avatar.

Closes #287
```

## Phase 8 — Postmortem (for serious bugs)

If the bug caused an outage, data loss, or user-visible incident, write a postmortem. See `ai/skills/incident_analysis.md`.

For routine bugs, the PR description is enough.

## Anti-patterns

- ❌ Pushing a fix without a reproduction
- ❌ Pushing a fix without a regression test
- ❌ Squashing the symptom (`try/except: pass`)
- ❌ "While I was here, I also refactored..." (file it for later)
- ❌ Closing a bug as "could not reproduce" without 2-3 attempts and asking the reporter for more info
