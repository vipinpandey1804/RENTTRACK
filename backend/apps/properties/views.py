"""Property, Unit, and Lease CRUD viewsets with tenant scoping."""

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsOrgMember, IsOrgOwnerOrManager
from apps.properties.models import Lease, Property, Unit
from apps.properties.serializers import LeaseSerializer, PropertySerializer, UnitSerializer


class OrgScopedMixin:
    """Automatically scope querysets to the user's active organization."""

    def get_org(self):
        return self.request.user.active_organization

    def get_queryset(self):
        org = self.get_org()
        if not org:
            return self.queryset.none()
        return self.queryset.filter(organization=org)

    def perform_create(self, serializer):
        serializer.save(organization=self.get_org())


class PropertyViewSet(OrgScopedMixin, viewsets.ModelViewSet):
    queryset = Property.objects.filter(is_deleted=False)
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "city", "state", "address_line1"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOrgOwnerOrManager()]
        return super().get_permissions()

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=["get"])
    def units(self, request, pk=None):
        prop = self.get_object()
        units = Unit.objects.filter(property=prop, is_deleted=False)
        serializer = UnitSerializer(units, many=True, context={"request": request})
        return Response(serializer.data)


class UnitViewSet(OrgScopedMixin, viewsets.ModelViewSet):
    queryset = Unit.objects.filter(is_deleted=False).select_related("property")
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "property__name", "electricity_meter_id"]
    ordering_fields = ["name", "base_rent", "status", "created_at"]
    ordering = ["property__name", "name"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOrgOwnerOrManager()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        property_id = self.request.query_params.get("property")
        if property_id:
            qs = qs.filter(property_id=property_id)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_destroy(self, instance):
        instance.soft_delete()


class LeaseViewSet(OrgScopedMixin, viewsets.ModelViewSet):
    queryset = Lease.objects.all().select_related("unit__property", "tenant")
    serializer_class = LeaseSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["tenant__email", "tenant__first_name", "tenant__last_name", "unit__name"]
    ordering_fields = ["start_date", "end_date", "monthly_rent", "status", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOrgOwnerOrManager()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        unit_id = self.request.query_params.get("unit")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        tenant_id = self.request.query_params.get("tenant")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        lease = self.get_object()
        if lease.status != Lease.Status.DRAFT:
            return Response(
                {"detail": "Only draft leases can be activated."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent double-booking: no other ACTIVE lease may exist for the same unit
        conflict = (
            Lease.objects.filter(
                unit=lease.unit,
                status=Lease.Status.ACTIVE,
            )
            .exclude(pk=lease.pk)
            .first()
        )
        if conflict:
            return Response(
                {
                    "detail": (
                        f"Unit already has an active lease (tenant: {conflict.tenant.email}). "
                        "Terminate or end the existing lease before activating a new one."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        lease.status = Lease.Status.ACTIVE
        lease.save(update_fields=["status"])
        lease.unit.status = Unit.Status.OCCUPIED
        lease.unit.save(update_fields=["status"])
        return Response(LeaseSerializer(lease).data)

    @action(detail=True, methods=["post"])
    def terminate(self, request, pk=None):
        lease = self.get_object()
        if lease.status not in (Lease.Status.ACTIVE, Lease.Status.DRAFT):
            return Response(
                {"detail": "Only active or draft leases can be terminated."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lease.status = Lease.Status.TERMINATED
        lease.save(update_fields=["status"])
        lease.unit.status = Unit.Status.VACANT
        lease.unit.save(update_fields=["status"])
        return Response(LeaseSerializer(lease).data)
