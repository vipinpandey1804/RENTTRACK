"""Django admin configuration for the properties app."""

from django.contrib import admin

from apps.properties.models import Lease, Property, Unit


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0
    fields = ("name", "floor", "base_rent", "status", "electricity_meter_id")
    readonly_fields = ("status",)
    show_change_link = True


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "property_type",
        "city",
        "state",
        "unit_count",
        "is_deleted",
        "created_at",
    )
    list_filter = ("property_type", "is_deleted", "organization")
    search_fields = ("name", "city", "state", "address_line1")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("organization",)
    ordering = ("organization", "name")

    fieldsets = (
        ("Identity", {"fields": ("id", "organization", "name", "property_type")}),
        (
            "Address",
            {
                "fields": (
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "postal_code",
                    "country",
                )
            },
        ),
        ("Tariffs", {"fields": ("electricity_rate_per_unit",)}),
        ("State", {"fields": ("is_deleted",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    inlines = [UnitInline]

    @admin.display(description="Units")
    def unit_count(self, obj):
        return obj.units.filter(is_deleted=False).count()


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "property",
        "organization",
        "base_rent",
        "status",
        "bedrooms",
        "electricity_meter_id",
        "is_deleted",
    )
    list_filter = ("status", "is_deleted", "organization")
    search_fields = ("name", "property__name", "electricity_meter_id")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("organization", "property")
    ordering = ("property", "name")


@admin.register(Lease)
class LeaseAdmin(admin.ModelAdmin):
    list_display = (
        "tenant",
        "unit",
        "organization",
        "monthly_rent",
        "status",
        "start_date",
        "end_date",
        "billing_cycle",
    )
    list_filter = ("status", "billing_cycle", "organization")
    search_fields = ("tenant__email", "tenant__first_name", "unit__name", "unit__property__name")
    readonly_fields = ("id", "created_at", "updated_at")
    raw_id_fields = ("organization", "unit", "tenant")
    ordering = ("-created_at",)

    fieldsets = (
        ("Parties", {"fields": ("id", "organization", "unit", "tenant")}),
        (
            "Terms",
            {
                "fields": (
                    "monthly_rent",
                    "security_deposit_held",
                    "start_date",
                    "end_date",
                    "status",
                )
            },
        ),
        (
            "Billing",
            {
                "fields": (
                    "billing_cycle",
                    "billing_day_of_month",
                    "grace_period_days",
                    "late_fee_type",
                    "late_fee_value",
                )
            },
        ),
        ("Notes", {"fields": ("notes",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
