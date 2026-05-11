"""
Example DRF endpoint.

Use only when a non-browser consumer needs JSON. For browser HTMX, use
function-based views returning HTML — see view_example.py.

Reference for:
- ModelViewSet with queryset scoped by request.user
- Permission classes (IsAuthenticated + custom IsOwner)
- Pagination
- Filtering via django-filter
- Idempotency for create
- Consistent error shape
- Action endpoint via @action
"""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.orders.exceptions import InsufficientStockError, OrderNotFoundError
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from apps.orders.services import order_complete


# ─── permissions ────────────────────────────────────────────────────────────


class IsOwner(BasePermission):
    """Allow access only if request.user owns the object."""

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


# ─── pagination ─────────────────────────────────────────────────────────────


class OrderPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "limit"
    max_page_size = 100
    ordering = "-created_at"


# ─── custom exceptions (translate domain errors to HTTP errors) ─────────────


class InsufficientStock(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Insufficient stock for one or more items."
    default_code = "insufficient_stock"


class OrderNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Order not found."
    default_code = "not_found"


# ─── viewset ────────────────────────────────────────────────────────────────


class OrderViewSet(viewsets.ModelViewSet):
    """CRUD for Orders, scoped to the authenticated user.

    URLs (via DefaultRouter):
        GET    /api/v1/orders/                list
        POST   /api/v1/orders/                create
        GET    /api/v1/orders/<public_id>/    retrieve
        PATCH  /api/v1/orders/<public_id>/    partial update
        DELETE /api/v1/orders/<public_id>/    delete
        POST   /api/v1/orders/<public_id>/complete/   action
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    pagination_class = OrderPagination
    lookup_field = "public_id"

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "total"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # CRITICAL: scope by user to prevent IDOR.
        # Without this, any authenticated user could fetch any order by public_id.
        return (
            Order.objects
                .filter(user=self.request.user)
                .select_related("user")
                .prefetch_related("items")
        )

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create an order. Idempotency-Key header is respected for safe retries."""
        idempotency_key = request.headers.get("Idempotency-Key")
        if idempotency_key:
            existing = self._lookup_idempotent(request.user, idempotency_key)
            if existing:
                return Response(
                    OrderSerializer(existing).data,
                    status=status.HTTP_200_OK,
                )

        try:
            return super().create(request, *args, **kwargs)
        except InsufficientStockError as exc:
            raise InsufficientStock(detail=str(exc)) from exc

    @action(detail=True, methods=["post"])
    def complete(self, request: Request, public_id=None) -> Response:
        """Mark this order as completed."""
        order = self.get_object()
        try:
            order = order_complete(order_id=order.id, completed_by=request.user)
        except OrderNotFoundError as exc:
            raise OrderNotFound() from exc

        return Response(OrderSerializer(order).data)

    # ─── helpers ─────────────────────────────────────────────────────────────

    def _lookup_idempotent(self, user, key: str) -> Order | None:
        """Return an order previously created with this idempotency key."""
        # Implementation depends on your storage choice (Redis, DB column, etc.)
        # Sketch only — see SECURITY_RULES and API_CONVENTION for guidance.
        return None
