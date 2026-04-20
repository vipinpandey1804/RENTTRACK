"""Properties API URLs."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.properties.views import LeaseViewSet, PropertyViewSet, UnitViewSet

router = DefaultRouter()
router.register("", PropertyViewSet, basename="property")
router.register("units", UnitViewSet, basename="unit")
router.register("leases", LeaseViewSet, basename="lease")

urlpatterns = [
    path("", include(router.urls)),
]
