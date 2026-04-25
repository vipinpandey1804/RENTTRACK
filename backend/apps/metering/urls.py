"""Metering API URLs."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.metering.views import MeterReadingViewSet

router = DefaultRouter()
router.register("readings", MeterReadingViewSet, basename="meter-reading")

urlpatterns = [
    path("", include(router.urls)),
]
