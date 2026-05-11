# Skill: Refactoring

Refactoring = changing the structure of code **without changing its behavior**. If behavior changes, it's not a refactor; it's a rewrite or a feature.

## When to refactor

- **Before a feature**, to make the feature easier ("make the change easy, then make the easy change")
- **After a bug fix**, if the bug revealed structural weakness
- **When you understand it better** than the original author did
- **When a pattern is duplicated** 3+ times and the duplication causes pain

## When NOT to refactor

- During a feature (mix scope = bad PR)
- Because "it could be more elegant" (no, leave it; ship features)
- To preempt a future need that may never come
- To switch to your preferred style

## Process

### Phase 1 — Lock behavior

Before changing anything:

1. **Identify what the code does** — read it, run it, see outputs
2. **Find existing tests** covering this code
3. **Fill test gaps** — add tests for any behavior not covered, in a separate commit. This is a critical step.

If you refactor uncovered code and break it, no one will know.

### Phase 2 — Plan the change

Output a plan:

```
## Refactor plan

**Target:** apps/orders/services.py — extract pricing logic to apps/orders/pricing.py

**Why:** pricing logic is 300 lines mixed with order creation; harder to test and reuse for quotes feature.

**Approach:**
1. Create apps/orders/pricing.py with extracted functions
2. Update order_create() to call them
3. No behavior change; tests must pass at every step

**Behavior change:** none

**Tests:**
- All existing service tests pass unchanged
- (Pricing tests stay where they are for now; can move later if needed)
```

Wait for approval.

### Phase 3 — Small steps

Refactor in commits that each:

- Compile
- Pass tests
- Leave the code in a coherent state

Example sequence:

1. Add new module/file with extracted code (old code still calls duplicate)
2. Switch one call site to use new code
3. Verify tests pass; commit
4. Switch remaining call sites
5. Delete old code
6. Final commit

If you can't make a single step without breaking tests, split it smaller.

### Phase 4 — Diff review

Compare your branch against `main`:

- Search for any behavior change you didn't intend
- Check that test count didn't drop (you didn't accidentally delete tests)
- Verify imports are clean
- Verify no leftover dead code from the old structure

### Phase 5 — PR

```markdown
## What

Extract pricing logic from `order_create()` into a dedicated `pricing.py` module.

## Why

Pricing logic was 300 lines mixed into order creation. Hard to test in isolation, and we're about to add a quotes feature that will reuse it.

## How

Created `apps/orders/pricing.py` with `compute_total()`, `compute_tax()`, `apply_discount()`. `order_create()` now calls these. No behavior change.

## Test plan

- All existing tests pass (no test changes)
- Test count: 47 before, 47 after
- Manual verification: created an order locally, total matches expected
```

## Refactoring patterns

### Extract function

When a function does multiple things:

```python
# Before
def order_create(*, user, items):
    # validate
    for item in items:
        if not item.get("sku"):
            raise ValidationError("sku required")
    # compute total
    total = sum(item["qty"] * item["price"] for item in items)
    # apply discount
    if user.discount_pct:
        total *= (1 - user.discount_pct / 100)
    # ... create order
```

```python
# After
def _validate_items(items):
    for item in items:
        if not item.get("sku"):
            raise ValidationError("sku required")

def _compute_total(items, user):
    subtotal = sum(item["qty"] * item["price"] for item in items)
    return _apply_discount(subtotal, user)

def order_create(*, user, items):
    _validate_items(items)
    total = _compute_total(items, user)
    # ... create order
```

### Extract module

When a file grows past ~500 lines or contains multiple concerns:

- Identify the concerns
- Move related functions to a new module
- Update imports

### Inline

The reverse — when a function is too small to justify its existence:

```python
# Before
def _is_active(user):
    return user.status == "active" and not user.suspended

if _is_active(user):
    ...

# After
if user.status == "active" and not user.suspended:
    ...
```

(Only if used once. Reused = keep the function.)

### Rename

When a name no longer reflects what the thing does:

- Use IDE rename (catches imports, references)
- Run all tests
- Don't combine with other changes

### Replace conditional with polymorphism

When you have repeated `if type == "X": ... elif type == "Y": ...`:

- Consider classes (one per type) with a common interface
- But: don't add abstraction just because it's "more OO". Inline conditionals are often clearer.

### Introduce parameter object

When a function has 6+ parameters:

```python
# Before
def order_create(user, billing_address, shipping_address, items, coupon, notes, gift_message): ...

# After
@dataclass
class OrderInput:
    user: User
    billing_address: Address
    shipping_address: Address
    items: list[OrderItem]
    coupon: str | None = None
    notes: str = ""
    gift_message: str = ""

def order_create(order_input: OrderInput): ...
```

## Anti-patterns

- ❌ Refactor that includes "while I was here, let me fix this bug" — separate PR
- ❌ Refactor that includes formatting changes across the file — separate PR
- ❌ Refactor that changes behavior "but only in edge cases" — that IS a behavior change
- ❌ Mass rename across the codebase as a single commit — split per area
- ❌ Refactor with no tests for the refactored code — add tests first
- ❌ Refactor "because Clean Code says so" — refactor for a concrete benefit
