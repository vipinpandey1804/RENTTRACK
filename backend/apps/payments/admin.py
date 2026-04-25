"""Django admin configuration for the payments app."""

from django.contrib import admin

from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "bill",
        "organization",
        "amount",
        "method",
        "status",
        "reference_number",
        "gateway",
        "paid_at",
        "recorded_by",
    )
    list_filter = ("status", "method", "gateway", "organization")
    search_fields = (
        "bill__bill_number",
        "reference_number",
        "gateway_payment_id",
        "recorded_by__email",
    )
    readonly_fields = (
        "id",
        "idempotency_key",
        "gateway_order_id",
        "gateway_payment_id",
        "gateway_response",
        "created_at",
        "updated_at",
    )
    raw_id_fields = ("organization", "bill", "recorded_by")
    ordering = ("-paid_at", "-created_at")
    date_hierarchy = "paid_at"

    fieldsets = (
        ("Reference", {"fields": ("id", "organization", "bill")}),
        ("Payment", {"fields": ("amount", "method", "status", "reference_number", "paid_at")}),
        (
            "Gateway",
            {"fields": ("gateway", "gateway_order_id", "gateway_payment_id", "gateway_response")},
        ),
        ("Audit", {"fields": ("recorded_by", "receipt_url", "idempotency_key", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
