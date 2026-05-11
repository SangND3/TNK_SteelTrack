# GIT_RULES.md

How we use git on this project. Optimized for solo work with discipline, scales to team.

## Branching

GitHub Flow (not Git Flow — too heavy for this size):

- `main` — always deployable
- `feature/<short-name>` — new features
- `fix/<short-name>` — bug fixes
- `chore/<short-name>` — tooling, deps, non-code
- `refactor/<short-name>` — structure changes, no behavior change
- `docs/<short-name>` — docs only

One branch = one logical change. Don't mix feature and refactor.

Branch name: lowercase, hyphens, descriptive.

```
feature/user-email-verification    ✓
fix/null-avatar-crash              ✓
feat/stuff                         ✗
fix-bug                            ✗
my-branch                          ✗
```

## Commits

### Conventional Commits

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types:

- `feat` — new feature
- `fix` — bug fix
- `refactor` — code change that neither fixes a bug nor adds a feature
- `perf` — performance improvement
- `test` — add/modify tests
- `docs` — documentation only
- `chore` — tooling, deps, non-code changes
- `build` — build system, deps
- `ci` — CI config changes
- `style` — formatting (rare; usually auto)

Scope is optional but encouraged:

```
feat(orders): add inline edit
fix(auth): handle expired tokens
refactor(billing): extract invoice service
```

### Subject line

- ≤ 72 characters
- Imperative mood ("add", not "added" or "adds")
- No trailing period
- Lowercase after the type (except proper nouns)

### Body (when needed)

- Wrap at 72 characters
- Explain **what and why**, not how (the diff shows how)
- Reference issues: `Closes #123` or `Refs #456`

### Examples

Good:

```
feat(orders): allow inline edit of order title

Replaces the static title cell with an HTMX edit form when the
user clicks the title. Submitting saves and returns the updated row.

Closes #142
```

```
fix(users): handle null avatar in profile view

Previously crashed with AttributeError when user had no avatar.
Now falls back to a default avatar URL.

Closes #287
```

Bad:

```
update stuff
WIP
fixes
Final fix for the bug fix that we had to fix
```

### Frequency

- Commit early, commit often
- Each commit should leave the repo in a working state (tests pass)
- Smaller commits are easier to review and revert

## Pull requests

Every change goes through a PR. Even solo. The PR is where:

- CI runs
- You self-review (force structured thought)
- History becomes a unit (squashable, revertable)

### PR title

Same format as a commit subject.

### PR description

Use `ai/templates/pr_description.md`:

```markdown
## What

<one-paragraph summary>

## Why

<the problem this solves>

## How

<approach taken — only if non-obvious>

## Test plan

- [ ] <how to verify, manual or automated>

## Screenshots

<for UI changes>

## Notes for reviewer

<anything specific to call attention to>

Closes #<issue>
```

### Size

- < 200 lines diff: ideal
- 200-500 lines: acceptable
- 500+ lines: justify in the PR description; consider splitting

If you find yourself with a 1000-line PR, you've gone too deep without checkpointing.

### CI

Must pass before merge:

- Lint (ruff)
- Format (ruff)
- Type-check (mypy)
- Tests (pytest)
- Migration check
- Build check

Failing CI = blocked. No "merge anyway" or "fix in next PR".

### Self-review

Before requesting review (or merging solo), walk the relevant checklist in `ai/checklists/`.

## Merging

- **Squash merge** for feature branches → clean linear history on `main`
- **Merge commit** only for long-running release branches (we don't have these yet)
- **Rebase** to update a branch with latest `main` — never merge `main` into your feature
- Delete the branch after merge

## Tagging and releases

- Semantic versioning: `v0.1.0`, `v0.2.0`, `v1.0.0`
- Tag from `main` after a release-worthy commit
- Auto-generate changelog from conventional commits (`git-cliff` or `conventional-changelog`)

## Force pushing

- **Never** to `main`. Period.
- **Allowed** on your own feature branches (rebasing, fixing commits)
- After force-push to a PR branch, leave a comment so reviewers know to refresh

## Resolving conflicts

- Rebase your branch on `main`: `git rebase origin/main`
- Resolve conflicts, test, continue
- Force-push: `git push --force-with-lease` (safer than `--force`)

Never use `--force` (without `--with-lease`) — you'll occasionally overwrite collaborator work.

## Things never to commit

- Secrets (`.env`, keys, certificates, tokens)
- Compiled artifacts (`*.pyc`, `node_modules/`, `dist/`, `build/`)
- Local config (`.vscode/`, `.idea/` — except shared `.editorconfig`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Large binary files (use Git LFS if truly needed; better: object storage)
- Generated files that should be built (`output.css`, compiled assets)

`.gitignore` covers most. `pre-commit` adds another layer (`detect-secrets`).

## Hooks

`pre-commit` runs on every commit:

- Ruff lint + format
- Detect secrets
- Check for large files
- Check merge conflict markers
- End-of-file fixer
- Trailing whitespace

Install with `pre-commit install`. Don't bypass with `--no-verify` unless you have a specific reason and document it.

## When things go wrong

- **Committed to wrong branch:** `git reset --soft HEAD~1`, switch branch, commit again
- **Bad commit message:** `git commit --amend` (if not pushed)
- **Need to undo a pushed commit:** `git revert <sha>` (don't rewrite shared history)
- **Lost work:** check `git reflog` — usually recoverable
- **Branch in a mess:** sometimes the fastest fix is to copy files aside, `git reset --hard origin/<branch>`, and reapply
