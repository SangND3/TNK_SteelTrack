"""
Example Celery task.

Reference for:
- @shared_task with bind=True, max_retries, default_retry_delay
- Accepting IDs, not instances
- Idempotent design (safe to run twice)
- Specific exception handling with retry
- Logging with structured context
"""

from __future__ import annotations

import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.mail import EmailMessage
from smtplib import SMTPException

from apps.orders.models import Order

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(SMTPException,),
    retry_backoff=True,        # exponential backoff: 60s, 120s, 240s
    retry_backoff_max=600,
    retry_jitter=True,         # avoid thundering herd
)
def notify_order_created(self, order_id: int) -> None:
    """Send order-confirmation email to the customer.

    Idempotent: if the order has already been notified, returns silently.

    Args:
        order_id: the Order.id (not the model instance).
    """
    try:
        order = Order.objects.select_related("user").get(pk=order_id)
    except Order.DoesNotExist:
        # The order was deleted between scheduling and execution.
        # This is fine; log and exit (don't retry — it will never appear).
        logger.warning("notify_order_created: order %s not found", order_id)
        return

    if order.notification_sent_at is not None:
        logger.info("notify_order_created: already sent for order %s", order_id)
        return

    try:
        _send_email(order)
    except SMTPException as exc:
        logger.warning(
            "notify_order_created: SMTP error for order %s: %s; retrying",
            order_id, exc,
        )
        raise  # autoretry_for will catch this

    # Mark as sent only after successful delivery
    Order.objects.filter(pk=order.pk).update(
        notification_sent_at=_now(),
    )
    logger.info("notify_order_created: sent for order %s", order_id)


@shared_task(bind=True, max_retries=0)
def expire_old_orders(self) -> int:
    """Periodic task (via celery beat): mark stale pending orders as expired.

    Returns:
        Number of orders expired.
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=7)
    expired_count = Order.objects.filter(
        status=Order.Status.PENDING,
        created_at__lt=cutoff,
    ).update(status=Order.Status.EXPIRED)

    logger.info("expire_old_orders: expired %s orders", expired_count)
    return expired_count


# ─── private helpers ────────────────────────────────────────────────────────


def _send_email(order: Order) -> None:
    EmailMessage(
        subject=f"Order #{order.public_id} confirmed",
        body=f"Hi {order.user.first_name}, your order is being processed.",
        to=[order.user.email],
    ).send(fail_silently=False)


def _now():
    from django.utils import timezone
    return timezone.now()
