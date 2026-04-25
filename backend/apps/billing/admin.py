"""Django admin configuration for the billing app."""

from django.contrib import admin

from apps.billing.models import Bill, BillLineItem


class BillLineItemInline(admin.TabularInline):
    model = BillLineItem
    extra = 0
    fields = ("description", "quantity", "unit_price", "tax_rate", "amount")
    readonly_fields = ("amount",)


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = (
        "bill_number",
        "organization",
        "lease_tenant",
        "bill_type",
        "status",
        "total_amount",
        "balance_due",
        "due_date",
        "issue_date",
    )
    list_filter = ("status", "bill_type", "organization")
    search_fields = ("bill_number", "lease__tenant__email", "lease__unit__name")
    readonly_fields = ("id", "bill_number", "created_at", "updated_at")
    raw_id_fields = ("organization", "lease")
    ordering = ("-due_date",)
    date_hierarchy = "due_date"

    fieldsets = (
        ("Identity", {"fields": ("id", "bill_number", "organization", "lease", "bill_type")}),
        ("Period", {"fields": ("period_start", "period_end", "issue_date", "due_date")}),
        (
            "Amounts",
            {"fields": ("subtotal", "tax_amount", "total_amount", "amount_paid", "balance_due")},
        ),
        ("State", {"fields": ("status", "pdf_url", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    inlines = [BillLineItemInline]

    @admin.display(description="Tenant")
    def lease_tenant(self, obj):
        return obj.lease.tenant.email if obj.lease_id else "—"


@admin.register(BillLineItem)
class BillLineItemAdmin(admin.ModelAdmin):
    list_display = ("bill", "description", "quantity", "unit_price", "tax_rate", "amount")
    search_fields = ("bill__bill_number", "description")
    readonly_fields = ("id",)
    raw_id_fields = ("bill",)
