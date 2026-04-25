"""Billing serializers."""

from decimal import Decimal

from rest_framework import serializers

from apps.billing.models import Bill, BillLineItem
from apps.payments.models import Payment


class BillLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLineItem
        fields = ["id", "description", "quantity", "unit_price", "amount", "tax_rate", "metadata"]
        read_only_fields = ["id"]


class PaymentSummarySerializer(serializers.ModelSerializer):
    recorded_by_email = serializers.EmailField(
        source="recorded_by.email", read_only=True, default=None
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "method",
            "status",
            "reference_number",
            "paid_at",
            "notes",
            "recorded_by_email",
        ]
        read_only_fields = ["id", "recorded_by_email"]


class BillSerializer(serializers.ModelSerializer):
    line_items = BillLineItemSerializer(many=True, read_only=True)
    payments = PaymentSummarySerializer(many=True, read_only=True)
    lease_info = serializers.SerializerMethodField()
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Bill
        fields = [
            "id",
            "bill_number",
            "bill_type",
            "lease",
            "lease_info",
            "period_start",
            "period_end",
            "issue_date",
            "due_date",
            "subtotal",
            "tax_amount",
            "total_amount",
            "amount_paid",
            "balance_due",
            "status",
            "pdf_url",
            "notes",
            "line_items",
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "bill_number",
            "balance_due",
            "amount_paid",
            "created_at",
            "updated_at",
        ]

    def get_lease_info(self, obj):
        lease = obj.lease
        return {
            "id": str(lease.id),
            "tenant_email": lease.tenant.email,
            "tenant_name": f"{lease.tenant.first_name} {lease.tenant.last_name}".strip(),
            "unit_name": lease.unit.name,
            "property_name": lease.unit.property.name,
        }


class RecordPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    method = serializers.ChoiceField(choices=Payment.Method.choices)
    reference_number = serializers.CharField(max_length=100, required=False, default="")
    notes = serializers.CharField(max_length=500, required=False, default="")

    def validate_amount(self, value):
        bill = self.context.get("bill")
        if bill and value > bill.balance_due:
            raise serializers.ValidationError(
                f"Amount {value} exceeds balance due {bill.balance_due}."
            )
        return value


class GenerateBillSerializer(serializers.Serializer):
    lease_id = serializers.UUIDField()
    period_date = serializers.DateField(
        help_text="Any date within the billing month (e.g. 2026-04-01)"
    )
