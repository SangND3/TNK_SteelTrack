"""
Example service module.

Services contain write operations and business logic. Reference for:
- Keyword-only args
- @transaction.atomic for multi-step writes
- transaction.on_commit for deferred side effects
- Domain-specific exceptions
- Calling selectors for reads
"""

from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction

from apps.orders.exceptions import InsufficientStockError, OrderNotFoundError
from apps.orders.models import Order, OrderItem
from apps.orders.tasks import notify_order_created
from apps.products.selectors import product_get
from apps.users.models import User

logger = logging.getLogger(__name__)


@transaction.atomic
def order_create(*, user: User, items: list[dict]) -> Order:
    """Create an order for ``user`` with the given items.

    Args:
        user: the customer placing the order.
        items: list of {"sku": str, "quantity": int} dicts.

    Returns:
        The newly created Order with related OrderItems already created.

    Raises:
        InsufficientStockError: if any item lacks sufficient stock.
        ValueError: if items is empty or malformed.
    """
    if not items:
        raise ValueError("items must not be empty")

    _validate_and_reserve_stock(items)

    total = _compute_total(items)
    order = Order.objects.create(user=user, total=total, status=Order.Status.PENDING)

    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            sku=item["sku"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
        )
        for item in items
    ])

    # Defer side effects until the transaction commits.
    # If the transaction is rolled back, no email is sent.
    transaction.on_commit(lambda: notify_order_created.delay(order.id))

    logger.info(
        "order_created",
        extra={"order_id": order.id, "user_id": user.id, "total": str(total)},
    )

    return order


@transaction.atomic
def order_complete(*, order_id: int, completed_by: User) -> Order:
    """Mark an order as completed."""
    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except Order.DoesNotExist as exc:
        raise OrderNotFoundError(f"Order {order_id} not found") from exc

    if order.status == Order.Status.COMPLETED:
        return order  # idempotent

    order.status = Order.Status.COMPLETED
    order.completed_at = _now()
    order.completed_by = completed_by
    order.save(update_fields=["status", "completed_at", "completed_by", "updated_at"])

    logger.info("order_completed", extra={"order_id": order.id})

    return order


# ─── private helpers ────────────────────────────────────────────────────────


def _validate_and_reserve_stock(items: list[dict]) -> None:
    """Decrement stock for each item; raise if any is insufficient."""
    for item in items:
        product = product_get(sku=item["sku"])
        if product.stock < item["quantity"]:
            raise InsufficientStockError(
                f"Product {product.sku} has {product.stock}, "
                f"requested {item['quantity']}"
            )
        product.stock -= item["quantity"]
        product.save(update_fields=["stock", "updated_at"])
        # Inject the unit_price so the caller doesn't need to re-fetch
        item["unit_price"] = product.price


def _compute_total(items: list[dict]) -> Decimal:
    return sum(
        (item["unit_price"] * item["quantity"] for item in items),
        start=Decimal("0"),
    )


def _now():
    # Wrapped so tests can monkeypatch without freezegun if they prefer
    from django.utils import timezone
    return timezone.now()
