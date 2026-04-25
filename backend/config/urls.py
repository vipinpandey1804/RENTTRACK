"""
URL Configuration for RentTrack.

API versioning: /api/v1/...
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

api_v1_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("properties/", include("apps.properties.urls")),
    path("billing/", include("apps.billing.urls")),
    path("metering/", include("apps.metering.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("payments/", include("apps.payments.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1_patterns)),
    # Health check
    path("health/", include("apps.core.urls")),
    # API schema + docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
