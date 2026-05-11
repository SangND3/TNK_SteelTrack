"""
Example test module.

Reference for:
- pytest-django + factory_boy
- Arrange/Act/Assert with blank-line separation
- Naming: test_<unit>__<scenario>__<expected>
- Mocking at boundaries (Celery, external services), never the ORM
- Testing services, views, and tasks at the right layer
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.orders.exceptions import InsufficientStockError, OrderNotFoundError
from apps.orders.models import Order
from apps.orders.services import order_complete, order_create

pytestmark = pytest.mark.django_db


# ─── service tests ──────────────────────────────────────────────────────────


class TestOrderCreate:
    """Tests for apps.orders.services.order_create."""

    def test__when_items_valid__creates_order_with_total(
        self, user_factory, product_factory
    ):
        user = user_factory()
        product = product_factory(price=Decimal("10.00"), stock=5)
        items = [{"sku": product.sku, "quantity": 2}]

        order = order_create(user=user, items=items)

        assert order.user == user
        assert order.total == Decimal("20.00")
        assert order.status == Order.Status.PENDING
        assert order.items.count() == 1

    def test__when_items_empty__raises_value_error(self, user_factory):
        user = user_factory()
        with pytest.raises(ValueError, match="must not be empty"):
            order_create(user=user, items=[])

    def test__when_stock_insufficient__raises_insufficient_stock_error(
        self, user_factory, product_factory
    ):
        user = user_factory()
        product = product_factory(stock=1)
        items = [{"sku": product.sku, "quantity": 5}]

        with pytest.raises(InsufficientStockError):
            order_create(user=user, items=items)

    def test__when_stock_insufficient__does_not_create_order(
        self, user_factory, product_factory
    ):
        user = user_factory()
        product = product_factory(stock=1)
        items = [{"sku": product.sku, "quantity": 5}]

        with pytest.raises(InsufficientStockError):
            order_create(user=user, items=items)

        assert Order.objects.count() == 0  # transaction rolled back

    def test__triggers_notification_task(
        self, mocker, user_factory, product_factory
    ):
        mock_task = mocker.patch(
            "apps.orders.services.notify_order_created.delay"
        )
        user = user_factory()
        product = product_factory(stock=10)

        order = order_create(
            user=user, items=[{"sku": product.sku, "quantity": 1}]
        )

        mock_task.assert_called_once_with(order.id)


class TestOrderComplete:
    def test__when_order_pending__transitions_to_completed(
        self, user_factory, order_factory
    ):
        user = user_factory()
        order = order_factory(status=Order.Status.PENDING)

        result = order_complete(order_id=order.id, completed_by=user)

        assert result.status == Order.Status.COMPLETED
        assert result.completed_at is not None
        assert result.completed_by == user

    def test__when_order_already_completed__is_idempotent(
        self, user_factory, order_factory
    ):
        user = user_factory()
        order = order_factory(status=Order.Status.COMPLETED)
        original_completed_at = order.completed_at

        result = order_complete(order_id=order.id, completed_by=user)

        assert result.completed_at == original_completed_at  # unchanged

    def test__when_order_does_not_exist__raises(self, user_factory):
        user = user_factory()
        with pytest.raises(OrderNotFoundError):
            order_complete(order_id=99999, completed_by=user)


# ─── view tests ─────────────────────────────────────────────────────────────


class TestOrderDetailView:
    def test__when_anonymous__redirects_to_login(self, client, order_factory):
        order = order_factory()

        response = client.get(f"/orders/{order.public_id}/")

        assert response.status_code == 302
        assert "/login" in response.url

    def test__when_not_owner__returns_404(
        self, client, user_factory, order_factory
    ):
        other_user = user_factory()
        order = order_factory(user=user_factory())
        client.force_login(other_user)

        response = client.get(f"/orders/{order.public_id}/")

        assert response.status_code == 404

    def test__when_owner_full_request__renders_full_page(
        self, client, user_factory, order_factory
    ):
        user = user_factory()
        order = order_factory(user=user)
        client.force_login(user)

        response = client.get(f"/orders/{order.public_id}/")

        assert response.status_code == 200
        assert b"<html" in response.content
        assert str(order.public_id).encode() in response.content

    def test__when_owner_htmx_request__renders_partial(
        self, client, user_factory, order_factory
    ):
        user = user_factory()
        order = order_factory(user=user)
        client.force_login(user)

        response = client.get(
            f"/orders/{order.public_id}/",
            HTTP_HX_REQUEST="true",
        )

        assert response.status_code == 200
        assert b"<html" not in response.content
        assert str(order.public_id).encode() in response.content


# ─── task tests ─────────────────────────────────────────────────────────────


class TestNotifyOrderCreated:
    def test__when_order_exists__sends_email(self, mocker, order_factory):
        from apps.orders.tasks import notify_order_created

        order = order_factory()
        mock_send = mocker.patch("apps.orders.tasks._send_email")

        notify_order_created(order.id)

        mock_send.assert_called_once()
        order.refresh_from_db()
        assert order.notification_sent_at is not None

    def test__when_order_missing__returns_silently(self, mocker):
        from apps.orders.tasks import notify_order_created

        mock_send = mocker.patch("apps.orders.tasks._send_email")

        notify_order_created(order_id=99999)  # does not exist

        mock_send.assert_not_called()

    def test__is_idempotent(self, mocker, order_factory):
        from apps.orders.tasks import notify_order_created
        from django.utils import timezone

        order = order_factory(notification_sent_at=timezone.now())
        mock_send = mocker.patch("apps.orders.tasks._send_email")

        notify_order_created(order.id)

        mock_send.assert_not_called()  # second run is a no-op
