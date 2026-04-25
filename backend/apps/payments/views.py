"""Payment views — list/retrieve only (writes go through billing/record-payment)."""

from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.accounts.permissions import IsOrgMember
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of payments. Recording payments is done via /billing/bills/{id}/record-payment/."""

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["reference_number", "bill__bill_number", "bill__lease__tenant__email"]
    ordering_fields = ["paid_at", "amount", "status", "created_at"]
    ordering = ["-paid_at"]

    def get_queryset(self):
        org = self.request.user.active_organization
        if not org:
            return Payment.objects.none()
        qs = Payment.objects.filter(organization=org).select_related(
            "bill__lease__tenant", "recorded_by"
        )
        bill_id = self.request.query_params.get("bill")
        if bill_id:
            qs = qs.filter(bill_id=bill_id)
        method = self.request.query_params.get("method")
        if method:
            qs = qs.filter(method=method)
        return qs
