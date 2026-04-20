"""Billing API views."""
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsOrgMember, IsOrgOwnerOrManager
from apps.billing.models import Bill, BillLineItem
from apps.billing.serializers import BillSerializer, GenerateBillSerializer, RecordPaymentSerializer
from apps.billing.services import apply_payment, generate_rent_bill
from apps.notifications.tasks import notify_bill_issued
from apps.properties.models import Lease


class BillViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve bills.

    Write operations (generate, record-payment, cancel) are via custom actions.
    Bills are immutable once issued — no update/delete endpoints.
    """

    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["bill_number", "lease__tenant__email", "lease__unit__name"]
    ordering_fields = ["due_date", "issue_date", "total_amount", "status", "created_at"]
    ordering = ["-due_date"]

    def get_queryset(self):
        org = self.request.user.active_organization
        if not org:
            return Bill.objects.none()
        qs = Bill.objects.filter(organization=org).select_related(
            "lease__tenant", "lease__unit__property"
        ).prefetch_related("line_items", "payments__recorded_by")

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        lease_id = self.request.query_params.get("lease")
        if lease_id:
            qs = qs.filter(lease_id=lease_id)

        bill_type = self.request.query_params.get("bill_type")
        if bill_type:
            qs = qs.filter(bill_type=bill_type)

        return qs

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated, IsOrgOwnerOrManager])
    def generate(self, request):
        """Manually generate a rent bill for a lease + period."""
        serializer = GenerateBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        org = request.user.active_organization
        lease = get_object_or_404(
            Lease,
            id=serializer.validated_data["lease_id"],
            organization=org,
            status=Lease.Status.ACTIVE,
        )

        bill = generate_rent_bill(lease, serializer.validated_data["period_date"])
        notify_bill_issued.delay(str(bill.id))
        return Response(BillSerializer(bill).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsOrgOwnerOrManager])
    def record_payment(self, request, pk=None):
        """Record a manual payment against this bill."""
        bill = self.get_object()

        if bill.status in (Bill.Status.PAID, Bill.Status.CANCELLED):
            return Response(
                {"detail": f"Cannot record payment on a {bill.status} bill."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RecordPaymentSerializer(data=request.data, context={"bill": bill})
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        try:
            apply_payment(
                bill=bill,
                amount=d["amount"],
                method=d["method"],
                recorded_by=request.user,
                reference=d.get("reference_number", ""),
                notes=d.get("notes", ""),
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        bill.refresh_from_db()
        return Response(BillSerializer(bill).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsOrgOwnerOrManager])
    def cancel(self, request, pk=None):
        """Cancel a bill. Only DRAFT or ISSUED bills can be cancelled."""
        bill = self.get_object()
        if bill.status not in (Bill.Status.DRAFT, Bill.Status.ISSUED):
            return Response(
                {"detail": "Only draft or issued bills can be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        bill.status = Bill.Status.CANCELLED
        bill.save(update_fields=["status"])
        return Response(BillSerializer(bill).data)
