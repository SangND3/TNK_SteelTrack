"""
Example selector module.

Selectors contain read queries. Reference for:
- Keyword-only args
- select_related / prefetch_related to prevent N+1
- Returning querysets so callers can paginate / chain
- Single-object getters that raise 404
"""

from __future__ import annotations

from datetime import datetime

from django.db.models import Count, Q, QuerySet
from django.shortcuts import get_object_or_404

from apps.orders.models import Order
from apps.users.models import User


def order_list(
    *,
    user: User,
    status: str | None = None,
    since: datetime | None = None,
    search: str | None = None,
) -> QuerySet[Order]:
    """Return orders for ``user`` matching the filters.

    Filters are optional and combine with AND.
    Returns a queryset; the caller is responsible for pagination.
    """
    qs = (
        Order.objects
        .filter(user=user)
        .select_related("user", "completed_by")
        .prefetch_related("items")
    )

    if status:
        qs = qs.filter(status=status)

    if since:
        qs = qs.filter(created_at__gte=since)

    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(items__sku__icontains=search)
        ).distinct()

    return qs.order_by("-created_at")


def order_get(*, public_id: str, user: User) -> Order:
    """Return a single order by public_id, scoped to the user.

    Raises Http404 if not found OR if it belongs to another user
    (avoids leaking existence of other users' orders).
    """
    return get_object_or_404(
        Order.objects
            .filter(user=user)
            .select_related("user", "completed_by")
            .prefetch_related("items"),
        public_id=public_id,
    )


def order_stats_for_user(*, user: User) -> dict:
    """Aggregate stats for the user's dashboard."""
    agg = Order.objects.filter(user=user).aggregate(
        total_count=Count("id"),
        completed_count=Count("id", filter=Q(status=Order.Status.COMPLETED)),
        pending_count=Count("id", filter=Q(status=Order.Status.PENDING)),
    )
    return {
        "total": agg["total_count"],
        "completed": agg["completed_count"],
        "pending": agg["pending_count"],
    }
