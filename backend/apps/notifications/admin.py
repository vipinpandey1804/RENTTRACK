"""Django admin configuration for the notifications app."""
from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient", "organization", "channel", "event_type", "status",
        "retry_count", "sent_at", "created_at",
    )
    list_filter = ("channel", "status", "event_type", "organization")
    search_fields = ("recipient__email", "subject", "event_type")
    readonly_fields = (
        "id", "provider_message_id", "sent_at", "delivered_at", "read_at",
        "created_at", "updated_at",
    )
    raw_id_fields = ("organization", "recipient")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Routing", {"fields": ("id", "organization", "recipient", "channel", "event_type")}),
        ("Content", {"fields": ("subject", "body", "payload")}),
        ("Delivery", {"fields": ("status", "provider", "provider_message_id", "retry_count", "error_message")}),
        ("Timestamps", {"fields": ("sent_at", "delivered_at", "read_at", "created_at", "updated_at")}),
    )
