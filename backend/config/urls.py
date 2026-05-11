from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls", namespace="dashboard")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("inventory/", include("apps.inventory.urls", namespace="inventory")),
    path("orders/", include("apps.orders.urls", namespace="orders")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
]

# Custom error handlers
handler403 = core_views.error_403
handler404 = core_views.error_404
handler500 = core_views.error_500

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
