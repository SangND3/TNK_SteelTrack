"""
Example DRF serializer.

Use only when there's a non-browser consumer (mobile, third-party).
For HTMX, use Django Forms instead — see forms.py and view_example.py.

Reference for:
- Field validation
- Cross-field validation in validate()
- Nested writes via create()
- Read-only public_id exposed instead of internal id
"""

from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.orders.services import order_create


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["sku", "quantity", "unit_price"]
        read_only_fields = ["unit_price"]  # service derives from product

    def validate_quantity(self, value: int) -> int:
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        if value > 1000:
            raise serializers.ValidationError("Quantity may not exceed 1000.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    items = OrderItemSerializer(many=True)
    status = serializers.CharField(read_only=True)
    total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "public_id",
            "status",
            "total",
            "items",
            "created_at",
            "completed_at",
        ]
        read_only_fields = [
            "public_id", "status", "total", "created_at", "completed_at",
        ]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item required.")

        # Detect duplicate SKUs — clients should merge instead
        skus = [item["sku"] for item in value]
        if len(skus) != len(set(skus)):
            raise serializers.ValidationError("Duplicate SKUs are not allowed.")

        return value

    def create(self, validated_data: dict) -> Order:
        # Delegate to the service — no business logic in the serializer
        items = validated_data["items"]
        user = self.context["request"].user
        return order_create(user=user, items=items)
