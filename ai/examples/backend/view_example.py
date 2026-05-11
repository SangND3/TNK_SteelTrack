"""
Example view module.

Views orchestrate: parse input → call selector/service → render. Nothing else.
Reference for:
- Function-based views (CBV only for DRF / admin)
- HTMX detection via request.htmx (django-htmx)
- Returning partial vs full page
- Using HX-Trigger for client-side events
- Permission boundary
"""

from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.orders.exceptions import InsufficientStockError
from apps.orders.forms import OrderForm
from apps.orders.selectors import order_get, order_list, order_stats_for_user
from apps.orders.services import order_complete, order_create


@login_required
@require_http_methods(["GET"])
def order_list_view(request: HttpRequest) -> HttpResponse:
    """List orders; supports HTMX for filter/search re-renders."""
    status = request.GET.get("status") or None
    search = request.GET.get("q") or None

    orders = order_list(user=request.user, status=status, search=search)

    # Paginate (kept simple for the example)
    from django.core.paginator import Paginator
    page = Paginator(orders, per_page=20).get_page(request.GET.get("page"))

    context = {"page": page, "status": status, "search": search}

    if request.htmx:
        return render(request, "orders/partials/order_list.html", context)
    return render(request, "orders/list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def order_create_view(request: HttpRequest) -> HttpResponse:
    """Create an order; supports HTMX form submit."""
    form = OrderForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            order = order_create(user=request.user, items=form.cleaned_data["items"])
        except InsufficientStockError as exc:
            form.add_error(None, str(exc))
            return render(
                request, "orders/partials/order_form.html", {"form": form}
            )

        if request.htmx:
            response = render(
                request, "orders/partials/order_row.html", {"order": order}
            )
            response["HX-Trigger"] = json.dumps({
                "orderCreated": {"id": order.id},
                "showToast": {"level": "success", "message": "Order created"},
            })
            return response

        return redirect("orders:detail", public_id=order.public_id)

    template = (
        "orders/partials/order_form.html"
        if request.htmx
        else "orders/create.html"
    )
    return render(request, template, {"form": form})


@login_required
@require_http_methods(["GET"])
def order_detail_view(request: HttpRequest, public_id: str) -> HttpResponse:
    """Order detail; selector raises 404 if not owned by user."""
    order = order_get(public_id=public_id, user=request.user)

    template = (
        "orders/partials/order_card.html"
        if request.htmx
        else "orders/detail.html"
    )
    return render(request, template, {"order": order})


@login_required
@require_http_methods(["POST"])
def order_complete_view(request: HttpRequest, public_id: str) -> HttpResponse:
    """Action endpoint: mark an order complete."""
    order = order_get(public_id=public_id, user=request.user)
    order = order_complete(order_id=order.id, completed_by=request.user)

    if request.htmx:
        return render(request, "orders/partials/order_row.html", {"order": order})
    return redirect("orders:detail", public_id=order.public_id)


@login_required
@require_http_methods(["GET"])
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Dashboard with aggregate stats."""
    stats = order_stats_for_user(user=request.user)
    return render(request, "orders/dashboard.html", {"stats": stats})
