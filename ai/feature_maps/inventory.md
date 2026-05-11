# Feature map: Inventory

> **Status:** template. Fill in actual file paths and decisions as you build the inventory feature.

## Scope

This feature covers:

- Product catalog
- Stock levels per product
- Stock movements (in/out, audit trail)
- Low-stock alerts
- Per-warehouse stock (if multi-warehouse)

Not in scope:

- Pricing (separate from stock; on `Product.price` for simplicity)
- Order fulfillment → see `orders.md` (feature map TBD)
- Supplier management → out of MVP scope

## Where it lives

| Concern              | Location                                                         |
| -------------------- | ---------------------------------------------------------------- |
| Product model        | `apps/products/models.py` — `Product`, `ProductCategory`         |
| Stock model          | `apps/inventory/models.py` — `StockLevel`, `StockMovement`       |
| Services             | `apps/inventory/services.py`                                     |
| Selectors            | `apps/inventory/selectors.py`                                    |
| Admin                | `apps/inventory/admin.py` — for ops to adjust manually           |
| Low-stock task       | `apps/inventory/tasks.py` — periodic, alerts when below threshold |
| URLs                 | `apps/inventory/urls.py`                                         |
| Templates            | `templates/inventory/`                                           |

## Key models

```
Product
├── id (auto-int, internal)
├── public_id (UUID, exposed)
├── sku (str, unique, indexed)
├── name
├── description
├── price_cents (int)
├── category (FK)
├── is_active (bool)
├── low_stock_threshold (int, default 10)
└── timestamps

StockLevel
├── product (FK, unique=True if single-warehouse; composite unique with warehouse otherwise)
├── quantity (int, ≥ 0)
└── updated_at

StockMovement (append-only audit log)
├── product (FK)
├── delta (int, signed: +10 receipt, -3 sale)
├── reason (enum: receipt, sale, adjustment, return, damage, transfer)
├── reference (str, e.g., order_id, receipt_id)
├── performed_by (FK, nullable)
└── created_at (db_index)
```

## Key business rules

- Stock can never go negative. Service raises `InsufficientStockError` if attempted.
- Every stock change writes a `StockMovement` (no direct UPDATE to `StockLevel.quantity` outside services)
- Adjustments (corrections) need a `reason` and `performed_by`
- Reservations during checkout: short-lived locks via `select_for_update()` (avoid double-sell)
- Low-stock alert fires when quantity drops below `low_stock_threshold` (idempotent — once per drop, not on every save below)

## Key flows

### Receive stock (incoming)

1. Admin or system calls `stock_receive(product_id, quantity, reference)`
2. Service wraps in `transaction.atomic`
3. Creates `StockMovement(delta=+qty)`
4. Increments `StockLevel.quantity`

### Sell stock (outgoing)

1. Order service calls `stock_decrement(product_id, quantity, reference=order_id)`
2. Service `select_for_update()` on `StockLevel`
3. Checks `quantity >= delta`; raises `InsufficientStockError` if not
4. Creates `StockMovement(delta=-qty)`
5. Decrements `StockLevel.quantity`

### Reconciliation

Daily job: sum of all `StockMovement.delta` per product == `StockLevel.quantity`. Discrepancies logged + alert.

## Concurrency

Stock is a hot row. Two simultaneous sells can race. Mitigations:

- `select_for_update()` on `StockLevel` during decrement
- Application-level retry on `OperationalError` (deadlock) with backoff
- Idempotency on `StockMovement.reference` (don't double-decrement for the same order)

## Tests

- `apps/inventory/tests/test_services.py` — receive, decrement, insufficient stock
- `apps/inventory/tests/test_concurrency.py` — simulate concurrent decrements
- `apps/inventory/tests/test_reconciliation.py` — sum-of-movements invariant

## Open items / known issues

- [ ] Single-warehouse assumption; multi-warehouse needs schema change
- [ ] Stock movements grow unbounded; consider archival after 2 years
- [ ] No "reserved" state for in-flight orders; race possible if checkout is slow

## Related ADRs

- `ai/decisions/00X-stock-strategy.md` — if/when you make a non-obvious call

## When to update this file

- Multi-warehouse added
- Reservation state introduced
- Significant model change
