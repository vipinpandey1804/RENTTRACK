"""Billing API URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.billing.views import BillViewSet

router = DefaultRouter()
router.register("bills", BillViewSet, basename="bill")

urlpatterns = [
    path("", include(router.urls)),
]
