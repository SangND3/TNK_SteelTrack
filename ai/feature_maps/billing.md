# Feature map: Billing

> **Status:** template. Fill in actual file paths and decisions as you build the billing feature.

## Scope

This feature covers:

- Plans / subscriptions
- Invoices
- Payment method storage (via payment provider; never PCI data in our DB)
- Webhooks from payment provider
- Refunds and credits

Not in scope:

- Pricing logic for one-off orders → see `orders.md` (feature map TBD)
- Tax calculation → handled by payment provider

## Critical: deferred to human

Billing changes are **always reviewed by a human** before merge. Mark this in `AI_CONTEXT.md` § "What to defer to the human".

## Where it lives

| Concern             | Location                                                                |
| ------------------- | ----------------------------------------------------------------------- |
| Subscription model  | `apps/billing/models.py` — `Subscription`, `Plan`                       |
| Invoice model       | `apps/billing/models.py` — `Invoice`, `InvoiceLineItem`                 |
| Services            | `apps/billing/services.py`                                              |
| Payment provider    | `apps/billing/providers/<provider>.py` (e.g., `stripe.py`)              |
| Webhook handler     | `apps/billing/webhooks.py` — verifies signature, dispatches             |
| Webhook URL         | `/billing/webhooks/<provider>/` — exempt from CSRF, signature-verified  |
| Templates           | `templates/billing/` — subscription page, invoice list, etc.            |

## Key models

```
Plan
├── code (str, unique)
├── name
├── price_cents (int)
├── interval ("month" | "year")
└── is_active

Subscription
├── user (FK, OneToOne or FK depending on multi-sub support)
├── plan (FK)
├── provider_subscription_id (str, from payment provider)
├── status (active | past_due | canceled | trialing)
├── current_period_start
├── current_period_end
├── cancel_at_period_end (bool)
├── created_at
└── updated_at

Invoice
├── user (FK)
├── subscription (FK, nullable for one-off)
├── provider_invoice_id (str, from provider)
├── total_cents (int)
├── status (open | paid | void | uncollectible)
├── issued_at
└── paid_at (nullable)
```

## Key business rules

- We never store credit card numbers or CVV. Period. Use the payment provider's vault.
- Plan changes take effect at end of current period (prorate optional)
- Failed payment → `past_due` status, retry per provider policy, downgrade after N days
- Refunds: only via service `refund_invoice()`, never direct DB edits
- All money in cents (integer), never floats
- Currency: USD only for now; multi-currency in future revision

## Webhooks

The payment provider drives state. Our DB is a cache of provider state.

```
provider webhook → /billing/webhooks/<provider>/
                    ↓
              verify signature
                    ↓
              dispatch by event type
                    ↓
              update our DB to match provider
                    ↓
              return 200 (always, unless signature invalid)
```

Rules:

- **Always verify signatures** — never trust payload without it
- **Idempotent** — same webhook may arrive multiple times (deduplicate by event ID)
- **Fast response** — defer heavy work to Celery; return 200 in <1s
- **Reconcile periodically** — webhook may be missed; nightly job compares state

## Tests

- `apps/billing/tests/test_services.py` — subscription lifecycle, refunds
- `apps/billing/tests/test_webhooks.py` — signature verification, event dispatch
- `apps/billing/tests/test_models.py` — invariants on Plan/Subscription/Invoice

Test the provider via a mock client (not real API calls). Use `vcrpy` or canned fixtures.

## Security notes

- Webhook endpoint: signature-required, no CSRF
- PCI: out of scope (we never touch card data)
- PII: minimum needed — billing address yes; SSN no
- Audit log: every state change written to `BillingAuditLog` (separate table, append-only)

## Open items / known issues

- [ ] Single payment provider; adding a second requires a plugin interface
- [ ] Tax calculation relies on provider; consider self-managed for some jurisdictions
- [ ] Dunning emails (failed-payment reminders) not yet customized

## Related ADRs

- `ai/decisions/00X-payment-provider.md` — chose <provider> over <alternatives>

## When to update this file

- New plan type or pricing model
- New provider integration
- Schema change to billing models
- Significant change to webhook handling
