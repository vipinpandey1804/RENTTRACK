"""Django admin configuration for the metering app."""

from django.contrib import admin

from apps.metering.models import MeterReading


@admin.register(MeterReading)
class MeterReadingAdmin(admin.ModelAdmin):
    list_display = (
        "unit",
        "organization",
        "meter_type",
        "period_month",
        "previous_reading",
        "current_reading",
        "units_consumed",
        "status",
    )
    list_filter = ("status", "meter_type", "organization")
    search_fields = ("unit__name", "unit__property__name", "submitted_by__email")
    readonly_fields = ("id", "units_consumed", "created_at", "updated_at")
    raw_id_fields = ("organization", "unit", "submitted_by", "confirmed_by")
    ordering = ("-period_month",)
    date_hierarchy = "period_month"

    fieldsets = (
        ("Reading", {"fields": ("id", "organization", "unit", "meter_type", "period_month")}),
        (
            "Values",
            {
                "fields": (
                    "previous_reading",
                    "current_reading",
                    "units_consumed",
                    "ocr_extracted_value",
                )
            },
        ),
        ("Photo & OCR", {"fields": ("reading_photo_url",)}),
        ("Status", {"fields": ("status", "submitted_by", "confirmed_by", "confirmed_at", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
