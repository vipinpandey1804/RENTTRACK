"""Metering API viewsets."""

from django.utils import timezone
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsOrgMember, IsOrgOwnerOrManager
from apps.metering.models import MeterReading
from apps.metering.serializers import MeterReadingSerializer
from apps.properties.views import OrgScopedMixin


class MeterReadingViewSet(OrgScopedMixin, viewsets.ModelViewSet):
    """
    CRUD for meter readings.

    - Any org member may submit (POST) and view readings.
    - Only owners / property managers may confirm or delete.
    """

    queryset = MeterReading.objects.select_related("unit__property", "submitted_by", "confirmed_by")
    serializer_class = MeterReadingSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [filters.OrderingFilter]
    ordering = ["-period_month", "-created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("confirm", "destroy"):
            return [IsAuthenticated(), IsOrgOwnerOrManager()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        # Tenants see only readings for their own units
        user = self.request.user
        from apps.accounts.models import Membership

        role = (
            Membership.objects.filter(
                user=user,
                organization=user.active_organization,
                is_active=True,
            )
            .values_list("role", flat=True)
            .first()
        )
        tenant_roles = {Membership.Role.TENANT, Membership.Role.CO_TENANT}
        if role in tenant_roles:
            qs = qs.filter(unit__leases__tenant=user, unit__leases__status="active")
        return qs

    @action(detail=True, methods=["patch"])
    def confirm(self, request, pk=None):
        """Confirm a submitted reading and generate the electricity bill."""
        reading = self.get_object()

        if reading.status == MeterReading.Status.LOCKED:
            return Response(
                {"detail": "Reading is already locked (billed)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if reading.status == MeterReading.Status.CONFIRMED:
            return Response(
                {"detail": "Reading is already confirmed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Confirm the reading
        reading.status = MeterReading.Status.CONFIRMED
        reading.confirmed_by = request.user
        reading.confirmed_at = timezone.now()
        reading.save(update_fields=["status", "confirmed_by", "confirmed_at"])

        # Generate electricity bill (locks the reading internally)
        try:
            from apps.billing.services import generate_electricity_bill

            bill = generate_electricity_bill(reading)
            # Re-fetch to get updated status (locked by service)
            reading.refresh_from_db()
            serializer = MeterReadingSerializer(reading, context={"request": request})
            return Response(
                {**serializer.data, "bill_id": str(bill.id)},
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
