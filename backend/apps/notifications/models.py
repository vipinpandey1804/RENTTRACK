"""
Notifications: multi-channel delivery (email, SMS, WhatsApp, in-app).

Every outbound notification is persisted for audit + retry.
"""

from django.db import models

from apps.core.models import TenantAwareModel


class Notification(TenantAwareModel):
    """A single notification dispatch."""

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        IN_APP = "in_app", "In-App"
        PUSH = "push", "Push"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        BOUNCED = "bounced", "Bounced"
        READ = "read", "Read"

    recipient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    event_type = models.CharField(max_length=100, db_index=True)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    provider = models.CharField(max_length=50, blank=True, help_text="msg91, sendgrid, etc.")
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["recipient", "status", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]
        # Partitioning hint: partition by month(created_at); 90-day hot retention

    def __str__(self):
        return f"{self.channel} to {self.recipient.email}: {self.event_type}"


# Event types that users can toggle preferences for
PREFERENCE_EVENTS = [
    ("bill.issued", "Bill issued"),
    ("bill.overdue", "Bill overdue"),
    ("payment.received", "Payment received"),
]

# Channels available for user preferences
PREFERENCE_CHANNELS = [
    ("email", "Email"),
    ("sms", "SMS"),
]


class NotificationPreference(models.Model):
    """Per-user toggle for each event × channel combination."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    event_type = models.CharField(max_length=100)
    channel = models.CharField(max_length=20)
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_preferences"
        unique_together = [("user", "event_type", "channel")]
        indexes = [
            models.Index(fields=["user", "event_type"]),
        ]

    def __str__(self):
        state = "on" if self.enabled else "off"
        return f"{self.user.email} {self.event_type}/{self.channel}: {state}"
