"""Payment serializers."""
from rest_framework import serializers

from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    recorded_by_email = serializers.EmailField(source="recorded_by.email", read_only=True, default=None)
    bill_number = serializers.CharField(source="bill.bill_number", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "bill",
            "bill_number",
            "amount",
            "method",
            "status",
            "reference_number",
            "gateway",
            "gateway_payment_id",
            "recorded_by_email",
            "paid_at",
            "receipt_url",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "bill_number", "status", "gateway", "gateway_payment_id",
            "recorded_by_email", "created_at", "updated_at",
        ]
